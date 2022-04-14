from re import L
from barrier import Barrier
import Pyro4
from state import State
#from ClientNew import CallbackHandler
import importlib
from pydoc import locate
from synchronizer_thread import synchronizerThread
import boto3 
import ujson
import cloudpickle

from client import Client 

import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger.addHandler(ch)

 # TODO: The serverless function needs to pass its name to synchronize_sync/async so that it can be restarted.

aws_region = 'us-east-1'

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Synchronizer(object):

    synchronizers = {"barrier", "Barrier", "semaphore", "Semaphore"}
    
    def __init__(self):
        self._name = "Synchronizer"
        self.threadID = 0
        self.lambda_client = boto3.client("lambda", region_name = aws_region)
        self.client = Client()

    #def init(self, synchronizer_class_name = None, synchronizer_object_name = None, value):

    #@Pyro4.oneway
    #def init(self, synchronizer_class_name = None, synchronizer_object_name = None, **kwargs):
    def create(self, synchronizer_class_name, synchronizer_object_name, **kwargs):
        # where init call by Client is init(“Barrier”,”b”,[‘n’,2]): and kwargs passed to Barrier.init
        if not synchronizer_class_name in self.synchronizers:
            logger.debug("Error: invalid synchronizer class name.")
            # throw a remote exception? remote back to client?

        #e.g. “Barrier_b”
        self._synchronizer_name = (str(synchronizer_class_name) + '_' + str(synchronizer_object_name))
        logger.debug("self._synchronizer_name: " + self._synchronizer_name)
        
        logger.debug("get MyClass")

        # locate() described in: https://stackoverflow.com/a/24815361 - shows lots of other things to try, which didn't work for me
        # I got it from this simple example: https://stackoverflow.com/a/55968374
        self._synchClass = locate("barrier.Barrier")
        logger.debug("got MyClass")
        self._synchronizer = self._synchClass()
        if self._synchronizer == None:
            logger.debug("null synchronizer")
        
        #e.g. "b"
        self._synchronizer_object_name = synchronizer_object_name
        logger.debug("self._sycnhronizer_object_name: " + self._synchronizer_object_name)

        logger.debug("Calling _synchronizer init")
        #self._synchronizer.init(value)
        #self._synchronizer.initX(kwargs)
        self._synchronizer.init(**kwargs)  #2
        # where Barrier init is: init(**kwargs): if len(kwargs) not == 1
	    # logger.debug(“Error: Barrier init has too many argos”) self._n = kwargs[‘n’]

        logger.debug ("Called _synchronizer init")
        return 0


    #def synchronize(self, method_name, ID, program_counter):#cb, first):
    #Note: will not be using callback, ID pc and first are part of state
    #and not args but args may be refs to state. So passing  to
    #synchronize and it saves state, where list of args is part of state
    #and list of args is passed to _synchronizer_method;

    def isTry_and_getMethodName(self,name):
        if name.startswith("try_"):
            return name[4:], True
        return name, False
        
    def trySynchronize(self, method_name, state, **kwargs):
    # 	method_name is "executesWait"
    
        ID_arg = kwargs["ID"]
        logger.debug("starting trySynchronize, method_name: " + str(method_name) + ", ID is: " + ID_arg)
        
        try:
            _synchronizer_method = getattr(self._synchClass,method_name)
        except Exception as x:
            logger.error("Caught Error >>> %s" % x)
            raise ValueError("Synchronizer of type %s does not have method called %s. Cannot complete trySynchronize() call." % (self._synchClass, method_name))

        myPythonThreadName = "Try_callerThread"+str(ID_arg)
        restart, returnValue = self.doMethodCall(2, myPythonThreadName, self._synchronizer, _synchronizer_method, **kwargs)
                
        logger.debug("trySynchronize " + " restart " + str(restart))
        logger.debug("trySynchronize " + " returnValue " + str(returnValue))
        
        return returnValue

    @Pyro4.oneway
    def synchronize(self, method_name, state, **kwargs):
        ID_arg = kwargs["ID"]
        logger.debug("starting synchronize, method_name: " + str(method_name) + ", ID is: " + ID_arg)
        
        try:
            _synchronizer_method = getattr(self._synchClass,method_name)
        except Exception as x:
            logger.error("Caught Error >>> %s" % x)
        
        myPythonThreadName = "NotTrycallerThread"+str(self.threadID)
        restart, returnValue = self.doMethodCall(1, myPythonThreadName, self._synchronizer, _synchronizer_method, **kwargs) 
        
        #rhc:   idea is if callerThread.getRestart() is true then restart he corresponding function.
        #rhc:   restart default/init value is true. Should be set to false for non-last callers of fan-in, or
        #         when doing synch/fast-path, in which case you know calling function is not restarting
        #rhc:   Barrier: would restart all, and init value of restart ia true
        #rhc:     if len(self._go) < (self._n - 1):
        #rhc            self._go.wait_c()
        #rhc      else:
        #rhc            threading.current_thread()._restart = False

        logger.debug("synchronize " + str(ID_arg) + " restart " + str(restart))
        logger.debug("synchronize " + str(ID_arg) + " returnValue " + str(returnValue))
        logger.debug("synchronize successfully called synchronize method and acquire exited. ")

        #if restart:
        #	restart serverless function, needs its ID?
        if restart:
            state.restart = True 
            function_name = state.id 
            # TODO: Restart the function (invoke it).
            logger.info("Restarting Lambda function %s." % function_name)
            self.client.invoke(do_create = False, state = state)
            #self.lambda_client.invoke(FunctionName=function_name, InvocationType='Event', Payload=cloudpickle.dumps(state))
        
        return returnValue

    def doMethodCall(self, PythonThreadID, myName, synchronizer, synchronizer_method, **kwargs):
        """
        Call a method.

        Arguments:
        ----------
            TODO: Fill in this documentation.
        """
        logger.debug ("starting caller thread to make the call")
        callerThread = synchronizerThread(PythonThreadID, myName,  synchronizer, synchronizer_method, **kwargs)
        callerThread.start()
        callerThread.join()
        returnValue = callerThread.getReturnValue()
        restart = callerThread.getRestart()
        logger.debug("doMethodCall: returnValue: " + str(returnValue))
        # For 2-way: result = _synchronizer_method (self._synchronizer)(kwargs)
        # where wait_b in Barrier is wait_b(self, **kwargs):
        logger.debug("calling acquire exited.")
        synchronizer._exited.acquire()
        logger.debug("called acquire exited. returning ...")
        return restart, returnValue
    
# need to call generic init() method on synchronizer with list of args
#    @property 
#    def n(self):
#        return self._n 

#    @n.setter 
#    def n(self, value):
#        logger.debug("setter")
#        self._n = value 
#       self._barrier._n = value


def main():
    Pyro4.Daemon.serveSimple(
        {
            Synchronizer: "Synchronizer"
        },
        ns = False)

if __name__=="__main__":
    main()

#
# Execute: python SynchronizerNew.py

