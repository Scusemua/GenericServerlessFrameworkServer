import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger.addHandler(ch)

class Synchronizer(object):
    def __init__(self, type = None, name = None):
        self.type = type
        self.name = name
    
    def synchronize(self, method_name = None):
        logger.debug("Synchronizer.synchronize() called. method_name=%s" % method_name)