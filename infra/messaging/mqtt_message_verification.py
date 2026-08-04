# mqtt_message_verification.py
# Verification utilities for MQTT messages

def search_bin_id_for_primary_node_list(message_array, mac_address) -> bool:
    for msg in reversed(message_array):
        if (msg[0] == "NodeList") and (getattr(msg[1].header, 'mac_address', None) == mac_address):
            if getattr(msg[1].header, 'bin_id', None):
                return False
            else:
                return True
    return False

def check_provisioned_status(message_array, mac_address) -> bool:
    for msg in reversed(message_array):
        if (
            (msg[0] == "BinStatistics")
            and (getattr(msg[1].header, 'mac_address', None) == mac_address)
            and (getattr(msg[1].header, 'bin_id', 0) > 1)
        ):
            return True
    return False

def verify_bin_id(message_array, mac_address, expected_bin_id) -> bool:
    verified_bin_config = False
    verified_bin_stats = False
    verified_cable_readings = False
    for msg in reversed(message_array):
        if getattr(msg[1].header, 'mac_address', None) == mac_address:
            if not verified_bin_config and msg[0] == "BinConfig":
                if getattr(msg[1].header, 'bin_id', None) == int(expected_bin_id[0]):
                    verified_bin_config = True
            elif not verified_bin_stats and msg[0] == "BinStatistics":
                if getattr(msg[1].header, 'bin_id', None) == int(expected_bin_id[0]):
                    verified_bin_stats = True
            elif not verified_cable_readings and msg[0] == "CableReadings":
                if getattr(msg[1].header, 'bin_id', None) == int(expected_bin_id[0]):
                    verified_cable_readings = True
        if verified_bin_config and verified_bin_stats and verified_cable_readings:
            break
    return verified_bin_config and verified_bin_stats and verified_cable_readings

def check_cable_amount(message_array, mac_address, expected_amount) -> bool:
    logged_cables = []
    for msg in reversed(message_array):
        if getattr(msg[1].header, 'mac_address', None) == mac_address and msg[0] == "BinConfig":
            for cable in getattr(msg[1], 'cables_properties', []):
                if hasattr(cable, 'type') and (cable.type[0] == 0 or cable.type[0] == 1 or cable.type[0] == 7):
                    logged_cables.append(getattr(cable, 'rom_id', None))
            break
    return len(logged_cables) == int(expected_amount)

def check_emc_readings(message_array, mac_address) -> bool:
    for msg in reversed(message_array):
        if getattr(msg[1].header, 'mac_address', None) == mac_address and msg[0] == "CableReadings":
            for cable in getattr(msg[1], 'cable_readings', []):
                for emc_reading in getattr(cable, 'emc_readings', []):
                    if emc_reading <= 0:
                        return False
    return True

def get_latest_msgs(message_array, t):
    import time
    last_msgs = []
    current_timestamp = int(time.time())
    start_timestamp = current_timestamp - int(t)
    for msg in reversed(message_array):
        if int(getattr(msg[1].header, 'timestamp', 0)) < start_timestamp:
            break
        else:
            last_msgs.append(msg)
    return last_msgs

def check_orphan_list(message_array, primary_mac_address, secondary_mac_address):
    for msg in reversed(message_array):
        if getattr(msg[1].header, 'mac_address', None) == primary_mac_address and msg[0] == "NodeList":
            for orphan in getattr(msg[1], 'orphanlist', []):
                if getattr(orphan, 'mac_address', None) == secondary_mac_address:
                    return True
    return False

def verify_firmware_version(message_array, mac_address, version_major, version_minor):
    for msg in reversed(message_array):
        if getattr(msg[1].header, 'mac_address', None) == mac_address and msg[0] == "BinStatistics":
            if (
                getattr(msg[1].firmware, 'major', [None])[0] == version_major
                and getattr(msg[1].firmware, 'minor', [None])[0] == version_minor
            ):
                return True
    return False
