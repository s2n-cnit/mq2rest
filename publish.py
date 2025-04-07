import json
import time
from threading import Thread
from typing import Self

import paho.mqtt.client as mqtt
from config import Config
from jinja2 import Template
from log import logger
from mqtt_client import MQTTClient
from parse import parse
from rest_http_client import RESTHTTPClient


class Publish:
    def __init__(self: Self, config: Config, mqtt_client: MQTTClient, rest_http_client: RESTHTTPClient) -> None:
        self.config = config.get("publish", error_msg=True)
        self.mqtt_client = mqtt_client
        self.mqtt_client.set_publish_event(self._on_event)
        self.rest_http_client = rest_http_client

    def run(self: Self) -> None:
        for record in self.config:
            rest_endpoint = record.get("rest_endpoint")
            rest_method = record.get("rest_method", "GET").upper()
            mqtt_topic = record.get("mqtt_topic")
            headers = record.get("headers", {})
            polling_interval = record.get("polling_interval", 60)  # Default to 60 seconds
            body = record.get("body")

            logger.info(f"Fetching data from: {rest_endpoint} (Rest_method: {rest_method}), "
                        "Publishing to: {mqtt_topic} every {polling_interval} seconds.")

            def publish_loop(endpoint, rest_method, mqtt_topic, headers, body, interval, client):
                while True:
                    def _callback(data: dict) -> None:
                        in_data = json.dumps(data)
                        r = parse(body.get("in"), in_data)
                        out_data = Template(body.out).render(dict(**r))
                        result = client.publish(mqtt_topic, out_data)
                        if result[0] == mqtt.MQTT_ERR_SUCCESS:
                            logger.info(f"Published to '{mqtt_topic}': {out_data[:50]}...")
                        else:
                            logger.error(f"Publishing to '{mqtt_topic}': {result}")
                    self.rest_http_client.run(endpoint=endpoint, method=rest_method, headers=headers,
                                              callback=_callback)
                    time.sleep(interval)

            thread = Thread(target=publish_loop,
                            args=(rest_endpoint, rest_method, mqtt_topic, headers, body,
                                  polling_interval, self.mqtt_client), daemon=True)
            thread.start()
        while True:
            time.sleep(1)  # Keep the main thread alive for the background threads

    def _on_event(self, client, userdata, mid):
        logger.info(f"Message published [MID: {mid}]")
