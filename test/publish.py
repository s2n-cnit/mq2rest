import json

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "mq2rest-test-publish", protocol=mqtt.MQTTv5)
client.connect("localhost", 1883)

properties = Properties(PacketTypes.PUBLISH)

properties.UserProperty = ("MessageId", "GainCommand")
data = {
    "Value": 10
}

client.publish('D0001/REMOTECLIENT_ROUTING_KEY', json.dumps(data), 1, properties=properties)
