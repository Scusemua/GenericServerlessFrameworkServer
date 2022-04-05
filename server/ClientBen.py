import sys
import _thread
import time
from counting_semaphore import CountingSemaphore
from state import State

SERVER_IP = ""

if sys.version_info<(3,0):
    input = raw_input

def ClientTask(taskID):
    state = State()
    state._ID = taskID
    state._pc = taskID
    print(taskID + " calling synchronize PC: " + str(state._ID))
    TCP.send("synchronize", "b", "wait_b", state, id=taskID)
    print(taskID + " called synchronize PC: " + str(state._ID))

if __name__ == "__main__":
    TCP.send("create", "Barrier", "b", n=2)

    try:
        print("Starting client thread1")
        _thread.start_new_thread(taskState, (str(1))
    except Exception as ex:
        print("[ERROR] Failed to start client thread1.")
        print(ex)

    try:
        print("Starting client thread2")
        _thread.start_new_thread(taskState, (str(2))
    except Exception as ex:
        print("[ERROR] Failed to start client thread2.")
        print(ex)

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