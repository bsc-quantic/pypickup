inOrOut = "out"

inFilters = {
    "version": ["any"],
    "python_tags": [">=3.5"],
    "abi_tags": ["~cp36", "~cp37"],
    "platform_tags": ["~manylinux", "~win32", "~amd64"]
}

outFilters = {
    "version": ["~rcl"],
    "python_tags": ["~pp", "~cp2"],
    "abi_tags": ["~mu"],
    "platform_tags": ["~i686", "~win32"]
}

class Config:

    """
    A class to save the configuration for the pypiCache commands. 

    The user can choose between filtering wheels in or out. If self.inOrOut == "in", the expected logic is that all packages will not be considere by
    default, only if they match with the specified expressions. If self.inOurOut == "out", then all the packages will be included by default and only
    those containing some of the specified expressions will be discarded.

    One can exactly match a expression (default behaviour), or either using the "~" or ">", "<", ">=", "<=" modifiers:
        "~" can be used to indicate "it contains the following string".
        ">", "<", ">=", "<=" can be used only in python_tags.
    """

    def __init__(self):
        self._inOrOut: str = inOrOut
        self._inFilters: dict = inFilters
        self._outFilters: dict = outFilters
    
    @property
    def inOrOut(self):
        return self._inOrOut
        
    @property
    def inFilters(self):
        return self._inFilters
    
    @property
    def outFilters(self):
        return self._outFilters

    def getField(self, fieldName: str) -> list:
        if self.inOrOut == "in":
            if fieldName not in self.inFilters:
                raise ValueError("Field name not available in inFilters settings!")
            return self.inFilters[fieldName]
        elif self.inOrOut == "out":
            if fieldName not in self.outFilters:
                raise ValueError("Field name not available in outFilters settings!")
            return self.outFilters[fieldName]
        else:
            raise ValueError("Wrong 'inOrOut' settings!")