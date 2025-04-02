from bridge import Bridge
from config import Config

config = Config(path="config.yaml")
bridge = Bridge(config=Config)
bridge.publish()
bridge.subscribe()
