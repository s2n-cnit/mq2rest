from enum import Enum
from threading import Thread
from typing import Self

import paho.mqtt.client as mqtt
from config import Config
from log import logger
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties


class MQTTType(Enum):
    Publish = 1
    Subscribe = 2


class MQTTClient:
    def __init__(self: Self, config: Config, type: MQTTType, on_connect: callable, on_event: callable) -> None:
        self.config = config.get("mqtt", error_msg=True)
        self.type = type

        self.host = self.config.get("host", error_msg=True)
        self.port = self.config.get("port", 1883)
        self.username = self.config.get("username")
        self.password = self.config.get("password")

        self.properties = Properties(PacketTypes.CONNECT)
        self.properties.MaximumPacketSize = 20
        self.handler = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "m2rest-mqtt5_client", protocol=mqtt.MQTTv5)
        if self.username and self.password:
            self.handler.username_pw_set(self.username, self.password)

        self.handler.on_connect = on_connect
        self.handler.on_disconnect = self._on_disconnect

        match self.type:
            case MQTTType.Publish:
                self.publish = self.handler.publish
                self.handler.on_publish = on_event
            case MQTTType.Subscribe:
                self.subscribe = self.handler.subscribe
                self.handler.on_message = on_event

    def run(self: Self) -> None:
        Thread(target=self._run).start()

    def _run(self: Self) -> None:
        try:
            self.handler.connect(self.host, self.port, 60)
            logger.success(f"Connected to MQTT at {self.host}:{self.port}")
            match self.type:
                case MQTTType.Publish:
                    self.handler.loop_start()
                case MQTTType.Subscribe:
                    self.handler.loop_forever()
        except Exception as e:
            logger.error(f"Connecting to MQTT {e}")

    def _on_disconnect(self, client, userdata, rc, properties, c):
        logger.info("Disconnected from MQTT")
