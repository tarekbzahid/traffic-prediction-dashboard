import os
import eventlet
eventlet.monkey_patch()  # ✅ Required for eventlet to work

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from zeep import Client, Settings
import json
import pytz
from datetime import datetime
import time

# ----------------------------
# 📍 Load Configuration
# ----------------------------
with open("config.json") as f:
    CONFIG = json.load(f)

TIME_STEP_MINUTES = CONFIG.get("time_step_minutes", 0.5)

# ----------------------------
# 📍 Flask App
# ----------------------------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ----------------------------
# 📍 Other configuration
# ----------------------------
local_timezone = pytz.timezone("America/Los_Angeles")
wsdl_url = "https://colondexsrv.its.nv.gov/tmddws/TmddWS.svc?singleWsdl"
metadata_path = "data/sensor_metadata.json"

latest_live_data = {"timestamp": None, "data": []}

# SOAP Settings
auth_params = {
    "user-id": "UNLV_TRC_RTIS",
    "password": "+r@^~Tr<R?|$"
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
# 📍 Fetch Live Data
# ----------------------------
def fetch_live_data():
    """Continuously fetch live traffic data and emit it via Socket.IO."""
    global latest_live_data

    settings = Settings(strict=False, xml_huge_tree=True)
    client = None

    while True:
        try:
            # Lazily initialize or reinitialize the SOAP client if needed.
            if client is None:
                try:
                    client = Client(wsdl=wsdl_url, settings=settings)
                    print("✅ SOAP client initialized")
                except Exception as e:
                    print(f"❌ Failed to connect to SOAP service: {e}")
                    client = None
                    # Sleep before retrying connection
                    time.sleep(TIME_STEP_MINUTES * 60)
                    continue

            # Fetch live detector data via SOAP
            response = client.service.dlDetectorDataRequest(**soap_parameters)
            if response:
                data = []
                for item in response:
                    detector_list = getattr(item, 'detector-list', None)
                    if not detector_list:
                        continue
                    for detector in getattr(detector_list, 'detector-data-detail', []):
                        data.append({
                            "stationId": getattr(detector, "station-id", None),
                            "detectorId": getattr(detector, "detector-id", None),
                            "vehicleOccupancy": getattr(detector, "vehicle-occupancy", None),
                            "vehicleSpeed": getattr(detector, "vehicle-speed", None),
                            "vehicleCount": getattr(detector, "vehicle-count", None)
                        })

                latest_live_data = {
                    "timestamp": datetime.now(local_timezone).strftime('%Y-%m-%d %H:%M:%S'),
                    "data": data
                }
                print(f"✅ Fetched {len(data)} detectors at {latest_live_data['timestamp']}")
                socketio.emit('new_data', latest_live_data)
                print("✅ Emitted new_data to frontend")
            else:
                print("⚠️ SOAP response was empty")

        except Exception as e:
            print(f"❌ SOAP request failed: {e}")
            # Reset client so we attempt to reconnect on the next iteration
            client = None

        # Sleep between polling intervals (cooperatively, thanks to eventlet.monkey_patch)
        time.sleep(TIME_STEP_MINUTES * 60)

# Start the background task after fetch_live_data is defined.
socketio.start_background_task(fetch_live_data)

# ----------------------------
# 📍 Flask Routes
# ----------------------------
@app.route("/")
def map_page():
    return render_template("map.html")

@app.route("/metadata")
def metadata():
    """Serve sensor metadata."""
    with open(metadata_path) as f:
        sensor_metadata = json.load(f)
    return jsonify(sensor_metadata)

@app.route("/config")
def config():
    """Serve configuration values."""
    return jsonify(CONFIG)

# ----------------------------
# 📍 Main
# ----------------------------
if __name__ == "__main__":
    # When running locally, this will start the server.
    # Under Gunicorn on Render, this block is not executed, but the background task has already started.
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
