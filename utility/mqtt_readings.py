

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
from infra.messaging.mqtt_collector import MQTTCollector
from utility.export_readings_to_excel import export_readings_to_excel

def extract_moisture3_omni4_readings(messages):
    readings = []
    print(f"[DEBUG] Processing {len(messages)} messages...")
    from infra.messaging import blue_pb2_2026
    for msg_type, decoded in messages:
        print(f"[DEBUG] Message type: {msg_type}")
        if msg_type == "AllReportsV3":
            # If readings are bytes, decode them
            readings_list = decoded.readings
            if hasattr(readings_list, '__iter__') and not isinstance(readings_list, (str, bytes)):
                readings_iter = readings_list
            else:
                readings_iter = [readings_list]
            for reading in readings_iter:
                # If reading is bytes, decode as CableReadingsV1
                if isinstance(reading, (bytes, bytearray)):
                    reading_decoded = blue_pb2_2026.CableReadingsV1()
                    reading_decoded.ParseFromString(reading)
                    reading = reading_decoded
                # Only keep reading if reading_count == 4
                reading_count = getattr(reading, "reading_count", None)
                reading_count_val = None
                if hasattr(reading_count, '__len__') and not isinstance(reading_count, (str, bytes)):
                    if len(reading_count) == 1:
                        reading_count_val = reading_count[0]
                    else:
                        reading_count_val = list(reading_count)
                else:
                    reading_count_val = reading_count
                if reading_count_val != 4:
                    continue
                header = getattr(reading, "header", None)
                ts = getattr(header, "timestamp", None) if header else None
                cable_readings_list = getattr(reading, "cable_readings", [])
                if hasattr(cable_readings_list, '__iter__') and not isinstance(cable_readings_list, (str, bytes)):
                    cable_iter = cable_readings_list
                else:
                    cable_iter = [cable_readings_list]
                for cable in cable_iter:
                    # If cable is bytes, decode as needed (add logic if you have nested wrappers)
                    types = cable.type if hasattr(cable, '__iter__') and not isinstance(cable.type, str) else [cable.type]
                    cable_num = getattr(cable, "cable_num", None)
                    print(f"[DEBUG] Found cable: types={types}, cable_num={cable_num}")
                    # MOISTURE cableNum 3
                    if cable_num == 3:
                        temp_vals = list(getattr(cable, "temp_readings", []))
                        rh_vals = list(getattr(cable, "rh_readings", []))
                        print(f"[DEBUG] --> Extracting MOISTURE cableNum 3 at ts={ts}")
                        print(f"[DEBUG]    tempReadings: {temp_vals}")
                        print(f"[DEBUG]    rhReadings: {rh_vals}")
                        readings.append({
                            "timestamp": ts,
                            "type": "moisture",
                            "tempReadings": temp_vals,
                            "rhReadings": rh_vals,
                        })
                    # OMNI cableNum 4
                    if cable_num == 4:
                        temp_vals = list(getattr(cable, "temp_readings", []))
                        rh_vals = list(getattr(cable, "rh_readings", []))
                        print(f"[DEBUG] --> Extracting OMNI cableNum 4 at ts={ts}")
                        print(f"[DEBUG]    tempReadings: {temp_vals}")
                        print(f"[DEBUG]    rhReadings: {rh_vals}")
                        readings.append({
                            "timestamp": ts,
                            "type": "omni",
                            "tempReadings": temp_vals,
                            "rhReadings": rh_vals,
                        })
    print(f"[DEBUG] Total extracted readings: {len(readings)}")
    return readings

def run_mqtt_collector_and_extract(mqtt_config, duration_hours=24):
    collector = MQTTCollector(
        mqtt_config["root_ca_path"],
        mqtt_config["cert_path"],
        mqtt_config["private_key_path"],
        mqtt_config["client_id"],
        mqtt_config["mac_address"]
    )
    collector.start()
    print(f"Collecting MQTT messages for {duration_hours} hours...")
    time.sleep(duration_hours * 3600)
    messages = collector.collect_messages()
    readings = extract_moisture3_omni4_readings(messages)
    return readings

