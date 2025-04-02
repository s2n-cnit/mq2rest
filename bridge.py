import json
import time
from typing import Self

import paho.mq.client as mq
import requests
from config import Config
from log import logger


class Bridge:
    def __init__(self: Self, config: Config):
        self.config_rest = config.get_section("rest")
        self.config_mq = config.get_section("mq")
        self.config_binding = config.get_section("binding")
        self.mq_client = self._connect_mq()

    def _connect_mq(self: Self):
        if not self.config_mq:
            logger.error("MQ configuration not found in config file.")
            return None

        broker_address = self.config_mq.get("broker_address")
        port = self.config_mq.get("port", 1883)
        username = self.config_mq.get("username")
        password = self.config_mq.get("password")

        if not broker_address:
            logger.error("MQ broker address not configured.")
            return None

        client = mq.Client()
        if username and password:
            client.username_pw_set(username, password)

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_publish = self._on_publish

        try:
            client.connect(broker_address, port, 60)
            client.loop_start()
            logger.success(f"Connected to MQ Broker at {broker_address}:{port}")
            return client
        except Exception as e:
            logger.error(f"Connecting to MQ Broker: {e}")
            return None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.success("MQ Connection successful.")
        else:
            logger.error(f"Failed to connect to MQ Broker with result code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.info("Disconnected from MQ Broker.")

    def _on_publish(self, client, userdata, mid):
        logger.info(f"Message published [MID: {mid}]")

    def subscribe(self: Self) -> None:
        pass

    def publish(self: Self) -> None:
        if not self.config_binding or not self.mq_client:
            logger.error("Mapping or MQ client not initialized.")
            return

        for binding_record in self.config_binding:
            rest_endpoint = binding_record.get("rest_endpoint")
            rest_method = binding_record.get("rest_method", "GET").upper()
            mq_topic = binding_record.get("mq_topic")
            headers = binding_record.get("headers", {})
            payload = binding_record.get("payload")
            polling_interval = binding_record.get("polling_interval", 60)  # Default to 60 seconds

            if not rest_endpoint or not mq_topic:
                print(f"Warning: Missing URL or MQ mq_topic in Binding: {binding_record}")
                continue
            logger.info(f"Fetching data from: {rest_endpoint} (Rest_method: {rest_method}), "
                        "Publishing to: {mq_mq_topic} every {polling_interval} seconds.")

            def fetch_and_publish_loop(url, rest_method, mq_topic, headers, payload, interval, client):
                while True:
                    try:
                        if rest_method == "GET":
                            response = requests.get(url, headers=headers)
                        elif rest_method == "POST":
                            response = requests.post(url, headers=headers, json=payload)
                        elif rest_method == "PUT":
                            response = requests.put(url, headers=headers, json=payload)
                        elif rest_method == "DELETE":
                            response = requests.delete(url, headers=headers)
                        else:
                            logger.error(f"Unsupported HTTP method '{rest_method}' for URL: {url}")
                            break
                        response.raise_for_status()  # Raise an exception for bad status codes
                        data = response.json()
                        payload_str = json.dumps(data)
                        if client and client.is_connected():
                            result = client.publish(mq_topic, payload_str)
                            if result[0] == mq.MQ_ERR_SUCCESS:
                                logger.info(f"Published to '{mq_topic}': {payload_str[:50]}...")
                            else:
                                logger.error(f"Publishing to '{mq_topic}': {result}")
                        else:
                            print("Error: MQ client not connected, cannot publish.")
                    except requests.exceptions.RequestException as e:
                        logger.error(f"HTTP request to '{url}' failed: {e}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Decoding JSON response from '{url}': {e}")
                    except Exception as e:
                        logger.error(f"Unexpected error occurred: {e}")
                    time.sleep(interval)

            import threading

            url = self.config_http.base_url + "/" + rest_endpoint
            thread = threading.Thread(target=fetch_and_publish_loop,
                                      args=(url, rest_method, mq_topic, headers, payload,
                                            polling_interval, self.mq_client), daemon=True)
            thread.start()
        while True:
            time.sleep(1)  # Keep the main thread alive for the background threads


import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pika  # For RabbitMQ (you might need other libraries for different MQs)
import requests

# --- Configuration ---
MQ_HOST = 'localhost'  # Replace with your MQ host
MQ_QUEUE = 'mq_to_http'  # Queue to subscribe to for HTTP calls
HTTP_API_URL_MAPPING = {
    'user.created': 'https://api.example.com/users',
    'order.placed': 'https://api.example.com/orders'
    # Add more mappings based on routing key or message content
}
HTTP_REQUEST_METHOD_MAPPING = {
    'user.created': 'POST',
    'order.placed': 'POST'
    # Define HTTP methods per message type/routing key
}
HTTP_AUTH_TOKEN = 'your_api_token'  # Optional: API authentication token

BRIDGE_HTTP_HOST = 'localhost'
BRIDGE_HTTP_PORT = 8080
HTTP_TO_MQ_EXCHANGE = 'http_to_mq'  # Exchange to publish messages from HTTP
HTTP_TO_MQ_ROUTING_KEY = 'incoming.http' # Default routing key for HTTP messages

# --- MQ to HTTP Bridge ---
def process_mq_message(ch, method, properties, body):
    try:
        message = json.loads(body.decode())
        routing_key = method.routing_key  # Or determine target API based on message content

        if routing_key in HTTP_API_URL_MAPPING:
            api_url = HTTP_API_URL_MAPPING[routing_key]
            http_method = HTTP_REQUEST_METHOD_MAPPING.get(routing_key, 'POST')  # Default to POST

            headers = {'Content-Type': 'application/json'}
            if HTTP_AUTH_TOKEN:
                headers['Authorization'] = f'Bearer {HTTP_AUTH_TOKEN}'

            print(f"Received MQ message (routing key: {routing_key}): {message}")
            print(f"Sending HTTP {http_method} request to: {api_url}")

            try:
                if http_method == 'POST':
                    response = requests.post(api_url, headers=headers, json=message)
                elif http_method == 'GET':
                    response = requests.get(api_url, headers=headers, params=message) # Assuming message can be query params
                elif http_method == 'PUT':
                    response = requests.put(api_url, headers=headers, json=message)
                elif http_method == 'DELETE':
                    response = requests.delete(api_url, headers=headers, json=message)
                else:
                    print(f"Unsupported HTTP method: {http_method}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                response.raise_for_status()  # Raise an exception for bad status codes
                print(f"HTTP Request successful. Status: {response.status_code}, Response: {response.text}")
                # Optionally process the API response and potentially send a message back to MQ
            except requests.exceptions.RequestException as e:
                print(f"Error during HTTP request: {e}")
            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error: {e.response.status_code} - {e.response.text}")

        else:
            print(f"No HTTP API URL mapping found for routing key: {routing_key}")

    except json.JSONDecodeError:
        print(f"Error decoding JSON from MQ message: {body.decode()}")
    except Exception as e:
        print(f"Error processing MQ message: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_mq():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(MQ_HOST))
        channel = connection.channel()

        channel.exchange_declare(exchange='amq.direct', exchange_type='direct') # Assuming direct exchange
        channel.queue_declare(queue=MQ_QUEUE, durable=True)
        channel.queue_bind(exchange='amq.direct', queue=MQ_QUEUE, routing_key=MQ_QUEUE) # Bind with queue name

        # You might want to bind to different routing keys based on your needs
        # channel.queue_bind(exchange='amq.direct', queue=MQ_QUEUE, routing_key='user.created')
        # channel.queue_bind(exchange='amq.direct', queue=MQ_QUEUE, routing_key='order.*')

        channel.basic_qos(prefetch_count=1)  # Process one message at a time
        channel.basic_consume(queue=MQ_QUEUE, on_message_callback=process_mq_message)

        print(f" [*] Waiting for messages on queue '{MQ_QUEUE}'. To exit press CTRL+C")
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        print(f"Error connecting to MQ: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in the MQ consumer: {e}")

# --- HTTP to MQ Bridge ---
class HTTPToMQHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            message = json.loads(post_data.decode())
            routing_key = query_params.get('routing_key', [HTTP_TO_MQ_ROUTING_KEY])[0] # Get routing key from query or default

            connection = pika.BlockingConnection(pika.ConnectionParameters(MQ_HOST))
            channel = connection.channel()
            channel.exchange_declare(exchange=HTTP_TO_MQ_EXCHANGE, exchange_type='topic', durable=True) # Using topic exchange

            channel.basic_publish(exchange=HTTP_TO_MQ_EXCHANGE,
                                  routing_key=routing_key,
                                  properties=pika.BasicProperties(delivery_mode=2), # Make message persistent
                                  body=json.dumps(message).encode())
            print(f" [x] Sent message to MQ (exchange: {HTTP_TO_MQ_EXCHANGE}, routing_key: {routing_key}): {message}")
            connection.close()

            self.send_response(202)  # Accepted
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {'status': 'success', 'message_sent': True}
            self.wfile.write(json.dumps(response_data).encode())

        except json.JSONDecodeError:
            self.send_response(400)  # Bad Request
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {'status': 'error', 'message': 'Invalid JSON payload'}
            self.wfile.write(json.dumps(response_data).encode())
        except pika.exceptions.AMQPConnectionError as e:
            self.send_response(503)  # Service Unavailable
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {'status': 'error', 'message': f'Error connecting to MQ: {e}'}
            self.wfile.write(json.dumps(response_data).encode())
        except Exception as e:
            self.send_response(500)  # Internal Server Error
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {'status': 'error', 'message': f'Internal server error: {e}'}
            self.wfile.write(json.dumps(response_data).encode())

def run_http_server():
    server_address = (BRIDGE_HTTP_HOST, BRIDGE_HTTP_PORT)
    httpd = HTTPServer(server_address, HTTPToMQHandler)
    print(f" [*] HTTP to MQ bridge listening on http://{BRIDGE_HTTP_HOST}:{BRIDGE_HTTP_PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    # Start the MQ consumer in a separate thread
    mq_thread = threading.Thread(target=consume_mq)
    mq_thread.daemon = True
    mq_thread.start()

    # Start the HTTP server in the main thread (or another thread if needed)
    run_http_server()
