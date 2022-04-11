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
        self._ID = ID
        self._pc = pc
        self.restart = restart 
        self.return_value = return_value 
        self.blocking = blocking
        self.keyword_arguments = keyword_arguments or {} 
    
    @property
    def id(self):
        return self._ID

    @property
    def function_name(self):
        return self._function_name

    def __str__(self):
        return "State(ID=" + self._ID + ", PC=" + self._pc + ")"