def format_for_excel(readings):
    # Merge moisture and omni readings by timestamp and sensor index
    from collections import defaultdict
    from datetime import datetime, timezone, timedelta
    merged = defaultdict(lambda: {"moisture_temperature": None, "omni_temperature": None, "moisture_rh": None, "omni_rh": None})
    for r in readings:
        ts = r["timestamp"]
        for i in range(10):
            key = (ts, i)
            if r["type"] == "moisture":
                if len(r["tempReadings"]) > i:
                    merged[key]["moisture_temperature"] = r["tempReadings"][i]
                if len(r["rhReadings"]) > i:
                    merged[key]["moisture_rh"] = r["rhReadings"][i]
            elif r["type"] == "omni":
                if len(r["tempReadings"]) > i:
                    merged[key]["omni_temperature"] = r["tempReadings"][i]
                if len(r["rhReadings"]) > i:
                    merged[key]["omni_rh"] = r["rhReadings"][i]
    # Mountain Time (America/Denver, UTC-7 or UTC-6 DST)
    # For simplicity, use UTC-7 (no DST logic)
    MT_OFFSET = -7
    rows = []
    for (ts, i) in sorted(merged.keys()):
        # Convert timestamp to mountain time string
        if ts is not None:
            dt_mt = datetime.utcfromtimestamp(ts) + timedelta(hours=MT_OFFSET)
            ts_str = dt_mt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts_str = None
        row = {"date_time_mountain": ts_str, "sensor_number": i+1}
        row.update(merged[(ts, i)])
        rows.append(row)
    return rows

if __name__ == "__main__":
    # --- Collect one real AllReportsV3 message and export ---
    mqtt_config = {
        "root_ca_path": "infra/messaging/dev_qa_root_cert_auth.crt",
        "cert_path": "infra/messaging/dev_qa_client.crt",
        "private_key_path": "infra/messaging/dev_qa_client.key",
        "client_id": "iotconsole-8ab27190-cb60-4b0f-81aa-7fa683a198c7",
        "mac_address": "18:8b:0e:c5:c4:8d"
    }
    import time
    collector = MQTTCollector(
        mqtt_config["root_ca_path"],
        mqtt_config["cert_path"],
        mqtt_config["private_key_path"],
        mqtt_config["client_id"],
        mqtt_config["mac_address"]
    )
    collector.start()
    print("Collecting AllReportsV3 messages for 24 hours...")
    start_time = time.time()
    duration_seconds = 24 * 3600  # 24 hours for production
    all_valid_msgs = []
    while time.time() - start_time < duration_seconds:
        messages = collector.collect_messages()
        for m in messages:
            if m[0] != "AllReportsV3":
                continue
            decoded = m[1]
            # Check top-level header.mac_address
            header_mac = None
            if hasattr(decoded, "header"):
                header = getattr(decoded, "header")
                if hasattr(header, "mac_address"):
                    header_mac = getattr(header, "mac_address")
            # Only process this message if ANY reading has reading_count == 4
            found_valid = False
            for reading in getattr(decoded, "readings", []):
                reading_count = getattr(reading, "reading_count", None)
                reading_count_val = None
                if hasattr(reading_count, '__len__') and not isinstance(reading_count, (str, bytes)):
                    if len(reading_count) == 1:
                        reading_count_val = reading_count[0]
                    else:
                        reading_count_val = list(reading_count)
                else:
                    reading_count_val = reading_count
                if reading_count_val == 4:
                    found_valid = True
                    break
            if not found_valid:
                continue
            all_valid_msgs.append(m)
        time.sleep(10)  # Poll every 10 seconds

    if not all_valid_msgs:
        print("No valid AllReportsV3 messages received in 2 hours.")
        exit(1)

    print(f"[DEBUG] Total valid messages collected: {len(all_valid_msgs)}")
    readings = extract_moisture3_omni4_readings(all_valid_msgs)
    print(f"[DEBUG] Readings extracted: {readings}")
    excel_rows = format_for_excel(readings)
    print(f"[DEBUG] Excel rows: {excel_rows}")
    from pandas import DataFrame
    df = DataFrame(excel_rows)
    df.to_excel("moisture_omni_readings_24hours.xlsx", index=False)
    print("Exported readings to moisture_omni_readings_24hours.xlsx")