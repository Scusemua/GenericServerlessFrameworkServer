import time 
from client import Client

"""
Invokes remote executors. This is used for running the test application using actual Lambdas, whereas local_driver.py is for running it all locally.
"""

c = Client()

c.invoke(do_create = True)

time.sleep(1)

c.invoke(do_create = False)