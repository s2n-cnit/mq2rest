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
