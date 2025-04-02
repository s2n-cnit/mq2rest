import json
import time

import paho.mqtt.client as mqtt
import requests


# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    """Callback when the MQTT client connects to the broker."""
    if rc == 0:
        print(f"Connected to MQTT Broker at {MQTT_BROKER_ADDRESS}:{MQTT_BROKER_PORT}")
        client.subscribe(MQTT_TOPIC_SUBSCRIBE)
        print(f"Subscribed to topic: {MQTT_TOPIC_SUBSCRIBE}")
    else:
        print(f"Failed to connect to MQTT Broker with result code {rc}")

def on_disconnect(client, userdata, rc):
    """Callback when the MQTT client disconnects from the broker."""
    print("Disconnected from MQTT Broker")

def on_message(client, userdata, msg):
    """Callback when a message is received on a subscribed topic."""
    try:
        payload = msg.payload.decode()
        print(f"Received message on topic '{msg.topic}': {payload}")
        # Process the received MQTT message here
        # You might want to interact with the HTTP API based on this message
        # Example:
        # if msg.topic == MQTT_TOPIC_SUBSCRIBE and "trigger_http_get" in payload:
        #     http_get_data()
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def on_publish(client, userdata, mid):
    """Callback when a message is published to the broker."""
    print(f"Message published [MID: {mid}] to topic: {MQTT_TOPIC_PUBLISH}")

# --- HTTP Functions ---
def http_get_data():
    """Performs an HTTP GET request to the configured API endpoint."""
    try:
        url = HTTP_BASE_URL + HTTP_ENDPOINT
        response = requests.get(url, headers=HTTP_HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        print(f"HTTP GET Response from {url}:")
        print(json.dumps(data, indent=4))
        # You might want to publish this data to MQTT
        # mqtt_publish_data(MQTT_TOPIC_PUBLISH, data)
    except requests.exceptions.RequestException as e:
        print(f"HTTP GET request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")

def http_post_data(payload):
    """Performs an HTTP POST request to the configured API endpoint."""
    try:
        url = HTTP_BASE_URL + HTTP_ENDPOINT
        response = requests.post(url, headers=HTTP_HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"HTTP POST Response from {url}:")
        print(json.dumps(data, indent=4))
        # You might want to publish the response to MQTT
        # mqtt_publish_data(MQTT_TOPIC_PUBLISH, data)
    except requests.exceptions.RequestException as e:
        print(f"HTTP POST request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")

def http_put_data(payload):
    """Performs an HTTP PUT request to the configured API endpoint."""
    try:
        url = HTTP_BASE_URL + HTTP_ENDPOINT
        response = requests.put(url, headers=HTTP_HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"HTTP PUT Response from {url}:")
        print(json.dumps(data, indent=4))
        # You might want to publish the response to MQTT
        # mqtt_publish_data(MQTT_TOPIC_PUBLISH, data)
    except requests.exceptions.RequestException as e:
        print(f"HTTP PUT request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")

def http_delete_data():
    """Performs an HTTP DELETE request to the configured API endpoint."""
    try:
        url = HTTP_BASE_URL + HTTP_ENDPOINT
        response = requests.delete(url, headers=HTTP_HEADERS)
        response.raise_for_status()
        print(f"HTTP DELETE request to {url} successful.")
        # You might want to publish a confirmation to MQTT
        # mqtt_publish_data(MQTT_TOPIC_PUBLISH, {"message": "HTTP DELETE successful"})
    except requests.exceptions.RequestException as e:
        print(f"HTTP DELETE request failed: {e}")

# --- MQTT Functions ---
def mqtt_connect():
    """Connects to the MQTT broker."""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.connect(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, 60)  # Keepalive = 60 seconds
    return client

def mqtt_publish_data(topic, payload):
    """Publishes data to the specified MQTT topic."""
    try:
        if isinstance(payload, dict):
            payload_str = json.dumps(payload)
        elif not isinstance(payload, str):
            payload_str = str(payload)
        else:
            payload_str = payload
        result = mqtt_client.publish(topic, payload_str)
        status = result[0]
        if status == 0:
            print(f"Published '{payload_str}' to topic '{topic}'")
        else:
            print(f"Failed to publish to topic '{topic}': error code {status}")
    except Exception as e:
        print(f"Error publishing to MQTT: {e}")

# --- Main Program ---
if __name__ == "__main__":
    # Initialize MQTT client
    mqtt_client = mqtt_connect()
    mqtt_client.loop_start()  # Start the MQTT network loop in a separate thread

    try:
        while True:
            print("\n--- Actions ---")
            print("1. Perform HTTP GET")
            print("2. Perform HTTP POST (enter JSON payload)")
            print("3. Perform HTTP PUT (enter JSON payload)")
            print("4. Perform HTTP DELETE")
            print("5. Publish MQTT message (enter topic and payload)")
            print("6. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                http_get_data()
            elif choice == '2':
                try:
                    payload_str = input("Enter JSON payload for POST: ")
                    payload = json.loads(payload_str)
                    http_post_data(payload)
                except json.JSONDecodeError:
                    print("Invalid JSON payload.")
            elif choice == '3':
                try:
                    payload_str = input("Enter JSON payload for PUT: ")
                    payload = json.loads(payload_str)
                    http_put_data(payload)
                except json.JSONDecodeError:
                    print("Invalid JSON payload.")
            elif choice == '4':
                http_delete_data()
            elif choice == '5':
                publish_topic = input(f"Enter MQTT topic to publish to (default: {MQTT_TOPIC_PUBLISH}): ") or MQTT_TOPIC_PUBLISH
                publish_payload = input("Enter MQTT payload to publish: ")
                mqtt_publish_data(publish_topic, publish_payload)
            elif choice == '6':
                break
            else:
                print("Invalid choice. Please try again.")

            time.sleep(1)  # Small delay for user interaction

    except KeyboardInterrupt:
        print("\nExiting program.")
    finally:
        mqtt_client.loop_stop()  # Stop the MQTT network loop
        mqtt_client.disconnect()
