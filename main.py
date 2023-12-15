from dotenv import load_dotenv
from loguru import logger

import app


def main():
	logger.debug("Loading env...")
	load_dotenv()

	logger.debug("Loading app...")
	try:
		app.run()
	except KeyboardInterrupt:
		app.cleanup()


if __name__ == "__main__":
	main()
