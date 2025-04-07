from config import Config
from mqtt_client import MQTTClient
from publish import Publish
from rest_http_client import RESTHTTPClient
from subscribe import Subscribe

config = Config().from_path(path="config.yaml")
mqtt_client = MQTTClient(config=config)
rest_http_client = RESTHTTPClient(config=config)
Subscribe(config=config, mqtt_client=mqtt_client, rest_http_client=rest_http_client).run()
Publish(config=config, mqtt_client=mqtt_client, rest_http_client=rest_http_client).run()
