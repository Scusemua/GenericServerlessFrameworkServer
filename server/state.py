class State(object):
    def __init__(
        self, 
        ID : str = None, 
        restart : bool = False, 
        pc : int = int(1), 
        keyword_arguments : dict = None, 
        return_value = None, 
        blocking : bool = None
    ):
        self._ID = ID                       # This is the variable used for the serverless function name.
        self._pc = pc                       # Program counter.
        self.restart = restart              # Indicates whether we're trying to restart a warm Lambda or if we're knowingly invoking a cold Lambda (value is False in this case).
        self.return_value = return_value    # The value being returned by the TCP server to the AWS Lambda function.
        self.blocking = blocking            # Indicates whether the Lambda executor is making a blocking or non-blocking call to the TCP server.
        self.keyword_arguments = keyword_arguments or {} # These are the keyword arguments passed from AWS Lambda function to TCP server.
    
    @property
    def id(self):
        return self._ID

    @property
    def function_name(self):
        return self._function_name

    def __str__(self):
        return "State(ID=" + self._ID + ", PC=" + self._pc + ")"
