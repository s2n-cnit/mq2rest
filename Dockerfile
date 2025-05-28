FROM python:3.13.2-bullseye

RUN pip install poetry

RUN mkdir ./mq2rest
WORKDIR /mq2rest

COPY ./ ./

RUN rm -rf test

RUN poetry install --no-root

ENV ID_DEVICE=${ID_DEVICE}
ENV MQTT_HOST=${MQTT_HOST}
ENV MQTT_PORT=${MQTT_PORT}
ENV MQTT_USERNAME=${MQTT_USERNAME}
ENV MQTT_PASSWORD=${MQTT_PASSWORD}
ENV VO_URL=${VO_URL}

CMD ["poetry", "run", "python", "main.py"]
