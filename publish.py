import json
import time
from threading import Thread
from typing import Self

import paho.mqtt.client as mqtt
from config import Config
from log import logger
from mqtt_client import MQTTClient
from rest_http_client import RESTHTTPClient


class Publish:
    def __init__(self: Self) -> None:
        def __init__(self: Self, config: Config, mqtt_client: MQTTClient, rest_http_client: RESTHTTPClient) -> None:
            self.config = config.get("publish", error_msg=True)
            self.mqtt_client = mqtt_client
            self.mqtt_client.set_publish_event(self._on_event)
            self.rest_http_client = rest_http_client

    def run(self: Self) -> None:
        for record in self.config:
            rest_endpoint = record.get("rest_endpoint", error_msg=True)
            rest_method = record.get("rest_method", "GET").upper()
            mqtt_topic = record.get("mqtt_topic")
            headers = record.get("headers", {})
            payload = record.get("payload")
            polling_interval = record.get("polling_interval", 60)  # Default to 60 seconds

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
                    self.rest_http_client.run(url=url, method=rest_method, headers=headers, data=payload,
                                              callback=_callback)
                    time.sleep(interval)

            url = self.config_http.base_url + "/" + rest_endpoint
            thread = Thread(target=publish_loop,
                            args=(url, rest_method, mqtt_topic, headers, payload,
                                  polling_interval, self.mqtt_client), daemon=True)
            thread.start()
        while True:
            time.sleep(1)  # Keep the main thread alive for the background threads

    def _on_event(self, client, userdata, mid):
        logger.info(f"Message published [MID: {mid}]")
