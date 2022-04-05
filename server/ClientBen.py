import sys
import _thread
import websockets 
import asyncio
import time
import ujson
from counting_semaphore import CountingSemaphore
from state import State

SERVER_IP = ""

if sys.version_info<(3,0):
    input = raw_input

def client_task_wrapper(taskID):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(client_task(taskID))

async def client_task(taskID):
    state = State()
    state._ID = taskID
    state._pc = taskID
    websocket = await websockets.connect(SERVER_IP)
    print(taskID + " calling synchronize PC: " + str(state._ID))

    message = {
        "op": "synchronize", 
        "name": "b", 
        "method_name": "wait_b", 
        "state": state, 
        "id": taskID
    }
    message_json = ujson.dumps(message)

    websocket.send(message_json)
    print(taskID + " called synchronize PC: " + str(state._ID))

async def client_main():
    websocket = await websockets.connect(SERVER_IP)

    print("Sending message to server...")

    message = {
        "op": "create", 
        "type": "Barrier", 
        "name": "b", 
        "n": 2
    }

    message_json = ujson.dumps(message)
    
    await websocket.send(message_json)
    
    print("Sent message to server")

    try:
        print("Starting client thread1")
        _thread.start_new_thread(client_task_wrapper, (str(1)))
    except Exception as ex:
        print("[ERROR] Failed to start client thread1.")
        print(ex)

    try:
        print("Starting client thread2")
        _thread.start_new_thread(client_task_wrapper, (str(2)))
    except Exception as ex:
        print("[ERROR] Failed to start client thread2.")
        print(ex)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(client_main)
    
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