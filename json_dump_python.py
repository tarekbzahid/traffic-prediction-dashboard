import json
import os
from datetime import datetime
from zeep import Client, Settings
from zeep.exceptions import Fault
import pytz

# Set timezone
local_timezone = pytz.timezone("America/Los_Angeles")

# WSDL URL for SOAP service
wsdl = "https://colondexsrv.its.nv.gov/tmddws/TmddWS.svc?singleWsdl"

# Enable Zeep settings for debugging
settings = Settings(strict=False, xml_huge_tree=True)
try:
    client = Client(wsdl=wsdl, settings=settings)
except Exception as e:
    print(f"Failed to connect to SOAP service: {e}")
    exit()

# Define authentication and request parameters
user = "UNLV_TRC_RTIS"
password = "+r@^~Tr&lt;R?|$"
organization = "unlv.edu"
center = "UNLV_TRC"
centerreq = "FAST"
devicetype = "detector"
deviceinfo = "device data"
organisationreq = "its.nv.gov"

# SOAP request parameters
parameters = {
    "device-information-request-header": {
        "authentication": {
            "user-id": user,
            "password": password
        },
        "organization-information": {
            "organization-id": organization,
            "center-contact-list": {
                "center-contact-details": {
                    "center-id": center
                }
            }
        },
        "organization-requesting": {
            "organization-id": organisationreq,
            "center-contact-list": {
                "center-contact-details": {
                    "center-id": centerreq
                }
            }
        },
        "device-type": devicetype,
        "device-information-type": deviceinfo
    }
}

# Print parameters for verification
#print("Sending the following parameters to the SOAP service:")
#print(json.dumps(parameters, indent=4))

# Fetch data from SOAP service
try:
    result = client.service.dlDetectorDataRequest(**parameters)
except Fault as e:
    print(f"SOAP request failed: {e}")
    exit()

# Process the data if `result` is a list
if not result:
    print("No data returned from SOAP request.")
    exit()

data = []
for item in result:
    detector_list = getattr(item, 'detector-list', None)
    if not detector_list:
        continue
    
    detector_data_detail = getattr(detector_list, 'detector-data-detail', [])
    for detector in detector_data_detail:
        data.append({
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

# Set up local time for filename
datetime_str = datetime.now(local_timezone).strftime('%Y-%m-%d_%H-%M-%S')
directory = 'C:/Users/MSI/Desktop/json_data/'
filename = f"{datetime_str}.json"
filepath = os.path.join(directory, filename)

# Ensure the directory exists
if not os.path.exists(directory):
    os.makedirs(directory)

# Save data to JSON file
try:
    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"DATA SAVED TO JSON FILE SUCCESSFULLY: {filepath}")
except Exception as e:
    print(f"Failed to save JSON data to file: {e}")
