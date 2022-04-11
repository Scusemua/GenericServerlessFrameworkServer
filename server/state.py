class State(object):
    def __init__(self, ID = None, restart = False, pc = int(1)):
        self._ID = ID
        self._pc = pc
        self.restart = restart 
    
    @property
    def id(self):
        return self._ID

    @property
    def function_name(self):
        return self._function_name

    def __str__(self):
        return "State(ID=" + self._ID + ", PC=" + self._pc + ")"
