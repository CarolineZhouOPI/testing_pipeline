import pandas as pd
from datetime import datetime

def export_readings_to_excel(readings, filename, start_time=None, end_time=None):
    """
    Export readings for 24 hours to an Excel spreadsheet for comparison.
    Args:
        readings (dict): Output from capture_cable_readings().
        filename (str): Path to the Excel file to create.
        start_time (datetime, optional): Start of the 24-hour window.
        end_time (datetime, optional): End of the 24-hour window.
    """
    # Collect readings by timestamp for both cables
    # Assumes readings['moisture_cable_3'] and readings['omni_cable_4']
    from collections import defaultdict
    temp_dict = defaultdict(dict)
    rh_dict = defaultdict(dict)

    # Helper to add readings to dicts
    def add_readings(reading_list, cable_key, value_key):
        for reading in reading_list:
            ts = reading.get('timestamp')
            if not ts:
                continue
            ts_dt = pd.to_datetime(ts)
            if start_time and ts_dt < start_time:
                continue
            if end_time and ts_dt > end_time:
                continue
            if value_key == 'temp':
                temp_dict[ts][cable_key] = reading.get('value')
            else:
                rh_dict[ts][cable_key] = reading.get('value')

    add_readings(readings.get('moisture_cable_3', {}).get('tempReadings', []), 'moisture', 'temp')
    add_readings(readings.get('omni_cable_4', {}).get('tempReadings', []), 'omni', 'temp')
    add_readings(readings.get('moisture_cable_3', {}).get('rhReadings', []), 'moisture', 'rh')
    add_readings(readings.get('omni_cable_4', {}).get('rhReadings', []), 'omni', 'rh')

    # Get all unique timestamps
    all_timestamps = set(temp_dict.keys()) | set(rh_dict.keys())
    all_timestamps = sorted(all_timestamps)

    rows = []
    for ts in all_timestamps:
        row = {
            'timestamp': ts,
            'moisture_temperature': temp_dict.get(ts, {}).get('moisture'),
            'omni_temperature': temp_dict.get(ts, {}).get('omni'),
            'moisture_rh': rh_dict.get(ts, {}).get('moisture'),
            'omni_rh': rh_dict.get(ts, {}).get('omni'),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.sort_values(by=['timestamp'], inplace=True)
    df.to_excel(filename, index=False)
