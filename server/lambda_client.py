import json
import uuid
from counting_semaphore import CountingSemaphore
from state import State
from threading import Thread
import cloudpickle 
import base64 
import socket

from util import make_json_serializable, decode_and_deserialize

SERVER_IP = ("71.191.38.59",25565)

"""
Lambda Client
-------------

This is the version of the client code that I've been running within an AWS Lambda function.

I've updated it to keep it consistent with the changes we've been making.
"""

def send_object(obj, websocket):
    """
    Send obj to a remote entity via the given websocket.
    The TCP server uses a different API (streaming via file handles), so it's implemented differently. 
    This different API is in tcp_server.py.    

    Arguments:
    ----------
        obj (bytes):
            The object to be sent. Should already be serialized via cloudpickle.dumps().
        
        websocket (socket.socket):
            Socket connected to a remote client.
    """
    # First, we send the number of bytes that we're going to send.
    websocket.sendall(len(obj).to_bytes(2, byteorder='big'))
    # Next, we send the serialized object itself. 
    websocket.sendall(obj)

def recv_object(websocket):
    """
    Receive an object from a remote entity via the given websocket.

    This is used by clients. There's another recv_object() function in TCP server.
    The TCP server uses a different API (streaming via file handles), so it's implemented differently. 
    This different API is in tcp_server.py.

    Arguments:
    ----------
        websocket (socket.socket):
            Socket connected to a remote client.    
    """
    # First, we receive the number of bytes of the incoming serialized object.
    incoming_size = websocket.recv(2)
    # Convert the bytes representing the size of the incoming serialized object to an integer.
    incoming_size = int.from_bytes(incoming_size, 'big')
    print("Will receive another message of size %d bytes" % incoming_size)
    # Finally, we read the serialized object itself.
    return websocket.recv(incoming_size).strip()

def client_task(taskID, function_name):
    state = State(ID = function_name, pc = taskID)
    websocket = socket.socket()
    websocket.connect(SERVER_IP)
    msg_id = str(uuid.uuid4())
    print(taskID + " calling synchronize PC: " + str(state._ID) + ". Message ID=" +msg_id)

    message = {
        "op": "synchronize_async", 
        "name": "b", 
        "method_name": "wait_b", 
        "state": base64.b64encode(cloudpickle.dumps(state)).decode('utf-8'), 
        "keyword_arguments": {"ID": taskID},
        "id": msg_id
    }
    print("Calling 'synchronize' on the server.")
    msg = json.dumps(message).encode('utf-8')
    send_object(msg)
    print(taskID + " called synchronize PC: " + str(state._ID))

    data = recv_object(websocket)               # Should just be a serialized state object.
    state_from_server = cloudpickle.loads(data) # `state_from_server` is of type State

def client_main(context):
    function_name = context.function_name
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as websocket:
        print("Connecting to " + str(SERVER_IP))
        websocket.connect(SERVER_IP)
        print("Succcessfully connected!")
        msg_id = str(uuid.uuid4())

        print("Sending 'create' message to server. Message ID=" + msg_id)

        message = {
            "op": "create", 
            "type": "Barrier", 
            "name": "b", 
            "function_name": function_name,
            "keyword_arguments": {"n": 2},
            "id": msg_id
        }
        
        msg = json.dumps(message).encode('utf-8')
        send_object(msg)
        
        print("Sent 'create' message to server")

        # Receive data. This should just be an ACK, as the TCP server will 'ACK' our create() calls.
        ack = recv_object()

        try:
            print("Starting client thread1")
            t1 = Thread(target=client_task, args=(str(1),function_name,), daemon=True)
            t1.start()
        except Exception as ex:
            print("[ERROR] Failed to start client thread1.")
            print(ex)

        t1.join()

        try:
            print("Starting client thread2")
            t2 = Thread(target=client_task, args=(str(2), function_name,), daemon=True)
            t2.start()
        except Exception as ex:
            print("[ERROR] Failed to start client thread2.")
            print(ex)
        
        t2.join()

def old_handler():
    uri = "PYRO:obj_6addf78ee967485c8f76ff0ef3d0172f@71.191.38.59:25565"
    name = "Ben"
    
    try:
        greeting_maker = Pyro4.Proxy(uri)   # get a Pyro proxy to the greeting object
    except Exception as ex:
        print("Got exception as ex: " + str(ex))
    
    print("Got proxy")
    
    fortune = greeting_maker.get_fortune(name)
    
    print(fortune)   # call method normally
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps(fortune)
    }

def lambda_handler(event, context):
    client_main(context)
    return {
        'statusCode': 200,
        'body': json.dumps("Hello, world!")
    }
