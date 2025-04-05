from typing import Self

import paho.mqtt.client as mqtt
from config import Config
from log import logger


class MQTTClient:
    def __init__(self: Self, config: Config):
        self.config = config.get_section("mqtt", error_msg=True)

        broker_address = self.config.get("broker_address", error_msg=True)
        port = self.config.get("port", 1883)
        username = self.config.get("username")
        password = self.config.get("password")

        self.handler = mqtt.Client()
        if username and password:
            self.handler.username_pw_set(username, password)

        self.handler.on_connect = self._on_connect
        self.handler.on_disconnect = self._on_disconnect

        try:
            self.handler.connect(broker_address, port, 60)
            self.handler.loop_start()
            logger.success(f"Connected to MQTT at {broker_address}:{port}")
        except Exception as e:
            logger.error(f"Connecting to MQTT {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.success("MQTT connection successful.")
        else:
            logger.error(f"Failed to connect to MQTT broker with result code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.info("Disconnected from MQTT")

    def set_subscribe_event(self: Self, callback: callable) -> None:
        self.handler.on_message = callback

    def set_publish_event(self: Self, callback: callable) -> None:
        self.handler.on_publish = callback
