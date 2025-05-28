from config import Config
from publish import Publish
from rest_http_client import RESTHTTPClient
from subscribe import Subscribe

config = Config().from_path(path="config.yaml")
rest_http_client = RESTHTTPClient(config=config)
Subscribe(config=config, rest_http_client=rest_http_client).run()
Publish(config=config, rest_http_client=rest_http_client).run()
