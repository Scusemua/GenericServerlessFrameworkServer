import boto3 
import uuid 
import ujson 
import time 

from state import State

import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

logger.addHandler(ch)

function_name = "PyroTest"

class Client(object):
    def __init__(self):
        self.client_id = str(uuid.uuid4)
        self.lambda_client = boto3.client("lambda", region_name = "us-east-1")

    def invoke(self):
        state = State(id = "PyroTest", restart = False, task_id = str(uuid.uuid4()))
        payload = {
            "state": state 
        }
        self.lambda_client.invoke(FunctionName = function_name, InvocationType = 'Event', Payload = ujson.dumps(payload))

        logger.debug("Invoked AWS Lambda function '%s'" % function_name)