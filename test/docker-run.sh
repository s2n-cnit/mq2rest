#!/bin/bash

docker run -e MQTT_PORT=1883 -e MQTT_HOST=172.19.2.7 -e VO_URL=http://172.19.2.7:5555 -e MQTT_USERNAME=x -e MQTT_PASSWORD=x -e ID_DEVICE=D0001 -it mq2rest:latest
