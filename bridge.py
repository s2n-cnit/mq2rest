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
