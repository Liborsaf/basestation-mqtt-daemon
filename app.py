from loguru import logger

from mqtt import MQTTCredentials, MQTTService
from basestations import BasestationsService


class Application:
	def __init__(self):
		self.mqtt = None
		self.basestations = None

	def load(self) -> bool:
		logger.debug("Loading app...")

		credentials = MQTTCredentials.load()

		if not credentials.check():
			logger.error("Failed to load MQTT credentials, please check your environment variables.")

			return False

		self.mqtt = MQTTService()

		if not self.mqtt.connect(credentials):
			logger.error(f"Please check your environment variables.")

			return False

		self.basestations = BasestationsService()

		if not self.basestations.load():
			logger.warning("No devices loaded, scanning...")

			if not self.basestations.discover():
				return False

			self.basestations.test_all()

			self.basestations.save()

		return True

	def run(self):
		while self.mqtt.is_connected():
			pass

	def cleanup(self):
		pass
