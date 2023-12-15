from __future__ import annotations

import os
import time

import json5
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from loguru import logger
# noinspection PyUnresolvedReferences
from basestation import BasestationScanner, BasestationDevice
# noinspection PyUnresolvedReferences
from bluepy.btle import BTLEDisconnectError

BASESTATIONS_FILE = "basestations.json5"


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


class Basestation:
	def __init__(self, device: BasestationDevice):
		self.device = device
		self.unreachable = True
		self.last_state = False  # Unknown in this phase

	def test(self):
		logger.info(f"Testing connection to basestation, mac: {self.device.mac}")

		try:
			self.device.connect()

			self.unreachable = False
			self.last_state = self.device.is_turned_on()

			logger.success(f"Connection successful, state: {self.last_state}")
		except BTLEDisconnectError as error:
			self.unreachable = True

			logger.error(f"Connection failed, reason: {error}")

		self.device.disconnect()


def main():
	load_dotenv()

	try:
		run()
	except KeyboardInterrupt:
		cleanup()


def run():
	credentials = MQTTCredentials.load()

	if not credentials.check():
		logger.error("Failed to load credentials, please check your environment variables.")

		return

	client = connect_mqtt(credentials)

	if not client or not client.is_connected():
		return

	basestations = load_basestations()

	if not basestations:
		logger.warning("No devices loaded, scanning...")

		basestations = discover_basestations()

		if not basestations:
			logger.error("No devices found nearby, try restarting your basestations.")

			return

		save_basestations(basestations)

	test_basestations(basestations)

	while client.is_connected():
		pass


def connect_mqtt(credentials: MQTTCredentials) -> mqtt.Client | None:
	client = mqtt.Client()
	client.on_connect = on_mqtt_connect
	client.on_publish = on_mqtt_publish

	client.will_set(f"{credentials.topic}/$announce", payload="{}", retain=True)

	logger.info(f"Connecting to MQTT, server: {credentials.hostname}")

	if credentials.is_auth():
		client.username_pw_set(credentials.username, credentials.password)

	try:
		client.connect(credentials.hostname, port=credentials.port, keepalive=60)
	except:
		logger.error("Failed to connect to MQTT, please check your environment variables.")

		return None
	else:
		client.loop_start()

		time.sleep(2)

		client.publish(f"{credentials.topic}/connected", payload="1", retain=True)

	return client


def on_mqtt_connect(client, userdata, flags, rc):
	if rc:
		logger.error(f"Failed to connect to MQTT, reason: {mqtt.connack_string(rc)}")
		exit(1)

	logger.success("MQTT Connected!")


def on_mqtt_publish(client, userdata, mid):
	logger.debug("Data published.")


def load_basestations() -> list[Basestation]:
	if not os.path.exists(BASESTATIONS_FILE):
		return []

	with open(BASESTATIONS_FILE) as file:
		try:
			basestations = [Basestation(BasestationDevice(mac)) for mac in json5.load(file)]
		except ValueError:
			basestations = []

	logger.info(f"Loaded {len(basestations)} basestations!")

	return basestations


def discover_basestations() -> list[Basestation]:
	scanner = BasestationScanner()

	try:
		devices = scanner.discover()
	except BTLEDisconnectError as error:
		logger.warning(f"Some device refused connection while discovering, reason: {error}")

	return [Basestation(device) for device in devices]


def save_basestations(basestations: list[Basestation]):
	logger.info(f"Saving {len(basestations)} basestations...")

	with open(BASESTATIONS_FILE, "w") as file:
		json5.dump([basestation.device.mac for basestation in basestations], file)


def test_basestations(basestations: list[Basestation]):
	for basestation in basestations:
		basestation.test()


def cleanup():
	pass


if __name__ == "__main__":
	main()
