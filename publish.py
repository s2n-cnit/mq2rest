import time
from threading import Thread
from typing import Self

import paho.mqtt.client as mqtt
from config import Config
from data_translator import translate
from log import logger
from mqtt_client import MQTTClient, MQTTType
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from rest_http_client import RESTHTTPClient


class Publish:
    def __init__(self: Self, config: Config, rest_http_client: RESTHTTPClient) -> None:
        self.config = config.get("publish", error_msg=True)
        self.rest_http_client = rest_http_client
        self.mqtt_client = MQTTClient(config=config, type=MQTTType.Publish,
                                      on_connect=self._on_connect, on_event=self._on_event)

    def run(self: Self) -> None:
        self.mqtt_client.run()

    def _on_connect(self, client, userdata, flags, rc, properties):
        for record in self.config:
            rest_endpoint = record.get("rest_endpoint")
            rest_method = record.get("rest_method", "GET").upper()
            mqtt_topic = record.get("mqtt_topic")
            polling_interval = record.get("polling_interval", 60)  # Default to 60 seconds
            message_id = record.get("message_id")
            body = record.get("body")

            logger.info(f"Fetching data from: {rest_endpoint} (Rest_method: {rest_method}), "
                        f"Publishing to: {mqtt_topic} every {polling_interval} seconds.")

            def publish_loop(endpoint: str, rest_method: str, mqtt_topic: str, body: dict,
                             interval: int, mqtt_client: MQTTClient, properties: Properties):
                def _callback(data: dict) -> None:
                    out_data = translate(data=data, template=body)
                    logger.info(f"Publish to {mqtt_topic} : {out_data} {properties}")
                    result = mqtt_client.publish(mqtt_topic, out_data, 1, properties=properties)
                    logger.info(f"Result: {result}")
                    if result[0] == mqtt.MQTT_ERR_SUCCESS:
                        logger.info(f"Published to '{mqtt_topic}': {out_data[:50]}...")
                    else:
                        logger.error(f"Publishing to '{mqtt_topic}': {result}")

                while True:
                    self.rest_http_client.run(endpoint=endpoint, method=rest_method, data={}, callback=_callback)
                    time.sleep(interval)

            properties = Properties(PacketTypes.PUBLISH)
            properties.UserProperty = ("MessageId", message_id)
            thread = Thread(target=publish_loop,
                            args=(rest_endpoint, rest_method, mqtt_topic, body, polling_interval,
                                  self.mqtt_client, properties),
                            daemon=True)
            thread.start()
        while True:
            time.sleep(1)  # Keep the main thread alive for the background threads

    def _on_event(self, client, userdata, mid):
        logger.info(f"Message published [MID: {mid}]")
