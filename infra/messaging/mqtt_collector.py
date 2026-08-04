# mqtt_collector.py

import json
import threading
import paho.mqtt.client as mqtt
from infra.messaging import blue_pb2_2026

MQTT_MESSAGE_LOGS = []

class MQTTCollector:
    AWS_IOT_ENDPOINT = "a3co9t51zvinlg-ats.iot.us-west-2.amazonaws.com"
    PORT = 8883
    client = None
    message_count = 0

    def __init__(
        self,
        root_ca_path,
        cert_path,
        private_key_path,
        client_id,
        mac_address,
    ):
        self.ROOT_CA_PATH = root_ca_path
        self.CERT_PATH = cert_path
        self.PRIVATE_KEY_PATH = private_key_path
        self.CLIENT_ID = client_id
        self.mac_address = mac_address
        # Topics with MAC address parameterized
        self.TOPIC_CONNECTED = f"connected/{mac_address}"
        self.TOPIC_ACK = f"ack/{mac_address}"
        self.TOPIC_COMMANDS = f"commands/{mac_address}"
        self.TOPIC_ALL_REPORTS_V2 = f"messages/qa/{mac_address}/AllReportsV3"
        self.TOPIC_FIRMWARE_VERSION_V1 = f"messages/qa/{mac_address}/FirmwareVersionV1"

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1, client_id=self.CLIENT_ID, transport="tcp"
        )
        self.client.tls_set(
            ca_certs=self.ROOT_CA_PATH,
            certfile=self.CERT_PATH,
            keyfile=self.PRIVATE_KEY_PATH,
        )
        # print("MQTTCollector initialized with the following parameters:")
        # print(f"ROOT_CA_PATH: {self.ROOT_CA_PATH}")
        # print(f"CERT_PATH: {self.CERT_PATH}")
        # print(f"PRIVATE_KEY_PATH: {self.PRIVATE_KEY_PATH}")
        # print(f"CLIENT_ID: {self.CLIENT_ID}")
        print(f"MAC_ADDRESS: {self.mac_address}")

    def disconnect(self):
        self.client.disconnect()

    def provision_one_primary(self) -> bool:
        self.connect_and_subscribe_to_topics()
        self.listen_to_messages()
        try:
            rv = self.client.connect(self.AWS_IOT_ENDPOINT, self.PORT)
            # Start the MQTT loop in a background thread
            self._loop_thread = threading.Thread(target=self.client.loop_forever, daemon=True)
            self._loop_thread.start()
        except Exception as e:
            print(f"An error occurred: {e}")

    def connect_and_subscribe_to_topics(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe(self.TOPIC_CONNECTED)
                client.subscribe(self.TOPIC_ACK)
                client.subscribe(self.TOPIC_COMMANDS)
                client.subscribe(self.TOPIC_ALL_REPORTS_V2)
                client.subscribe(self.TOPIC_FIRMWARE_VERSION_V1)
                return 0
            return 1
        self.client.on_connect = on_connect

    def listen_to_messages(self):
        def on_message(client, userdata, message):
            # print("########## receive a message ##########")
            # print(f"[DEBUG] Topic: {message.topic}")
            # print(f"[DEBUG] Raw payload: {message.payload}")
            self.message_count += 1
            topic_parts = message.topic.split("/")
            # print(f"topic parts length: {len(topic_parts)}")
            mac_address = ""
            message_type = ""
            if len(topic_parts) == 4:
                mac_address = topic_parts[2]
                message_type = topic_parts[3]
            elif len(topic_parts) == 2:
                mac_address = topic_parts[1]
                message_type = topic_parts[0]
            else:
                # print(f"Unexpected topic format: {message.topic}")
                return
            # print(f"Mac address: {mac_address}, Message type: {message_type}")

            # Log all messages, not just AllReportsV3 or FirmwareVersionV1
            if message_type == "AllReportsV3":
                # print("found AllReportsV3 message")
                try:
                    decoded = blue_pb2_2026.AllReportsV3()
                    decoded.ParseFromString(message.payload)
                    MQTT_MESSAGE_LOGS.append(("AllReportsV3", decoded))
                except Exception as e:
                    print(f"Failed to decode AllReportsV3 payload: {e}")
                    MQTT_MESSAGE_LOGS.append(("AllReportsV3", message.payload))
            elif message_type == "FirmwareVersionV1":
                # print("found FirmwareVersionV1 message")
                try:
                    decoded = blue_pb2_2026.FirmwareVersionV1()
                    decoded.ParseFromString(message.payload)
                    MQTT_MESSAGE_LOGS.append(("FirmwareVersionV1", decoded))
                except Exception as e:
                    # print(f"Failed to decode FirmwareVersionV1 payload: {e}")
                    MQTT_MESSAGE_LOGS.append(("FirmwareVersionV1", message.payload))
            else:
                # Log all other message types for debugging
                # print(f"[DEBUG] Unhandled message type: {message_type}")
                MQTT_MESSAGE_LOGS.append((message_type, message.payload))

            # print(f"MQTT_MESSAGE_LOGS length: {len(MQTT_MESSAGE_LOGS)}")
            if MQTT_MESSAGE_LOGS:
                msg_type = MQTT_MESSAGE_LOGS[-1][0]
                last_msg = MQTT_MESSAGE_LOGS[-1][1]
                # print(f"Last message type: {msg_type}")
                # print(f"Last message: {last_msg}")
                # if msg_type == "AllReportsV3":
                    # print("--- AllReportsV3 fields ---")
                    # if hasattr(last_msg, 'config'):
                    #     print(f">>>>>>>>>>>>>>>>>>FanNodeCfg: {last_msg.config[0].fan_node_cfg}")
                    # if hasattr(last_msg, 'readings'):
                    #     print(f"++++++++++++>Number of readings: {len(last_msg.readings)}")
                    #     for i, reading in enumerate(last_msg.readings):
                    #         print(f"  Reading {i}: {reading}")
                    #         if hasattr(reading, 'cable_readings'):
                    #             print(f"~~~~~~~~~Number of cable readings: {len(reading.cable_readings)}")
                    #             for j, cable_reading in enumerate(reading.cable_readings):
                    #                 print(f"Cable Reading {j}: {cable_reading.type[0]}")
                # if msg_type == "FirmwareVersionV1":
                    # print(f"FirmwareVersionV1 object major: {last_msg.major[0]}")
                    # print(f"FirmwareVersionV1 object minor: {last_msg.minor[0]}")
            import sys
            sys.stdout.flush()
        self.client.on_message = on_message

    def start(self):
        self.provision_one_primary()

    def collect_messages(self, duration_hours=None):
        return MQTT_MESSAGE_LOGS