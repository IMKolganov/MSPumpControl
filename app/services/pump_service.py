# app/services/pump_service.py

import random
import json
import time
import pika
from datetime import datetime

from app.messages.start_pump_request_message import StartPumpRequestMessage

class PumpService:
    def __init__(self, rabbitmq_client):
        self.rabbitmq_client = rabbitmq_client

    def handle_request(self, ch, method, properties, body, app):
        try:
            request_data = json.loads(body)
            print("PumpService: Receive message")
            print(f"PumpService: {request_data}")
            method_name = request_data.get('MethodName')
            correlation_id = properties.correlation_id
            request_id = request_data.get('RequestId')
            pump_id = request_data.get('PumpId', 0)

            if method_name == 'start-pump':
                if request_data.get('WithoutMSMicrocontrollerManager'):
                    # If the request comes with the WithoutMSMicrocontrollerManager flag
                    self.send_request_without_ms_microcontroller_manager(app, ch, request_id, method_name, pump_id, correlation_id, method)
                    return
                
                self.send_request_to_ms_microcontroller_manager(app, request_id, method_name, pump_id, correlation_id)
                pump_response = self.receive_answer_from_ms_microcontroller_manager(app, correlation_id, ch, method)
                self.send_result_to_backend(app, ch, pump_response, correlation_id, method)

            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                print(f"PumpService: Unhandled method '{method_name}'. Message nack'ed.")
        except Exception as e:
            print(f"PumpService: Error while receiving message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            print(f"PumpService: Message handling failed due to error: {e}")

    def start_listening(self, app):
        time.sleep(3)  # Delay for service readiness
        print("PumpService: Starting to process messages...")
        self.rabbitmq_client.start_queue_listener(
            queue_name=app.config['BACKEND_TO_MSPUMPCONTROL_REQUEST_QUEUE'],
            on_message_callback=lambda ch, method, properties, body: self.handle_request(ch, method, properties, body, app)
        )
        print("PumpService: Listening for messages...")
    
    
    
    
    def send_request_to_ms_microcontroller_manager(self, app, request_id, method_name, pump_id, correlation_id):
        message = StartPumpRequestMessage(
            request_id=request_id,
            method_name=method_name,
            pump_id=pump_id,
            create_date=datetime.utcnow().isoformat(),
            additional_info={"request_origin": "MSPumpControl"}
        )
        # Send request to MSMicrocontrollerManager
        self.rabbitmq_client.send_message(
            queue_name=app.config['MSPUMPCONTROL_TO_MSMICROCONTROLLERMANAGER_REQUEST_QUEUE'],
            message=message,
            correlation_id=correlation_id,
            reply_to=app.config['MSMICROCONTROLLERMANAGER_TO_MSPUMPCONTROL_RESPONSE_QUEUE']
        )
        print(f"PumpService: Request sent to MSMicrocontrollerManager.")

    def receive_answer_from_ms_microcontroller_manager(self, app, correlation_id, ch, method):
        print("PumpService: Waiting for response...")
        try:
            pump_response = self.rabbitmq_client.receive_message(
                queue_name=app.config['MSMICROCONTROLLERMANAGER_TO_MSPUMPCONTROL_RESPONSE_QUEUE'],
                correlation_id=correlation_id,
                timeout=5  # Timeout in seconds
            )

            if pump_response:
                return pump_response
        
            else:
                # Timeout expired, message not processed
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                print(f"Timeout expired. No response from MSMicrocontrollerManager. Message not processed.")

        except Exception as e:
            print(f"Fatal error: {e}")

    def send_result_to_backend(self, app, ch, pump_response, correlation_id, method):
        response_message = self.prepare_response(pump_response)

        ch.basic_publish(
            exchange='',
            routing_key=app.config['MSPUMPCONTROL_TO_BACKEND_RESPONSE_QUEUE'],
            body=json.dumps(response_message),
            properties=pika.BasicProperties(
                correlation_id=correlation_id
            )
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"PumpService: Received response from MSMicrocontrollerManager. Response sent to "
                +f"{app.config['MSPUMPCONTROL_TO_BACKEND_RESPONSE_QUEUE']}")
        print(json.dumps(response_message))
        
    def send_request_without_ms_microcontroller_manager(self, app, ch, request_id, 
                                                        method_name, pump_id, correlation_id, method):
        pump_response = {
            'RequestId': request_id,
            'MethodName': method_name,
            'PumpId': pump_id,
            'CreateDate': datetime.utcnow().isoformat(),
        }

        response_message = self.prepare_response(pump_response)
        
        ch.basic_publish(
            exchange='',
            routing_key=app.config['MSPUMPCONTROL_TO_BACKEND_RESPONSE_QUEUE'],
            body=json.dumps(response_message),
            properties=pika.BasicProperties(
                correlation_id=correlation_id
            )
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"PumpService: Handled 'start-pump' request without MSMicrocontrollerManager. "
                + f"Response sent to {app.config['MSPUMPCONTROL_TO_BACKEND_RESPONSE_QUEUE']}")
        print(f"PumpService: {json.dumps(response_message)}")
        return

    def prepare_response(self, pump_response):
        error_message = ""
        return {
            'RequestId': pump_response.get('RequestId'),
            'MethodName': pump_response.get('MethodName'),
            'PumpId': pump_response.get('PumpId'),
            'CreateDate': datetime.utcnow().isoformat(),
            'ErrorMessage': error_message,
        }