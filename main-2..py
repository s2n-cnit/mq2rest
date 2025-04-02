import json
import os
import time

import paho.mqtt.client as mqtt
import requests
import yaml


class Config:
    """
    A class to load configuration parameters from a YAML file.
    """
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        self._config_data = self._load_config()

    def _load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Error: Configuration file '{self.config_file}' not found.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file '{self.config_file}': {e}")
            return {}

    def get(self, key, default=None):
        return self._config_data.get(key, default)

    def __getitem__(self, key):
        if key not in self._config_data:
            raise KeyError(f"'{key}' not found in configuration file '{self.config_file}'.")
        return self._config_data[key]

    def __contains__(self, key):
        return key in self._config_data

    def get_section(self, section_name, default=None):
        return self._config_data.get(section_name, default)

    def all(self):
        return self._config_data


class APIMQTTBridge:
    def __init__(self, config_file="config.yaml"):
        self.config = Config(config_file)
        self.mqtt_config = self.config.get_section("mqtt")
        self.api_mqtt_mapping = self.config.get_section("api_mqtt_mapping")
        self.mqtt_client = self._connect_mqtt()

    def _connect_mqtt(self):
        if not self.mqtt_config:
            print("Error: MQTT configuration not found in config file.")
            return None

        broker_address = self.mqtt_config.get("broker_address")
        port = self.mqtt_config.get("port", 1883)
        username = self.mqtt_config.get("username")
        password = self.mqtt_config.get("password")

        if not broker_address:
            print("Error: MQTT broker address not configured.")
            return None

        client = mqtt.Client()
        if username and password:
            client.username_pw_set(username, password)

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_publish = self._on_publish

        try:
            client.connect(broker_address, port, 60)
            client.loop_start()
            print(f"Connected to MQTT Broker at {broker_address}:{port}")
            return client
        except Exception as e:
            print(f"Error connecting to MQTT Broker: {e}")
            return None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT Connection successful.")
        else:
            print(f"Failed to connect to MQTT Broker with result code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT Broker.")

    def _on_publish(self, client, userdata, mid):
        print(f"Message published [MID: {mid}]")

    def fetch_and_publish(self):
        if not self.api_mqtt_mapping or not self.mqtt_client:
            print("Error: API-MQTT mapping or MQTT client not initialized.")
            return

        for api_config in self.api_mqtt_mapping:
            api_url = api_config.get("url")
            http_method = api_config.get("method", "GET").upper()
            mqtt_topic = api_config.get("topic")
            headers = api_config.get("headers", {})
            payload = api_config.get("payload")
            polling_interval = api_config.get("polling_interval", 60)  # Default to 60 seconds

            if not api_url or not mqtt_topic:
                print(f"Warning: Missing URL or MQTT topic in API mapping: {api_config}")
                continue

            print(f"Fetching data from: {api_url} (Method: {http_method}), "
                  "Publishing to: {mqtt_topic} every {polling_interval} seconds.")

            def fetch_and_publish_loop(url, method, topic, headers, payload, interval, client):
                while True:
                    try:
                        if method == "GET":
                            response = requests.get(url, headers=headers)
                        elif method == "POST":
                            response = requests.post(url, headers=headers, json=payload)
                        elif method == "PUT":
                            response = requests.put(url, headers=headers, json=payload)
                        elif method == "DELETE":
                            response = requests.delete(url, headers=headers)
                        else:
                            print(f"Error: Unsupported HTTP method '{method}' for URL: {url}")
                            break

                        response.raise_for_status()  # Raise an exception for bad status codes
                        data = response.json()
                        payload_str = json.dumps(data)
                        if client and client.is_connected():
                            result = client.publish(topic, payload_str)
                            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                                print(f"Published to '{topic}': {payload_str[:50]}...")
                            else:
                                print(f"Error publishing to '{topic}': {result}")
                        else:
                            print("Error: MQTT client not connected, cannot publish.")

                    except requests.exceptions.RequestException as e:
                        print(f"HTTP request to '{url}' failed: {e}")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON response from '{url}': {e}")
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")

                    time.sleep(interval)

            import threading
            thread = threading.Thread(target=fetch_and_publish_loop,
                                      args=(api_url, http_method, mqtt_topic, headers, payload,
                                            polling_interval, self.mqtt_client), daemon=True)
            thread.start()

        while True:
            time.sleep(1) # Keep the main thread alive for the background threads


if __name__ == "__main__":
    # Create a sample config.yaml file in the same directory:
    """
    mqtt:
      broker_address: "YOUR_MQTT_BROKER_ADDRESS"  # Replace with your MQTT broker address
      port: 1883
      username: "YOUR_MQTT_USERNAME"          # Optional
      password: "YOUR_MQTT_PASSWORD"          # Optional

    api_mqtt_mapping:
      - name: "get_users"
        url: "https://jsonplaceholder.typicode.com/users"
        method: "GET"
        topic: "api/users"
        polling_interval: 10
        headers:
          Content-Type: "application/json"
      - name: "get_todos"
        url: "https://jsonplaceholder.typicode.com/todos/1"
        method: "GET"
        topic: "api/todos/1"
        polling_interval: 5
        headers:
          Content-Type: "application/json"
      - name: "post_data"
        url: "https://httpbin.org/post"
        method: "POST"
        topic: "api/post_data"
        polling_interval: 20
        headers:
          Content-Type: "application/json"
        payload:
          message: "Hello from Python"
          timestamp: "{{timestamp}}" # Example of a placeholder
    """
    # Note: Replace "YOUR_MQTT_BROKER_ADDRESS", etc., in the config.yaml

    # You might want to create the config.yaml file programmatically for the first run:
    if not os.path.exists("config.yaml"):
        default_config = {
            "mqtt": {
                "broker_address": "YOUR_MQTT_BROKER_ADDRESS",
                "port": 1883,
                "username": "YOUR_MQTT_USERNAME",
                "password": "YOUR_MQTT_PASSWORD",
            },
            "api_mqtt_mapping": [
                {
                    "name": "example_get",
                    "url": "https://api.example.com/data",
                    "method": "GET",
                    "topic": "api/example_data",
                    "polling_interval": 60,
                    "headers": {
                        "Content-Type": "application/json"
                    }
                }
            ]
        }
        with open("config.yaml", "w") as f:
            yaml.dump(default_config, f, default_flow_style=False)
        print("Created a default config.yaml file. Please edit it with your settings.")
    else:
        bridge = APIMQTTBridge()
        if bridge.mqtt_client:
            bridge.fetch_and_publish()
