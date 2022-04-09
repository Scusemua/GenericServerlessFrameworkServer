from re import L
from barrier import Barrier
import Pyro4
from state import State
#from ClientNew import CallbackHandler
import importlib
from pydoc import locate
from synchronizer_thread import synchronizerThread

import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger.addHandler(ch)

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Synchronizer(object):

    synchronizers = {"barrier", "Barrier", "semaphore", "Semaphore"}
    
    def __init__(self):
        self._name = "Synchronizer"
        self.threadID = 0

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
        
    @Pyro4.oneway
    def synchronize(self, method_name, state, **kwargs):
        # where kws are: ID, program_counter cb, first
        # synchronize called as 
        #    synchronize(“wait_b”, ID = program_counter = cb =  first =
        # where we might start with cb = None and first = None
        # wait_b in Barrier is wait_b(self, **kwargs):
        # with ID = kwarg[‘ID’], etc though we may not be using parms

        # Todo: fast_wait_b : perhaps call Barrier setFast to set fast = true
        # and do the mutex.P instead of enterMonitor, so Enter and Exit
        # monitor of fast_wait_b do not do anything and
        # if fast_b returns wait is true then return WAIT and call
        # regular wait_b and enter_monitor again will not mutex.P
        # but will set fast = false so exit_monitor will do mutex.V.
        # note: sgnal and exit not used for fast_X and if caled always
        # fast = false so no check fast flag.

        ID_arg = kwargs["ID"]
        #program_counter = kwargs["program_counter"]
        #cb = kwargs["cb"]
        #first = kwargs["first"]

        program_counter = state._pc
        state.pc = 10
 
        logger.debug("starting remote method " + str(method_name) + ", ID is: " + ID_arg + " PC is " + str(program_counter))
	# note: most examples are getattr(instance, name) but we have a class
	# so we get an attribute of class (getattr(class, name) and we need
	# an instance to call it on so method(instance)(parm)

        #method_name = "try_"+method_name
	
        base_name, isTryMethod = self.isTry_and_getMethodName(method_name)
        logger.debug("method_name: " + method_name)
        logger.debug("base_name: " + base_name)
        logger.debug("isTryMethod: " + str(isTryMethod))

        try:

            # call try_baseName
            _synchronizer_method = getattr(self._synchClass,method_name)
        except Exception as x:
            logger.debug("Caught Error >>> %s" % x)
            logger.debug("Pyro Traceback:")
            logger.debug("".join(Pyro4.util.getPyroTraceback()))
            logger.debug("End Traceback")

        
        #_synchronizer_method(self._synchronizer)#(kwargs)
        #
#rhc: lock
        self.threadID += 1
#rhc: unlock

        
        #logger.debug ("starting caller thread to make the call"  + str(self.threadID))
        #callerThread = synchronizerThread(self.threadID, "callerThread"+str(self.threadID),  self._synchronizer, _synchronizer_method, **kwargs)
        #callerThread.start()
        #logger.debug("calling acquire exited.")
        #self._synchronizer._exited.acquire()

