filtersEnabled_wheels = "no"

inOrOut_wheels = "out"

# ToDo: "(python_tags>=1.2 | python_tags==1.01) & version>=18.0 & #^cp\d*d-\d*.whl$ | #^cp\d*d-manylinux14.whl$"
inFilters_wheels = {"version": [], "python_tags": [">=3.5"], "abi_tags": ["~cp36", "~cp37"], "platform_tags": ["~manylinux", "~win32", "~amd64"]}

outFilters_wheels = {"version": ["~rc"], "python_tags": ["~pp", "~cp2", "<3.5"], "abi_tags": ["~mu"], "platform_tags": ["~i686", "~win32"]}

# Attributes lists (https://peps.python.org/pep-0425/):
# version: rc[X]
# python_tags: py, cp, ip, pp, jy
# abi_tags: [XX]m, [XX]u, [XX]d
# platform_tags: win32, linux_i386, linux_x86_64
#
#   where X are numbers.

from typing import Dict, List


class WheelsConfig:

    """
    A class to save the configuration for the pypickup commands.

    The user can choose between filtering wheels in or out. If self.inOrOut == "in", the expected logic is that all packages will not be considere by
    default, only if they match with the specified expressions. If self.inOurOut == "out", then all the packages will be included by default and only
    those containing some of the specified expressions will be discarded.

    One can exactly match a expression (default behaviour), or either using the "~" or ">", "<", ">=", "<=" modifiers:
        "~" can be used to indicate "it contains the following string", for every kind of filter.
        ">", "<", ">=", "<=" can be used only in 'python_tags' filter. In this case, the format of the string can contain 1 '.' characters or more,
            as well as the inequality characters themselves, but no other special characters. E.g. "cp<=3.2" wouldn't be correct. ">3" is translated
            into ">3.0".

    If a list for a specific field is empty, then that field is not used to either filter in or out the wheels.
    """

    _incorrectInOrOutMessage: str = "Incorrect settings field 'inOrOut'! Set 'in' or 'out' in settings/wheelFilters.py."

    def __init__(self):
        self._filtersEnabled: str = filtersEnabled_wheels

        self._inOrOut: str = inOrOut_wheels

        self._inFilters: Dict[str, List[str]] = inFilters_wheels
        self._outFilters: Dict[str, List[str]] = outFilters_wheels

    @property
    def filtersEnabled(self):
        return self._filtersEnabled

    @property
    def inOrOut(self):
        return self._inOrOut

    @property
    def inFilters(self):
        return self._inFilters

    @property
    def outFilters(self):
        return self._outFilters

    @property
    def incorrectInOrOutMessage(self):
        return self._incorrectInOrOutMessage

    def getFilterKeys(self) -> List[str]:
        if self.inOrOut == "in":
            return list(self.inFilters.keys())
        elif self.inOrOut == "out":
            return list(self.outFilters.keys())
        else:
            raise ValueError("Config::getFilterKeys() - " + self._incorrectInOrOutMessage)

    def getField(self, fieldName: str) -> List[str]:
        if self.inOrOut == "in":
            if fieldName not in self.inFilters:
                raise ValueError("Config::getField() - Field name not available in inFilters settings!")
            return self.inFilters[fieldName]
        elif self.inOrOut == "out":
            if fieldName not in self.outFilters:
                raise ValueError("Config::getField() - Field name not available in outFilters settings!")
            return self.outFilters[fieldName]
        else:
            raise ValueError("Config::getField() - " + self._incorrectInOrOutMessage)
