import os

import json5
# noinspection PyUnresolvedReferences
from basestation import BasestationScanner, BasestationDevice

BASESTATIONS_FILE = "basestations.json5"


def main():
	devices = []

	if os.path.exists(BASESTATIONS_FILE):
		with open(BASESTATIONS_FILE) as file:
			try:
				devices = [BasestationDevice(mac) for mac in json5.load(file)]
			except ValueError:
				pass

	if not devices:
		print("No devices loaded, scanning...")
		scanner = BasestationScanner()
		devices = scanner.discover()

		if not devices:
			print("No devices found nearby!")

			return

		with open(BASESTATIONS_FILE, "w") as file:
			json5.dump([device.mac for device in devices], file)
	else:
		print("Devices loaded!")

	for device in devices:
		device.connect()
		device.turn_on()
		device.disconnect()


if __name__ == "__main__":
	main()
