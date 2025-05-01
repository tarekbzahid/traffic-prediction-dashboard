import importlib
import importlib.metadata

required = {
    "flask": "Flask",
    "flask_socketio": "flask-socketio",
    "zeep": "zeep",
    "pytz": "pytz",
    "socketio": "python-socketio",
    "eventlet": "eventlet"
}

print("Checking required packages:\n")

for module_name, package_name in required.items():
    try:
        importlib.import_module(module_name)
        version = importlib.metadata.version(package_name)
        print(f"{package_name:20} ✅ Installed (v{version})")
    except ImportError:
        print(f"{package_name:20} ❌ Not Installed")
    except Exception as e:
        print(f"{package_name:20} ⚠ Error: {str(e)}")
