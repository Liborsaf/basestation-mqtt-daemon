from loguru import logger

from mqtt import MQTTCredentials, MQTTService
from basestations import BasestationsService

# TODO: Move all this to class


def run():
	credentials = MQTTCredentials.load()

	if not credentials.check():
		logger.error("Failed to load credentials, please check your environment variables.")

		return

	mqtt = MQTTService()
	mqtt.connect(credentials)

	if not mqtt.is_connected():
		return

	basestations = BasestationsService()

	if not basestations.load():
		logger.warning("No devices loaded, scanning...")

		if not basestations.discover():
			return

		basestations.test_all()

		basestations.save()

	while mqtt.is_connected():
		pass


def cleanup():
	pass
