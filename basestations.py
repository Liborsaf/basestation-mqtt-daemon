import os

import json5
from loguru import logger
# noinspection PyUnresolvedReferences
from basestation import BasestationScanner, BasestationDevice
# noinspection PyUnresolvedReferences
from bluepy.btle import BTLEDisconnectError

BASESTATIONS_FILE = "basestations.json5"


class Basestation:
	def __init__(self, device: BasestationDevice, unreachable=True, last_state=False):
		self.device = device
		self.unreachable = unreachable
		self.last_state = last_state
		# self.last_test = 0

	def connect(self) -> bool:
		try:
			self.device.connect()

			self.unreachable = False

			return True
		except BTLEDisconnectError as error:
			self.unreachable = True

			logger.error(f"Connection failed, reason: {error}")
		# finally:
		#   self.device.disconnect()

		return False

	def disconnect(self):
		self.device.disconnect()

	def is_turned_on(self) -> bool:
		return self.device.is_turned_on()

	def test(self) -> bool:
		logger.info(f"Testing connection to basestation, mac: {self.device.mac}")

		if self.connect():
			self.last_state = self.is_turned_on()

			logger.success(f"Connection successful, state: {self.last_state}")

			self.disconnect()

			return True

		return False

	def dump(self):
		return {
			'mac': self.device.mac,
			'unreachable': self.unreachable,
			'last_state': self.last_state
		}


class BasestationsService:
	def __init__(self):
		self.scanner = BasestationScanner()
		self.basestations = []

	def load(self) -> bool:
		if not os.path.exists(BASESTATIONS_FILE):
			return False

		with open(BASESTATIONS_FILE) as file:
			try:
				self.basestations = [Basestation(BasestationDevice(data['mac']), data['unreachable'], data['last_state']) for data in json5.load(file)]
			except ValueError as error:
				logger.error(f"Failed to load basestation, reason: {error}")

		logger.info(f"Loaded {len(self.basestations)} basestations!")

		return True

	def discover(self) -> bool:
		logger.info("Discovering basestations...")

		devices = []

		try:
			devices = self.scanner.discover()
		except BTLEDisconnectError as error:
			logger.warning(f"Some device refused connection while discovering, reason: {error}")

			# return False

		if not devices:
			logger.error("No devices found nearby, try restarting your basestations.")

			return False

		self.basestations = [Basestation(device) for device in devices]

		logger.success(f"Found {len(self.basestations)} basestations!")

		return True

	def save(self):
		logger.info(f"Saving {len(self.basestations)} basestations...")

		with open(BASESTATIONS_FILE, "w") as file:
			json5.dump([basestation.dump() for basestation in self.basestations], file)

		logger.success("Save successful!")

	def test_all(self):
		for basestation in self.basestations:
			basestation.test()