import ujson
import uuid
from counting_semaphore import CountingSemaphore
from state import State
from threading import Thread
import cloudpickle 
import base64 
import socket

from util import make_json_serializable, decode_and_deserialize

SERVER_IP = "ws://localhost:25565"

def client_task(taskID):
    state = State(pc = taskID, ID="local", restart = False, keyword_arguments = {"ID": taskID})
    websocket = socket.socket()
    websocket.connect(("127.0.0.1", 25565))
    msg_id = str(uuid.uuid4())
    print(taskID + " calling synchronize PC: " + str(state._ID) + ". Message ID=" +msg_id)

    message = {
        "op": "synchronize_async", 
        "name": "b", 
        "method_name": "wait_b", 
        "state": make_json_serializable(state),
        "id": msg_id
    }
    print("Calling 'synchronize' on the server.")
    msg = ujson.dumps(message).encode('utf-8')
    websocket.sendall(len(msg).to_bytes(2, byteorder='big'))
    websocket.sendall(msg)
    print(taskID + " called synchronize PC: " + str(state._ID))

def client_main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as websocket:
        websocket.connect(("127.0.0.1", 25565))
        msg_id = str(uuid.uuid4())
        state = State(ID = "local", restart = False, keyword_arguments = {"n": 2})
        print("Sending 'create' message to server. Message ID=" + msg_id)

        message = {
            "op": "create", 
            "type": "Barrier", 
            "name": "b", 
            "state": make_json_serializable(state),
            "id": msg_id
        }
        
        msg = ujson.dumps(message).encode('utf-8')
        websocket.sendall(len(msg).to_bytes(2, byteorder='big'))
        websocket.sendall(msg)
        
        print("Sent 'create' message to server")

        # Receive data from the server and shut down
        received = str(websocket.recv(1024), "utf-8")

        try:
            print("Starting client thread1")
            t1 = Thread(target=client_task, args=(str(1),), daemon=True)
            t1.start()
        except Exception as ex:
            print("[ERROR] Failed to start client thread1.")
            print(ex)

        t1.join()

        try:
            print("Starting client thread2")
            t2 = Thread(target=client_task, args=(str(2),), daemon=True)
            t2.start()
        except Exception as ex:
            print("[ERROR] Failed to start client thread2.")
            print(ex)
        
        t2.join()

if __name__ == "__main__":
    client_main()
    
"""
Changes:
1. Above CP send synchronize pass kwargs parm [ID = taskID]
2. tcp loop action: create: change **keyword_arguments to keyword_arguments, I think
3. tcp loop action: synchronize: same kwargs logic as create()
4. method synchronize() in class Synchronizer:
    a. add state parm: def synchronize(self, method_name, state, **kwargs):
    b. get rid of:
        cb = kwargs["cb"]
        first = kwargs["first"]
    c. Change program_counter = kwargs["program_counter"] to
        program_counter = state._pc
        state.pc = 10
"""