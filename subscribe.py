from typing import Self

from config import Config
from data_translator import translate
from log import logger
from mqtt_client import MQTTClient, MQTTType
from rest_http_client import RESTHTTPClient


class Subscribe:
    def __init__(self: Self, config: Config, rest_http_client: RESTHTTPClient) -> None:
        self.config = config.get("subscribe", error_msg=True)
        self.rest_http_client = rest_http_client
        self.topics = {}
        self.mqtt_client = MQTTClient(config=config, type=MQTTType.Subscribe,
                                      on_connect=self._on_connect, on_event=self._on_event)

    def run(self: Self) -> None:
        self.mqtt_client.run()

    def _on_connect(self, client, userdata, flags, rc):
        for record in self.config:
            mqtt_topic = record.get("mqtt_topic")
            self.mqtt_client.subscribe(mqtt_topic)
            self.topics[mqtt_topic] = record
            logger.info(f"Subscribe to: {mqtt_topic}")

    def _on_event(self, client, userdata, msg):
        record = self.topics.get(msg.topic, None)
        if not record:
            logger.warning(f"Unknown topic: {msg.topic}")
            return

        rest_endpoint = record.get("rest_endpoint")
        rest_method = record.get("rest_method", "GET").upper()
        body = record.get("body")

        def _callback(data: dict) -> None:
            logger.info(f"Response from {rest_endpoint} {rest_method}: {data}")

        out_data = translate(data=msg.payload.decode(), template=body)

        self.rest_http_client.run(endpoint=rest_endpoint, method=rest_method, data=out_data, callback=_callback)
