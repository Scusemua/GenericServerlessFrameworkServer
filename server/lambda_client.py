import json
import uuid
from counting_semaphore import CountingSemaphore
from state import State
from threading import Thread
import cloudpickle 
import base64 
import socket

SERVER_IP = ("71.191.38.59",25565)

def client_task(taskID, function_name):
    state = State()
    state._ID = taskID
    state._pc = taskID
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
        "function_name": function_name,
        "id": msg_id
    }
    print("Calling 'synchronize' on the server.")
    msg = json.dumps(message).encode('utf-8')
    websocket.sendall(len(msg).to_bytes(2, byteorder='big'))
    websocket.sendall(msg)
    print(taskID + " called synchronize PC: " + str(state._ID))

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
        websocket.sendall(len(msg).to_bytes(2, byteorder='big'))
        websocket.sendall(msg)
        
        print("Sent 'create' message to server")

        # Receive data from the server and shut down
        received = str(websocket.recv(1024), "utf-8")

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
