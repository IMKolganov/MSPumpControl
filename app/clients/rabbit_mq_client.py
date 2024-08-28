# app/clients/rabbit_mq_client.py

import pika
import json
import uuid
import threading
import time

class RabbitMQClient:
    def __init__(self, host, queues):
        self.host = host
        self.queues = queues

    def get_connection_and_channel(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )
        channel = connection.channel()
        
        for queue_name in self.queues:
            channel.queue_declare(queue=queue_name, durable=False, exclusive=False, auto_delete=False)
        
        return connection, channel

    def send_message(self, queue_name, message, correlation_id=None, reply_to=None):
        connection, channel = self.get_connection_and_channel()
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message.to_json(),
                properties=pika.BasicProperties(
                    correlation_id=correlation_id,
                    reply_to=reply_to
                )
            )
            print(f"Sent message to {queue_name}: {message.to_dict()}")
        finally:
            connection.close()

    def receive_message(self, queue_name, correlation_id, timeout=10):
        connection, channel = self.get_connection_and_channel()
        response = None

        def callback(ch, method, properties, body):
            if properties.correlation_id == correlation_id:
                nonlocal response
                response = json.loads(body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                ch.stop_consuming()

        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False
        )

        # Start consuming messages with timeout
        start_time = time.time()
        try:
            while response is None and (time.time() - start_time) < timeout:
                connection.process_data_events(time_limit=1)  # Process incoming data
                time.sleep(0.1)  # Short sleep to prevent excessive CPU usage
        except KeyboardInterrupt:
            channel.stop_consuming()
            print("Interrupted by user. Stopping message consumption.")
        finally:
            connection.close()

        if response is None:
            # Timeout expired, return an error message
            error_message = {
                "ErrorMessage": f"Timeout expired. No response received from the queue. "
                + f"Queue_name {queue_name}, correlation_id {correlation_id}",
            }
            print(f"Timeout expired. Error: {error_message}")
            return error_message

        return response

    def start_queue_listener(self, queue_name, on_message_callback):
        def run():
            connection, channel = self.get_connection_and_channel()
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=on_message_callback,
                auto_ack=False
            )

            print(f"Listening to {queue_name}...")
            try:
                channel.start_consuming()
            except KeyboardInterrupt:
                channel.stop_consuming()
            finally:
                connection.close()

        listener_thread = threading.Thread(target=run)
        listener_thread.start()
