import asyncio
from multiprocessing import synchronize
from re import A
import ujson
import websockets
import cloudpickle 
import _thread
import base64 
import threading
import socket

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

class ServerThread(threading.Thread):
    def __init__(self, ip, port, client_socket):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.client_socket = client_socket 
        logger.info("Starting new thread for " + str(ip) + ":" + str(port))

    def _get_synchronizer_name(self, obj_type = None, name = None):
        """
        Return the key of a synchronizer object. 

        The key is a string of the form <type>-<name>.
        """
        #return "{0}-{1}".format(obj_type, name)
        return str(name) 

    def create(self, message = None):
        logger.debug("server.create() called.")
        type_arg = message["type"]
        name = message["name"]

        synchronizer = Synchronizer()

        if "keyword_arguments" in message:
            keyword_arguments = message["keyword_arguments"]
            synchronizer.create(type_arg, name, **keyword_arguments)
        else:
            n = message["n"]
            keyword_arguments = {"n": n}
            synchronizer.create(type_arg, name, keyword_arguments)
        
        synchronizer_name = self._get_synchronizer_name(obj_type = type_arg, name = name)
        self.synchronizers[synchronizer_name] = synchronizer # Store Synchronizer object.

    def setup(self, message = None):
        logger.debug("server.setup() called.")
        pass 
    
    def synchronize(self, message = None):
        logger.debug("server.synchronize() called.")
        obj_name = message['name']
        method_name = message['method_name']
        state = cloudpickle.loads(base64.b64decode(message['state'])) 

        synchronizer_name = self._get_synchronizer_name(obj_type = None, name = obj_name)
        synchronizer = self.synchronizers[synchronizer_name]
        
        if "keyword_arguments" in message:
            keyword_arguments = message["keyword_arguments"]
            synchronizer.synchronize(method_name, state, **keyword_arguments)
        else:
            synchronizer.synchronize(method_name, state)

    def run(self):
        while True:
            data = self.client_socket.recv(2048) 
            json_message = ujson.loads(data)
            action = json_message.get("op", None)
            self.action_handlers[action](message = json_message)

class TcpServer(socket.socket):
    def __init__(self):
        socket.socket.__init__(self)
        self.action_handlers = {
            "create": self.create,
            "setup": self.setup,
            "synchronize": self.synchronize
        }
        self.synchronizers = dict() 
        self.bind(('0.0.0.0', 25565))
        self.listen(5)
        self.server_threads = []
    
    def run(self):
        print("Starting server...")
        try:
            self.server_loop()
        except Exception as ex:
            logger.error(ex)
        finally:
            for client in self.clients:
                client.close()
            self.close()

    def server_loop(self):
        while True:
            (client_socket, (address,port)) = self.accept()

            self.clients.append(client_socket)

            self.onopen(client_socket)

            server_thread = ServerThread(address, port, client_socket)
            self.server_threads.append(server_thread)
            server_thread.start()

    def start(self):
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logger.info("==========================")
        logger.info("Started Python Coordinator")
        logger.info("==========================")

if __name__ == "__main__":
    tcp_server = TcpServer()
    print("Starting TCP server")
    tcp_server.start()