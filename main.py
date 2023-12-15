from dotenv import load_dotenv
from loguru import logger

from app import Application


def main():
	logger.debug("Loading env...")
	load_dotenv()

	app = Application()

	if not app.load():
		logger.error("Failed to load app!")

		return

	try:
		app.run()
	except KeyboardInterrupt:
		pass

	app.cleanup()


if __name__ == "__main__":
	main()
