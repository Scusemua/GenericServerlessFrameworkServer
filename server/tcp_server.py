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
from util import make_json_serializable, decode_and_deserialize

# Set up logging.
import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger.addHandler(ch)

def isTry_and_getMethodName(name):
    if name.startswith("try_"):
        return name[4:], True
    return name, False

class TCPHandler(socketserver.StreamRequestHandler):
    # def __init__(self, request, client_address, server):
    #     super().__init__(request, client_address, server)
    #     logger.info("Created TCPHandler")

    def handle(self):
        logger.info("Recieved one request from {}".format(self.client_address[0]))

        self.action_handlers = {
            "create": self.create_obj,
            "setup": self.setup_server,
            "synchronize_async": self.synchronize_async,
            "synchronize_sync": self.synchronize_sync
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

    def synchronize_sync(self, message = None):
        logger.debug("server.synchronize_async() called.")
        obj_name = message['name']
        method_name = message['method_name']
        state = decode_and_deserialize(message["state"])
        function_name = state.id

        synchronizer_name = self._get_synchronizer_name(obj_type = None, name = obj_name)
        logger.debug("Trying to retrieve existing Synchronizer '%s'" % synchronizer_name)
        synchronizer = tcp_server.synchronizers[synchronizer_name]

        base_name, isTryMethod = self.isTry_and_getMethodName(method_name)
    
        logger.debug("method_name: " + method_name)
        logger.debug("base_name: " + base_name)
        logger.debug("isTryMethod: " + str(isTryMethod))    
        
        try:
            _synchronizer_method = getattr(self._synchClass,method_name)
        except Exception as x:
            logger.debug("Caught Error >>> %s" % x)

        if isTryMethod: 
            # check if synchronize op will block, if yes tell client to terminate then call op
            # rhc: FIX THIS here and in CREATE: let 
            return_value =  synchronizer.trySynchronize(method_name, **state.keyword_arguments)
        
            if return_value == True:   # synchronize op will execute wait so tell client to terminate
                self.wfile.write(cloudpickle.dumps([True, None]))
                
                # execute synchronize op but don't send result to client
                return_value = synchronizer.synchronize(base_name, state, function_name, **state.keyword_arguments)
            else:
                # execute synchronize op but don't send result to client
                return_value = synchronizer.synchronize(base_name, state, function_name, **state.keyword_arguments)
        else:  # not a "try" so do synchronization op and send result to waiting client
            # rhc: FIX THIS here and in CREATE
            return_value = synchronizer.synchronize(method_name, state, function_name, **state.keyword_arguments)
                
            state.return_value = return_value
            # send tuple to be consistent, and False to be consistent, i.e., get result if False
            self.wfile.write(cloudpickle.dumps([False, state]))

    def create_obj(self, message = None):
        logger.debug("server.create() called.")
        type_arg = message["type"]
        name = message["name"]
        state = decode_and_deserialize(message["state"])

        synchronizer = Synchronizer()

        synchronizer.create(type_arg, name, **state.keyword_arguments)
        
        synchronizer_name = self._get_synchronizer_name(obj_type = type_arg, name = name)
        logger.debug("Caching new Synchronizer with name '%s'" % synchronizer_name)
        tcp_server.synchronizers[synchronizer_name] = synchronizer # Store Synchronizer object.

        resp = {
            "op": "ack",
            "op_performed": "create"
        }
        #############################
        # Write ACK back to client. #
        #############################
        logger.info("Sending ACK to client %s for CREATE operation." % self.client_address[0])
        self.wfile.write(ujson.dumps(resp).encode('utf-8'))
        logger.info("Sent ACK to client %s for CREATE operation." % self.client_address[0])

    def setup_server(self, message = None):
        logger.debug("server.setup() called.")
        pass 
    
    def synchronize_async(self, message = None):
        logger.debug("server.synchronize_async() called.")
        obj_name = message['name']
        method_name = message['method_name']
        state = decode_and_deserialize(message["state"])
        function_name = state.id

        synchronizer_name = self._get_synchronizer_name(obj_type = None, name = obj_name)
        logger.debug("Trying to retrieve existing Synchronizer '%s'" % synchronizer_name)
        synchronizer = tcp_server.synchronizers[synchronizer_name]
        
        if (synchronizer is None):
            raise ValueError("Could not find existing Synchronizer with name '%s'" % synchronizer_name)
        
        logger.debug("Successfully found synchronizer")
        
        sync_ret_val = synchronizer.synchronize(method_name, state, function_name, **state.keyword_arguments)
        
        logger.debug("Synchronize returned: %s" % str(sync_ret_val))
            

class TCPServer(object):
    def __init__(self):
        self.synchronizers = dict() 
        self.server_threads = []
        self.clients = []
        self.server_address = ("0.0.0.0",25565)
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