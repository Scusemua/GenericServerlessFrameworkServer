from re import L
from barrier import Barrier
import Pyro4
from state import State
#from ClientNew import CallbackHandler
import importlib
from pydoc import locate
from synchronizer_thread import synchronizerThread

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
            print("Error: invalid synchronizer class name.")
            # throw a remote exception? remote back to client?

        #e.g. “Barrier_b”
        self._synchronizer_name = (str(synchronizer_class_name) + '_' + str(synchronizer_object_name))
        print("self._synchronizer_name: " + self._synchronizer_name)
        
        print("get MyClass")

        # locate() described in: https://stackoverflow.com/a/24815361 - shows lots of other things to try, which didn't work for me
        # I got it from this simple example: https://stackoverflow.com/a/55968374
        self._synchClass = locate("barrier.Barrier")
        print("got MyClass")
        self._synchronizer = self._synchClass()
        if self._synchronizer == None:
            print("null synchronizer")
        
        #e.g. "b"
        self._synchronizer_object_name = synchronizer_object_name
        print("self._sycnhronizer_object_name: " + self._synchronizer_object_name)

        print("Calling _synchronizer init")
        #self._synchronizer.init(value)
        #self._synchronizer.initX(kwargs)
        self._synchronizer.init(**kwargs)  #2
        # where Barrier init is: init(**kwargs): if len(kwargs) not == 1
	    # print(“Error: Barrier init has too many argos”) self._n = kwargs[‘n’]

        print ("Called _synchronizer init")
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
    def synchronize(self, method_name, **kwargs):
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

        ID = kwargs["ID"]
        program_counter = kwargs["program_counter"]
        cb = kwargs["cb"]
        first = kwargs["first"]
 
        print("starting remote method " + str(method_name) + ", ID is: " + ID + " PC is " + str(program_counter))
	# note: most examples are getattr(instance, name) but we have a class
	# so we get an attribute of class (getattr(class, name) and we need
	# an instance to call it on so method(instance)(parm)

        method_name = "try_"+method_name
	
        base_name, isTryMethod = self.isTry_and_getMethodName(method_name)
        print("method_name: " + method_name)
        print("base_name: " + base_name)
        print("isTryMethod: " + str(isTryMethod))

        try:

            # call try_baseName
            _synchronizer_method = getattr(self._synchClass,method_name)
        except Exception as x:
            print("Caught Error >>> %s" % x)
            print("Pyro Traceback:")
            print("".join(Pyro4.util.getPyroTraceback()))
            print("End Traceback")

        
        #_synchronizer_method(self._synchronizer)#(kwargs)
        #
#rhc: lock
        self.threadID += 1
#rhc: unlock

        
        #print ("starting caller thread to make the call"  + str(self.threadID))
        #callerThread = synchronizerThread(self.threadID, "callerThread"+str(self.threadID),  self._synchronizer, _synchronizer_method, **kwargs)
        #callerThread.start()
        #print("calling acquire exited.")
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
            myPythonThreadName = "Try_callerThread"+str(ID)
            restart, returnValue = self.doMethodCall(self.threadID, myPythonThreadName, self._synchronizer, _synchronizer_method, **kwargs)
            
            print("Try_callerThread " + str(ID) + " restart " + str(restart))
            print("Try_callerThread " + str(ID) + " returnValue " + str(returnValue))
            print("Try_callerThread Synchronizer successfully called synchronizer try-method and acquire exited. ")
                  
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
                    print("Caught Error >>> %s" % x)
                    print("Pyro Traceback:")
                    print("".join(Pyro4.util.getPyroTraceback()))
                    print("End Traceback")
                myPythonThreadName = "BaseNameTryBlocking_callerThread"+str(ID)
                restart, returnValue = self.doMethodCall(self.threadID, myPythonThreadName, self._synchronizer, _synchronizer_method, **kwargs)

                print("BaseNameTryBlocking_callerThread " + str(ID) + " restart " + str(restart))
                print("BaseNameTryBlocking_callerThread " + str(ID) + " returnValue " + str(returnValue))
                print("BaseNameTryBlocking_callerThread Synchronizer successfully called synchronizer baseName-method and acquire exited. ")

                # check and maybe do restart
            else:  # base_name does not block on conditionVariable
                try:
                    # call baseName
                    _synchronizer_method = getattr(self._synchClass,base_name)
                except Exception as x:
                    print("Caught Error >>> %s" % x)
                    print("Pyro Traceback:")
                    print("".join(Pyro4.util.getPyroTraceback()))
                    print("End Traceback")
                myPythonThreadName = "BaseNameTryNoBlocking_callerThreadTry"+str(self.threadID)
                restart, returnValue = self.doMethodCall(self.threadID, myPythonThreadName, self._synchronizer, _synchronizer_method, **kwargs)
                print("BaseNameTryNoBlocking_callerThreadTry " + str(ID) + " restart " + str(restart))
                print("BaseNameTryNoBlocking_callerThreadTry " + str(ID) + " returnValue " + str(returnValue))
                print("BaseNameTryNoBlocking_callerThreadTry Synchronizer successfully called synchronizer baseName-method and acquire exited. ")

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

            print("caller thread " + str(ID) + " restart " + str(restart))
            print("caller thread " + str(ID) + " returnValue " + str(returnValue))
            print(" Synchronizer successfully called synchronizer method and acquire exited. ")

            #if restart:
            #cb.restart(ID, program_counter, cb, first)
            return program_counter # for something to return

    def doMethodCall(self, PythonThreadID, myName, synchronizer, synchronizer_method, **kwargs):
        print ("starting caller thread to make the call")
        callerThread = synchronizerThread(PythonThreadID, myName,  synchronizer, synchronizer_method, **kwargs)
        callerThread.start()
        callerThread.join()
        returnValue = callerThread.getReturnValue()
        restart = callerThread.getRestart()
        print("doMethodCall: returnValue: " + str(returnValue))
        # For 2-way: result = _synchronizer_method (self._synchronizer)(kwargs)
        # where wait_b in Barrier is wait_b(self, **kwargs):
        print("calling acquire exited.")
        synchronizer._exited.acquire()
        print("called acquire exited. returning ...")
        return restart, returnValue
    
# need to call generic init() method on synchronizer with list of args
#    @property 
#    def n(self):
#        return self._n 

#    @n.setter 
#    def n(self, value):
#        print("setter")
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

