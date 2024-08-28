# app/main.py

from flask import Flask
from app.routes import bp as routes_bp
import threading
import os
import sys
from app.clients.rabbit_mq_client import RabbitMQClient
from app.services.pump_service import PumpService

def create_app():
    app = Flask(__name__, static_folder='static')

    env = os.getenv('FLASK_ENV', 'development')
    if env == 'development':
        app.config.from_object('app.config.DevelopmentConfig')
    elif env == 'docker':
        app.config.from_object('app.config.DockerConfig')
    else:
        app.config.from_object('app.config.Config')
    
    app.register_blueprint(routes_bp)
    return app

def handle_signal(signum, frame):
    print('MSPumpControl: Received signal:', signum)
    # Perform cleanup if needed
    sys.exit(0)

def start_message_processing(app):
    """Starts message processing in a separate thread with application context."""
    import app.services.pump_service as pump_service
    rabbitmq_client = RabbitMQClient(host=app.config['RABBITMQ_HOST'], queues=app.config['QUEUES'])
    pump_service = PumpService(rabbitmq_client=rabbitmq_client)
    
    processing_thread = threading.Thread(target=pump_service.start_listening, args=(app,))
    processing_thread.daemon = True
    processing_thread.start()
    print("MSPumpControl: Message processing thread started")