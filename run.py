# run.py

import signal
import sys
import os
from app.main import create_app, start_message_processing

app = create_app()

def handle_shutdown_signal(signum, frame):
    print("MSPumpControl: Shutdown signal received. Stopping the message processing and Flask server...")
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    
    if not app.debug or os.getenv('WERKZEUG_RUN_MAIN') == 'true':
        print("MSPumpControl: Starting Flask app...")
        print("MSPumpControl: Starting message processing...")
        start_message_processing(app)
    app.run(debug=True, host='0.0.0.0', port=5004)