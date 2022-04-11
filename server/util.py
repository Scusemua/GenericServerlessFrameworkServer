import cloudpickle 
import socketserver
import base64 

import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger.addHandler(ch)

def make_json_serializable(obj):
    """
    Serialize and encode an object.
    """
    return base64.b64encode(cloudpickle.dumps(obj)).decode('utf-8')

def decode_and_deserialize(obj):
    """
    Decode and deserialize an object.
    """
    return cloudpickle.loads(base64.b64decode(obj))

def send_object(obj, websocket):
    """
    Send obj to a remote entity via the given websocket.
    """
    websocket.sendall(len(obj).to_bytes(2, byteorder='big'))
    websocket.sendall(obj)

def recv_object(request_handler : socketserver.StreamRequestHandler):
    """
    Receive an object from a remote entity via the given websocket.
    """
    incoming_size = request_handler.rfile.read(2)
    incoming_size = int.from_bytes(incoming_size, 'big')
    logger.debug("Will receive another message of size %d bytes" % incoming_size)
    return request_handler.rfile.read(incoming_size).strip()