import asyncio
from multiprocessing import synchronize
from re import A
import ujson
import websockets
import cloudpickle 
import _thread
import base64 
import threading
import traceback
import sys
import socket
import socketserver
import threading

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

class TCPHandler(socketserver.StreamRequestHandler):
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
        print("Recieved one request from {}".format(self.client_address[0]))

        msg = self.rfile.readline().strip()

        print("Data Recieved from client is:".format(msg))

        print(msg)  

        print("Thread Name:{}".format(threading.current_thread().name))

class TCPServer(object):
    def __init__(self):
        self.synchronizers = dict() 
        self.server_threads = []
        self.clients = []
        self.server_address = ("127.0.0.1",25565)
        self.tcp_server = socketserver.ThreadingTCPServer(self.server_address, TCPHandler)
    
    def start(self):
        logger.info("Starting TCP server.")
        try:
            self.tcp_server.serve_forever()
        except Exception as ex:
            logger.error("Exception encountered:" + repr(ex))

if __name__ == "__main__":
    # Create a Server Instance
    tcp_server = TCPServer()
    tcp_server.start()