class State(object):
    def __init__(self, ID = None, restart = False, pc = int(1), keyword_arguments = None, return_value = None):
        self._ID = ID
        self._pc = pc
        self.restart = restart 
        self.return_value = return_value 
        self.keyword_arguments = keyword_arguments or {} 
    
    @property
    def id(self):
        return self._ID

    @property
    def function_name(self):
        return self._function_name

    def __str__(self):
        return "State(ID=" + self._ID + ", PC=" + self._pc + ")"
