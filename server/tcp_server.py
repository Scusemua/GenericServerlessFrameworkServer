import asyncio
from multiprocessing import synchronize
from re import A
import ujson
import websockets

from base_server import BaseServer
from synchronizer import Synchronizer

# Set up logging.
import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger.addHandler(ch)

class TcpServer(BaseServer):
    def __init__(self):
        self.action_handlers = {
            "create": self.create,
            "setup": self.setup,
            "synchronize": self.synchronize
        }
        self.synchronizers = dict() 
        pass

    def start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.server = websockets.serve(self.server_loop, "0.0.0.0", self.port)
        logger.info("==========================")
        logger.info("Started Python Coordinator")
        logger.info("==========================")
        # print_incomplete_pairing_names = asyncio.get_event_loop().create_task(printIncomplete())
        self.loop.run_until_complete(self.server)
        self.loop.run_forever()
    
    def _get_synchronizer_name(self, obj_type = None, name = None):
        """
        Return the key of a synchronizer object. 

        The key is a string of the form <type>-<name>.
        """
        #return "{0}-{1}".format(obj_type, name)
        return str(name) 

    async def create(self, message = None):
        logger.debug("server.create() called.")
        type_arg = message["type"]
        name = message["name"]

        synchronizer = Synchronizer(type_arg = type_arg, name = name)
        synchronizer_name = self._get_synchronizer_name(obj_type = type_arg, name = name)
        self.synchronizers[synchronizer_name] = synchronizer # Store Synchronizer object.

    async def setup(self, message = None):
        logger.debug("server.setup() called.")
        pass 
    
    async def synchronize(self, message = None):
        logger.debug("server.synchronize() called.")
        obj_name = message['name']
        method_name = message['method_name']
        state = message['state']

        synchronizer_name = self._get_synchronizer_name(obj_type = None, obj_name = obj_name)
        synchronizer = self.synchronizers[synchronizer_name].synchronize(method_name = method_name)

    async def server_loop(self, websocket, path):
        """
            This is the main server loop for the NAT Punching coordinator.

            The coordinator listens for pairing names and caches the associated websocket. When it receives another message
            with the same pairing name, the coordinator will send the IP addresses to each remote server.
        """
        while True:
            try:
                # Listen for pairing names.
                msg_json = await websocket.recv() # TODO: Possibly needs its own thread to handle this.

                message = ujson.loads(msg_json)

                action = message.get("operation", None)

                await self.action_handlers[action](websocket = websocket, message = message)
            except websockets.ConnectionClosed:
                break