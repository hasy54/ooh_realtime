import subprocess
import re
import bluetooth
import time
from supabase import create_client, Client
import logging

# Configure logging
logging.basicConfig(
    filename='ooh_realtime.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Supabase configuration
SUPABASE_URL = 'https://khagoihfiizosznzsphn.supabase.co'  # Replace with your Supabase URL
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtoYWdvaWhmaWl6b3N6bnpzcGhuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcyNjQ5NjQyOSwiZXhwIjoyMDQyMDcyNDI5fQ.tjvyFooLpcfgfCVc16RwctkjNE4NW1hAfkjMcyhUEh4'  # Replace with your Supabase service role key

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logging.info("Connected to Supabase successfully.")
except Exception as e:
    logging.error(f"Failed to connect to Supabase: {e}")
    exit(1)

# Function to scan Wi-Fi devices
def scan_wifi():
    try:
        logging.info("Scanning for Wi-Fi devices...")
        result = subprocess.check_output(['sudo', 'iwlist', 'wlan0', 'scan']).decode('utf-8', errors='ignore')
        cells = result.split('Cell')
        wifi_devices = []
        for cell in cells[1:]:
            mac_address_match = re.search(r'Address: ([\dA-F:]{17})', cell)
            ssid_match = re.search(r'ESSID:"(.*)"', cell)
            signal_match = re.search(r'Signal level=(-?\d+) dBm', cell)
            if mac_address_match and ssid_match and signal_match:
                mac_address = mac_address_match.group(1)
                ssid = ssid_match.group(1)
                signal = int(signal_match.group(1))
                wifi_devices.append({
                    'mac_address': mac_address,
                    'ssid': ssid,
                    'signal': signal,
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                })
        logging.info(f"Found {len(wifi_devices)} Wi-Fi devices.")
        return wifi_devices
    except Exception as e:
        logging.error(f"Error scanning Wi-Fi: {e}")
        return []

# Function to scan Bluetooth devices
def scan_bluetooth():
    try:
        logging.info("Starting Bluetooth scan...")
        devices = bluetooth.discover_devices(duration=12, lookup_names=True)
        bt_devices = []
        for addr, name in devices:
            bt_devices.append({
                'address': addr,
                'name': name,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            })
        logging.info(f"Found {len(bt_devices)} Bluetooth devices.")
        return bt_devices
    except Exception as e:
        logging.error(f"Error scanning Bluetooth: {e}")
        return []

# Function to insert data into Supabase
def insert_data(table_name, data):
    if not data:
        logging.info(f"No data to insert into {table_name}.")
        return
    try:
        response = supabase.table(table_name).insert(data).execute()
        logging.debug(f"Insert response for {table_name}: {response}")
        if hasattr(response, 'error') and response.error:
            logging.error(f"Error inserting data into {table_name}: {response.error}")
        else:
            logging.info(f"Data successfully inserted into {table_name}.")
    except Exception as e:
        logging.error(f"Exception during data insertion into {table_name}: {e}")

# Function to perform scanning and data insertion
def perform_scan_cycle():
    logging.info("Starting new scan cycle...")
    wifi_data = scan_wifi()
    bt_data = scan_bluetooth()

    # Insert data into Supabase
    insert_data('wifi_devices', wifi_data)
    insert_data('bluetooth_devices', bt_data)

    logging.info("Scan cycle complete.")

# Main function to run scanning at intervals
def main():
    logging.info("ooh_realtime script started.")
    while True:
        perform_scan_cycle()
        logging.info("Waiting for the next cycle...")
        time.sleep(0)  # Wait for 5 minutesSS

if __name__ == "__main__":
    main()
