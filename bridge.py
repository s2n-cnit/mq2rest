import json
import time
from threading import Thread
from typing import Self

import paho.mqtt.client as mqtt
import requests
from config import Config
from log import logger


class Bridge:
    def __init__(self: Self, config: Config):
        self.config_rest = config.get_section("rest")
        self.config_mqtt = config.get_section("mqtt")
        self.config_publish = config.get_section("publish")
        self.config_subscribe = config.get_section("subscribe")
        self.mqtt_client = self._connect_mqtt()
        self.subscribe_topics = {}

    def _connect_mq(self: Self):
        if not self.config_mqtt:
            logger.error("MQTT configuration not found in config file.")
            return None

        broker_address = self.config_mqtt.get("broker_address")
        port = self.config_mqtt.get("port", 1883)
        username = self.config_mqtt.get("username")
        password = self.config_mqtt.get("password")

        if not broker_address:
            logger.error("MQTT broker address not configured.")
            return None

        client = mqtt.Client()
        if username and password:
            client.username_pw_set(username, password)

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_publish = self._on_publish
        client.on_message = self._on_message

        try:
            client.connect(broker_address, port, 60)
            client.loop_start()
            logger.success(f"Connected to MQTTBroker at {broker_address}:{port}")
            return client
        except Exception as e:
            logger.error(f"Connecting to MQTTBroker: {e}")
            return None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.success("MQTT connection successful.")
        else:
            logger.error(f"Failed to connect to MQTT broker with result code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.info("Disconnected from MQTTBroker.")

    def _on_publish(self, client, userdata, mid):
        logger.info(f"Message published [MID: {mid}]")

    def _on_message(self, client, userdata, msg):
        subscribe_record = self.subscribe_topics.get(msg.topic, None)
        if not subscribe_record:
            logger.warning(f"Unknown topic: {msg.topic}")
            return

        rest_endpoint = subscribe_record.get("rest_endpoint")
        rest_method = subscribe_record.get("rest_method", "GET").upper()
        headers = subscribe_record.get("headers", {})
        url = self.config_http.base_url + "/" + rest_endpoint

        def _callback(data: dict) -> None:
            logger.info(f"Response from {url} {rest_method}: {data}")

        self._rest_mgmt(url=url, method=rest_method, headers=headers, data=msg.payload, callback=_callback)

    def subscribe(self: Self) -> None:
        if not self.config_subscribe or not self.mqtt_client:
            logger.error("Mapping for subscribe or MQTTclient not initialized.")
            return

        for subscribe_record in self.config_subscribe:
            mqtt_topic = subscribe_record.get("mqtt_topic")
            if not mqtt_topic:
                logger.warning(f"MQTT topic in Subscribe: {subscribe_record}")
                continue
            self.mqtt_client.subscribe(mqtt_topic)
            self.subscribe_topics[mqtt_topic] = subscribe_record
            logger.info(f"Subscribe to: {mqtt_topic}")

        thread = Thread(target=self.mqtt_client.loop_forever, daemon=True)
        thread.start()

    def publish(self: Self) -> None:
        if not self.config_publish or not self.mqtt_client:
            logger.error("Mapping for publish or MQTTclient not initialized.")
            return

        for publish_record in self.config_publish:
            rest_endpoint = publish_record.get("rest_endpoint")
            rest_method = publish_record.get("rest_method", "GET").upper()
            mqtt_topic = publish_record.get("mqtt_topic")
            headers = publish_record.get("headers", {})
            payload = publish_record.get("payload")
            polling_interval = publish_record.get("polling_interval", 60)  # Default to 60 seconds

            if not rest_endpoint or not mqtt_topic:
                print(f"Warning: Missing URL or MQTT topic in Publish: {publish_record}")
                continue
            logger.info(f"Fetching data from: {rest_endpoint} (Rest_method: {rest_method}), "
                        "Publishing to: {mqtt_topic} every {polling_interval} seconds.")

            def publish_loop(url, rest_method, mqtt_topic, headers, payload, interval, client):
                while True:
                    def _callback(data: dict) -> None:
                        payload_str = json.dumps(data)
                        result = client.publish(mqtt_topic, payload_str)
                        if result[0] == mqtt.MQTT_ERR_SUCCESS:
                            logger.info(f"Published to '{mqtt_topic}': {payload_str[:50]}...")
                        else:
                            logger.error(f"Publishing to '{mqtt_topic}': {result}")
                    self._rest_mgmt(url=url, method=rest_method, headers=headers, data=payload, callback=_callback)
                    time.sleep(interval)

            url = self.config_http.base_url + "/" + rest_endpoint
            thread = Thread(target=publish_loop,
                            args=(url, rest_method, mqtt_topic, headers, payload,
                                  polling_interval, self.mqtt_client), daemon=True)
            thread.start()
        while True:
            time.sleep(1)  # Keep the main thread alive for the background threads

    def _rest_mgmt(self: Self, url: str, method: str, headers: str, data: any, callback: callable) -> None:
        try:
            match method.lower():
                case "get": r = requests.get
                case "post": r = requests.post
                case "put": r = requests.put
                case "delete": r = requests.delete
                case _:
                    logger.error(f"Unsupported REST HTTP method '{method}' for URL: {url}")
                    return
            resp = r(url, headers=headers, data=data)
            resp.raise_for_status()  # Raise an exception for bad status codes
            callback(data=resp.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"REST HTTP request to '{url}' failed: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Decoding JSON response from '{url}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
