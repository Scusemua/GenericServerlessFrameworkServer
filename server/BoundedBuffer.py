from re import L
from monitor_su import MonitorSU, ConditionVariable
import threading
import _thread
import time

class BoundedBuffer (MonitorSU):
    def __init__(self, initial_capacity = 0, monitor_name = None):
        super(BoundedBuffer, self).__init__(monitor_name=monitor_name)
        self._capacity = initial_capacity

    def init(self, **kwargs):
        self._fullSlots=0
        self._buffer=[]
        self._notFull=super().get_condition_variable(condition_name="notFull")
        self._notEmpty=super().get_condition_variable(condition_name="notEmpty")
        print(kwargs)
        self._in=0
        self._out=0


    def deposit(self, value=None, **kwargs):
        super().enter_monitor(method_name="deposit")
        print(" deposit() entered monitor, len(self._notFull) ="+str(len(self._notFull))+",self._capacity="+str(self._capacity))
        print(" deposit() entered monitor, len(self._notEmpty) ="+str(len(self._notEmpty))+",self._capacity="+str(self._capacity))
        if self._fullSlots==self._capacity:
            self._notFull.wait_c()
        self._buffer.insert(self._in,value)
        self._in=(self._in+1) % int(self._capacity)
        self._fullSlots+=1
        self._notEmpty.signal_c_and_exit_monitor()
        threading.current_thread()._returnValue=1
        return 1


    def withdraw(self, **kwargs):
        super().enter_monitor(method_name = "withdraw")
        print(" withdraw() entered monitor, len(self._notFull) ="+str(len(self._notFull))+",self._capacity="+str(self._capacity))
        print(" withdraw() entered monitor, len(self._notEmpty) ="+str(len(self._notEmpty))+",self._capacity="+str(self._capacity))
        value = 0
        if self._fullSlots==0:
            self._notEmpty.wait_c()
        value=self._buffer[self._out]
        self._out=(self._out+1) % int(self._capacity)
        self._fullSlots-=1
        threading.current_thread()._returnValue=value
        self._notFull.signal_c_and_exit_monitor()
        return value


def taskD(b : BoundedBuffer):
    time.sleep(1)
    print("Calling deposit")
    b.deposit("A")
    print("Successfully called deposit")

def taskW(b : BoundedBuffer):
    print("Calling withdraw")
    value = b.withdraw()
    print("Successfully called withdraw")


def main():
    b = BoundedBuffer(initial_capacity=1,monitor_name="BoundedBuffer")
    b.init()
    #b.deposit(value = "A")
    #value = b.withdraw()
    #print(value)
    #b.deposit(value = "B")
    #value = b.withdraw()
    #print(value)

    try:
        print("Starting D thread")
        _thread.start_new_thread(taskD, (b,))
    except Exception as ex:
        print("[ERROR] Failed to start first thread.")
        print(ex)

    try:
        print("Starting first thread")
        _thread.start_new_thread(taskW, (b,))
    except Exception as ex:
        print("[ERROR] Failed to start first thread.")
        print(ex)

    print("Sleeping")
    time.sleep(2)
    print("Done sleeping")

if __name__=="__main__":
    main()
