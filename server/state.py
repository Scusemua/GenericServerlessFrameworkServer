class State(object):
    def __init__(self, ID = 0, function_name = None):
        self._ID = ID
        self._pc = int(1)
        self._function_name = function_name
    
    @property
    def function_name(self):
        return self._function_name

    def __str__(self):
        return "State(ID=" + self._ID + ", PC=" + self._pc + ", FunctionName=" + self._function_name + ")"
