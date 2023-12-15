from __future__ import annotations

import os
import time

import paho.mqtt.client as mqtt
from loguru import logger


class MQTTCredentials:
	def __init__(self, hostname: str, port: int, username: str, password: str, topic: str):
		self.hostname = hostname
		self.port = port
		self.username = username
		self.password = password
		self.topic = topic

	@classmethod
	def load(cls) -> MQTTCredentials:
		return cls(os.environ.get("MQTT_HOSTNAME"),
		           os.environ.get("MQTT_PORT", 1883),
		           os.environ.get("MQTT_USERNAME"),
		           os.environ.get("MQTT_PASSWORD"),
		           os.environ.get("MQTT_TOPIC", "basestations"))

	def check(self) -> bool:
		if self.hostname and self.port and self.topic:
			return True

		return False

	def is_auth(self) -> bool:
		if self.username and self.password:
			return True

		return False


# noinspection PyMethodMayBeStatic
class MQTTService:
	def __init__(self):
		self.client = None
		self.topic = None

	def connect(self, credentials: MQTTCredentials) -> bool:
		self.topic = credentials.topic

		self.client = mqtt.Client()
		self.client.on_connect = self._on_connect
		self.client.on_publish = self._on_publish

		self.client.will_set(f"{self.topic}/$announce", payload="{}", retain=True)

		logger.info(f"Connecting to MQTT, server: {credentials.hostname}")

		if credentials.is_auth():
			self.client.username_pw_set(credentials.username, credentials.password)

		try:
			self.client.connect(credentials.hostname, port=credentials.port, keepalive=60)
		except ValueError as error:
			logger.error(f"Failed to connect to MQTT, reason: {error}")

			return False
		else:
			self.client.loop_start()

			time.sleep(1)

			self.publish("connected", payload="1", retain=True)

		return self.is_connected()

	def publish(self, path: str, payload: any, retain=True):
		self.client.publish(f"{self.topic}/{path}",
		                    payload=payload,
		                    retain=retain)

	# TODO: Missing typing
	def _on_connect(self, _client, _userdata, _flags, rc):
		if rc:
			logger.error(f"Failed to connect to MQTT, reason: {mqtt.connack_string(rc)}")
			exit(1)

		logger.success("MQTT Connected!")

	def _on_publish(self, _client, _userdata, _mid):
		logger.debug("Data published.")

	def is_connected(self):
		return self.client and self.client.is_connected()
