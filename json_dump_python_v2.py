import json
import os
import time
from datetime import datetime
from zeep import Client, Settings
from zeep.exceptions import Fault
import pytz

# ----------------------------
# 📍 1. Configuration
# ----------------------------

# Set timezone
local_timezone = pytz.timezone("America/Los_Angeles")

# WSDL URL for SOAP service
wsdl_url = "https://colondexsrv.its.nv.gov/tmddws/TmddWS.svc?singleWsdl"

# Dynamic Desktop paths
desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
base_data_dir = os.path.join(desktop_path, 'json_data')
save_directory = base_data_dir
log_directory = os.path.join(base_data_dir, 'logs')

# Time step in minutes
TIME_STEP_MINUTES = 0.5

# Authentication parameters
auth_params = {
    "user-id": "UNLV_TRC_RTIS",
    "password": "+r@^~Tr&lt;R?|$"
}
organization_info = {
    "organization-id": "unlv.edu",
    "center-contact-list": {
        "center-contact-details": {"center-id": "UNLV_TRC"}
    }
}
requesting_organization_info = {
    "organization-id": "its.nv.gov",
    "center-contact-list": {
        "center-contact-details": {"center-id": "FAST"}
    }
}
device_type = "detector"
device_info = "device data"

# SOAP request parameters
soap_parameters = {
    "device-information-request-header": {
        "authentication": auth_params,
        "organization-information": organization_info,
        "organization-requesting": requesting_organization_info,
        "device-type": device_type,
        "device-information-type": device_info
    }
}

# ----------------------------
# 📍 2. Initialize
# ----------------------------

# Ensure folders exist
os.makedirs(save_directory, exist_ok=True)
os.makedirs(log_directory, exist_ok=True)

# Configure Zeep client
settings = Settings(strict=False, xml_huge_tree=True)

try:
    client = Client(wsdl=wsdl_url, settings=settings)
except Exception as e:
    print(f"Failed to connect to SOAP service: {e}")
    exit()

# ----------------------------
# 📍 3. Helper Functions
# ----------------------------

def write_log(event_type, message, extra_info=None):
    """Write structured logs with more information."""
    log_filename = datetime.now(local_timezone).strftime('%Y-%m-%d') + ".log"
    log_filepath = os.path.join(log_directory, log_filename)
    timestamp = datetime.now(local_timezone).strftime('%Y-%m-%d %H:%M:%S')
    
    log_entry = {
        "timestamp": timestamp,
        "event": event_type,
        "message": message,
    }
    
    if extra_info:
        log_entry.update(extra_info)
    
    with open(log_filepath, 'a') as log_file:
        log_file.write(json.dumps(log_entry) + "\n")  # Save log entries as JSON per line

def fetch_and_save_data():
    """Fetch sensor data and save to JSON."""
    fetch_start = datetime.now(local_timezone)
    
    try:
        response = client.service.dlDetectorDataRequest(**soap_parameters)
    except Fault as e:
        error_msg = f"SOAP request failed: {e}"
        print(error_msg)
        write_log("ERROR", error_msg)
        return

    if not response:
        msg = "No data returned from SOAP service."
        print(msg)
        write_log("ERROR", msg)
        return

    sensor_data = []
    for item in response:
        detector_list = getattr(item, 'detector-list', None)
        if not detector_list:
            continue
        
        detector_details = getattr(detector_list, 'detector-data-detail', [])
        for detector in detector_details:
            sensor_data.append({
                'stationId': getattr(detector, 'station-id', None),
                'detectorId': getattr(detector, 'detector-id', None),
                'vehicleOccupancy': getattr(detector, 'vehicle-occupancy', None),
                'vehicleSpeed': getattr(detector, 'vehicle-speed', None),
                'vehicleCountBin1': getattr(detector, 'vehicle-count-bin1', None),
                'vehicleCountBin2': getattr(detector, 'vehicle-count-bin2', None),
                'vehicleCountBin3': getattr(detector, 'vehicle-count-bin3', None),
                'vehicleCountBin4': getattr(detector, 'vehicle-count-bin4', None),
                'vehicleCount': getattr(detector, 'vehicle-count', None),
            })

    timestamp_str = fetch_start.strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{timestamp_str}.json"
    filepath = os.path.join(save_directory, filename)

    try:
        with open(filepath, 'w') as f:
            json.dump(sensor_data, f, indent=4)
        
        fetch_end = datetime.now(local_timezone)
        duration_seconds = (fetch_end - fetch_start).total_seconds()

        success_msg = f"Data saved successfully: {filename}"
        print(success_msg)
        write_log("SUCCESS", success_msg, {
            "file": filename,
            "entries_saved": len(sensor_data),
            "fetch_duration_sec": duration_seconds
        })

    except Exception as e:
        error_msg = f"Failed to save JSON file: {e}"
        print(error_msg)
        write_log("ERROR", error_msg)

# ----------------------------
# 📍 4. Main Loop
# ----------------------------

if __name__ == "__main__":
    print(f"Starting live data collection every {TIME_STEP_MINUTES} minutes...\n")
    write_log("INFO", f"Service started. Fetch interval: {TIME_STEP_MINUTES} minutes.")
    
    while True:
        fetch_and_save_data()
        print(f"Waiting {TIME_STEP_MINUTES} minutes for next fetch...\n")
        time.sleep(TIME_STEP_MINUTES * 60)
