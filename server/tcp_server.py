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
    # def __init__(self, request, client_address, server):
    #     super().__init__(request, client_address, server)
    #     logger.info("Created TCPHandler")

    def handle(self):
        logger.info("Recieved one request from {}".format(self.client_address[0]))

        self.action_handlers = {
            "create": self.create_obj,
            "setup": self.setup_server,
            "synchronize": self.synchronize
        }
        logger.info("Thread Name:{}".format(threading.current_thread().name))

        try:
            incoming_size = self.rfile.read(2)
            incoming_size = int.from_bytes(incoming_size, 'big')
            logger.info("Will receive another message of size %d bytes" % incoming_size)
            data = self.rfile.read(incoming_size).strip()
            #logger.info("Received %d bytes from client: %s" % (len(data), str(data)))
            json_message = ujson.loads(data)
            message_id = json_message["id"]
            logger.debug("Received message (size=%d bytes) from client %s with ID=%s" % (len(data), self.client_address[0], message_id))
            action = json_message.get("op", None)
            resp = {
                "op": "ack"
            }
            self.action_handlers[action](message = json_message)
            logger.info("Writing response back to client %s" % self.client_address[0])
            self.wfile.write(ujson.dumps(resp).encode('utf-8'))            
            logger.info("Wrote response back to client %s" % self.client_address[0])
        except Exception as ex:
            logger.error(ex)
            logger.error(traceback.format_exc())

    def _get_synchronizer_name(self, obj_type = None, name = None):
        """
        Return the key of a synchronizer object. 

        The key is a string of the form <type>-<name>.
        """
        #return "{0}-{1}".format(obj_type, name)
        return str(name) 

    def create_obj(self, message = None):
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
        logger.debug("Caching new Synchronizer with name '%s'" % synchronizer_name)
        tcp_server.synchronizers[synchronizer_name] = synchronizer # Store Synchronizer object.

        resp = {
            "op": "ack",
            "op_performed": "create"
        }
        self.wfile.write(ujson.dumps(resp).encode('utf-8'))

    def setup_server(self, message = None):
        logger.debug("server.setup() called.")
        pass 
    
    def synchronize(self, message = None):
        logger.debug("server.synchronize() called.")
        obj_name = message['name']
        method_name = message['method_name']
        state = cloudpickle.loads(base64.b64decode(message['state'])) 

        synchronizer_name = self._get_synchronizer_name(obj_type = None, name = obj_name)
        logger.debug("Trying to retrieve existing Synchronizer '%s'" % synchronizer_name)
        synchronizer = tcp_server.synchronizers[synchronizer_name]
        
        if (synchronizer is None):
            raise ValueError("Could not find existing Synchronizer with name '%s'" % synchronizer_name)
        
        logger.debug("Successfully found synchronizer")
        
        if "keyword_arguments" in message:
            keyword_arguments = message["keyword_arguments"]
            synchronizer.synchronize(method_name, state, **keyword_arguments)
        else:
            synchronizer.synchronize(method_name, state)
            

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