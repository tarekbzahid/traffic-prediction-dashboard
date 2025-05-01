import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import SocketIO
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
      <title>Quick Test</title>
      <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    </head>
    <body>
      <h2>Socket.IO Quick Test</h2>
      <pre id="log"></pre>
      <script>
        const socket = io();
        const log = document.getElementById('log');
        socket.on('connect', () => {
          log.textContent += '✅ Connected to server\\n';
        });
        socket.on('new_data', data => {
          log.textContent += '📦 ' + JSON.stringify(data) + '\\n';
        });
      </script>
    </body>
    </html>
    '''

def emit_loop():
    while True:
        socketio.emit('new_data', {"time": time.strftime("%H:%M:%S")})
        print("✅ Emitted data")
        time.sleep(3)

if __name__ == '__main__':
    socketio.start_background_task(emit_loop)
    socketio.run(app, debug=True)