#rhc: we need synchronizeAsynch and synchronizeSynch where Synch version is for try or always 2-way
#     and Asynch is for always 1-way (like a P or V operation)
#     Q: A barrier will want to do something with outputs? Lie a fan-in with an output of results somewhere or
#     barrier succeeded by fan-in, which is collecting outputs and saving them? or is looping them back?
#     Example, suppose functions are each doing half and then fan-in results for final op on the halves, then output final result
#     or feed result back into next iteration, i.e., send this result back to both serverless functions? So we need a post()
#     for the barrier, which processes the sub-results, maybe outputs the result of this process and either sends something
#     back to functions or tells them to exit loop. while(!stop) { sf1 ... sfn: (do work; r, stop = b.waitB) so they al get stop and stop 

        if isTryMethod:
            # execute atomic try_wait_b followed by wait_b, i.e., no other thread can enter
            # between this threads try_waitb and wait_b.

            # call the try-method
            myPythonThreadName = "Try_callerThread"+str(ID_arg)
            restart, returnValue = self.doMethodCall(self.threadID, myPythonThreadName, self._synchronizer, _synchronizer_method, **kwargs)
            
            logger.debug("Try_callerThread " + str(ID_arg) + " restart " + str(restart))
            logger.debug("Try_callerThread " + str(ID_arg) + " returnValue " + str(returnValue))
            logger.debug("Try_callerThread Synchronizer successfully called synchronizer try-method and acquire exited. ")
                  
            if returnValue:  # base_name blocks on conditionVariable
                #send back to serverless function before executing base method for earliest serverless function termination
                #Need the socket of he caler to do this. When clientHandler of socket calls synchronize() on the synchronizer, it
                #can pass a way to return a value back to clentHandler, which is waiting for a vlaue (true, None) or (False, Object)
                #to send back to serverlessFunction. Example: clientHandler blicks on a semaphore and passes self to synchronizer
                #so we can call clientHandler.resume(tuple) where resume() saves tuple and release semaphore so clintHandlerThread
                #can get and send tuple to serverlessFunction.
                
                #send (true, None) back to serverless function
                try:
                    # call baseName method
                    _synchronizer_method = getattr(self._synchClass,base_name)
                except Exception as x:
                    logger.debug("Caught Error >>> %s" % x)
                    logger.debug("Pyro Traceback:")
                    logger.debug("".join(Pyro4.util.getPyroTraceback()))
                    logger.debug("End Traceback")
                myPythonThreadName = "BaseNameTryBlocking_callerThread"+str(ID_arg)
                restart, returnValue = self.doMethodCall(self.threadID, myPythonThreadName, self._synchronizer, _synchronizer_method, **kwargs)

                logger.debug("BaseNameTryBlocking_callerThread " + str(ID_arg) + " restart " + str(restart))
                logger.debug("BaseNameTryBlocking_callerThread " + str(ID_arg) + " returnValue " + str(returnValue))
                logger.debug("BaseNameTryBlocking_callerThread Synchronizer successfully called synchronizer baseName-method and acquire exited. ")

                # check and maybe do restart
            else:  # base_name does not block on conditionVariable
                try:
                    # call baseName
                    _synchronizer_method = getattr(self._synchClass,base_name)
                except Exception as x:
                    logger.debug("Caught Error >>> %s" % x)
                    logger.debug("Pyro Traceback:")
                    logger.debug("".join(Pyro4.util.getPyroTraceback()))
                    logger.debug("End Traceback")
                myPythonThreadName = "BaseNameTryNoBlocking_callerThreadTry"+str(self.threadID)
                restart, returnValue = self.doMethodCall(self.threadID, myPythonThreadName, self._synchronizer, _synchronizer_method, **kwargs)
                logger.debug("BaseNameTryNoBlocking_callerThreadTry " + str(ID_arg) + " restart " + str(restart))
                logger.debug("BaseNameTryNoBlocking_callerThreadTry " + str(ID_arg) + " returnValue " + str(returnValue))
                logger.debug("BaseNameTryNoBlocking_callerThreadTry Synchronizer successfully called synchronizer baseName-method and acquire exited. ")

                #rhc: Q: for fan-in send all fan-in outputs/inputs? Note: can execute fan-in task on server.
                
                # No restart, send return value back to serverless function, so execute baseName before send
                #send (true, returnValue(s)) back to serverless function
        else:
            myPythonThreadName = "NotTrycallerThread"+str(self.threadID)
            restart, returnValue = self.doMethodCall(self.threadID, myPythonThreadName, self._synchronizer, _synchronizer_method, **kwargs)   

            #rhc:   idea is if callerThread.getRestart() is true then restart he corresponding function.
            #rhc:   restart default/init value is true. Should be set to false for non-last callers of fan-in, or
            #         when doing synch/fast-path, in which case you know calling function is not restarting
            #rhc:   Barrier: would restart all, and init value of restart ia true
            #rhc:     if len(self._go) < (self._n - 1):
            #rhc            self._go.wait_c()
            #rhc      else:
            #rhc            threading.current_thread()._restart = False

            logger.debug("caller thread " + str(ID_arg) + " restart " + str(restart))
            logger.debug("caller thread " + str(ID_arg) + " returnValue " + str(returnValue))
            logger.debug(" Synchronizer successfully called synchronizer method and acquire exited. ")

            #if restart:
            #cb.restart(ID, program_counter, cb, first)
            return returnValue # for something to return

    def doMethodCall(self, PythonThreadID, myName, synchronizer, synchronizer_method, **kwargs):
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

