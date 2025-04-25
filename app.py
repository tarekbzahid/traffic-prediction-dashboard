from flask import Flask, render_template, jsonify
import random

app = Flask(__name__)

# Bellagio starting position
bellagio_coords = [36.1126, -115.1767]

@app.route("/")
def index():
    return render_template("map.html")

@app.route("/data")
def data():
    # Simulate slight movement
    lat_variation = random.uniform(-0.0005, 0.0005)
    lon_variation = random.uniform(-0.0005, 0.0005)
    new_lat = bellagio_coords[0] + lat_variation
    new_lon = bellagio_coords[1] + lon_variation

    return jsonify({"lat": new_lat, "lon": new_lon})

if __name__ == "__main__":
    app.run(debug=True)