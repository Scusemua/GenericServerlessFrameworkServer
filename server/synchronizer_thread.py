
from threading import Thread

class synchronizerThread(Thread):
    def __init__(self, threadID, PythonThreadName, synchronizer, synchronizer_method, **kwargs):
        # Call the Thread class's init function
        #Thread.__init__(self)
        super(synchronizerThread,self).__init__(name=PythonThreadName)
        self._threadID = threadID
        self._synchronizer = synchronizer
        self._synchronizer_method = synchronizer_method
        self._restart = True
        #self._serverlessFunctionID = kwargs['ID']
        self._kwargs = kwargs

    def getRestart(self):
        return self._restart
    def getID(self):
        return self._threadID
    def getReturnValue(self):
        return self._returnValue
        
    # Override the run() function of Thread class
    def run(self):
        #print("kwargs serverlessFunctionID: " + self._serverlessFunctionID)
        # lucky guess on passing argument self._serverlessFunctionID to self._synchronizer_method
        #self._synchronizer_method(self._synchronizer,self._serverlessFunctionID)

        self._returnValue = self._synchronizer_method(self._synchronizer,**self._kwargs)
        # where wait_b in Barrier is wait_b(self, **kwargs):

        print ("return value is " + str(self._returnValue))
