import logging

LOG=logging.getLogger(__name__)

def debug_on():
	formatter = logging.Formatter("%(asctime)s - %(name)s (%(process)d) - %(levelname)s - %(message)s")
	screen_handler=logging.StreamHandler()
	screen_handler.setFormatter(formatter)
	screen_handler.setLevel(logging.DEBUG)
	LOG.addHandler(screen_handler)
	LOG.setLevel(logging.DEBUG)
