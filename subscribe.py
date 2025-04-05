from threading import Thread
from typing import Self

from config import Config
from log import logger
from mqtt_client import MQTTClient
from rest_http_client import RESTHTTPClient


class Subscribe:
    def __init__(self: Self, config: Config, mqtt_client: MQTTClient, rest_http_client: RESTHTTPClient) -> None:
        self.config = config.get("subscribe", error_msg=True)
        self.mqtt_client = mqtt_client
        self.rest_http_client = rest_http_client

    def run(self: Self) -> None:
        for record in self.config:
            mqtt_topic = record.get("mqtt_topic", error_msg=True)
            self.mqtt_client.subscribe(mqtt_topic)
            self.topics[mqtt_topic] = record
            logger.info(f"Subscribe to: {mqtt_topic}")

        self.mqtt_client.set_subscribe_event(self._on_event)
        thread = Thread(target=self.mqtt_client.loop_forever, daemon=True)
        thread.start()

    def _on_event(self, client, userdata, msg):
        record = self.topics.get(msg.topic, None)
        if not record:
            logger.warning(f"Unknown topic: {msg.topic}")
            return

        rest_endpoint = record.get("rest_endpoint")
        rest_method = record.get("rest_method", "GET").upper()
        headers = record.get("headers", {})
        url = self.config_http.base_url + "/" + rest_endpoint

        def _callback(data: dict) -> None:
            logger.info(f"Response from {url} {rest_method}: {data}")

        self.rest_http_client.run(url=url, method=rest_method, headers=headers,
                                  data=msg.payload, callback=_callback)
