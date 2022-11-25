from typing import Dict, List

import os, shutil

import yaml

class WheelsConfig:

    """
    A class to save the configuration for the pypickup commands.

    The user can choose between filtering wheels in or out. If self.inOrOut == "in", the expected logic is that all packages will not be considered
    by default, only if they match with the specified expressions. If self.inOurOut == "out", then all the packages will be included by default and 
    only those containing some/all of the specified expressions will be discarded.

    The _ORorAndAttributes modifiers states whether the values for each field should be concatenated with an 'or' or with an 'and' logical operator.
    The _ORorAnd variable, in turn, states whether the previous logical results should be concatenated with an 'or' or with an 'and'. See the
    examples section below for a specific example about this.

    One can exactly match a expression (default behaviour), or either using the "~" or ">", "<", ">=", "<=" modifiers:
        "~" can be used to indicate "it contains the following string", for every kind of filter.
        ">", "<", ">=", "<=" can be used only in 'python_tags' filter. In this case, the format of the string can contain 1 '.' characters or more,
            as well as the inequality characters themselves, but no other special characters. E.g. "cp<=3.2" wouldn't be correct. ">3" is translated
            into ">3.0".

    If a list for a specific field is empty, then that field is not used to either filter in or out the wheels.

    
    According to https://peps.python.org/pep-0425/, some attribute strings are:
        version: rc[X]
        python_tags: py, cp, ip, pp, jy
        abi_tags: [XX]m, [XX]u, [XX]d
        platform_tags: win32, linux_i386, i686, linux_x86_64, manylinux, macos, intel

            where X are numbers.


    #### EXAMPLES ####

    inOrOut_wheels = "in"

    inFilters_wheels = {
        "version": [],
        "python_tags": [">=3.5"],
        "abi_tags": ["~cp36", "~cp37"],
        "platform_tags": ["~manylinux", "~x86_64"]
    }
    in_ORorAnd = "and"
    in_ORorAndAttributes = {
        "version": "or",
        "python_tags": "or",
        "abi_tags": "or",
        "platform_tags": "and",
    }

    outFilters_wheels = {
        "version": ["~rc"],
        "python_tags": ["~pp", "~cp2", "<3.5"],
        "abi_tags": ["~mu"],
        "platform_tags": ["~i686", "~win32", "~amd64"]
    }
    out_ORorAnd = "and"
    out_ORorAndAttributes = {
        "version": "or",
        "python_tags": "or",
        "abi_tags": "or",
        "platform_tags": "or",
    }

        * For this example, the logical expression that should be evaluated to true in order to include a certain 'wheel' file in the list of files
          to be downloaded is:
            if ((   wheel.python_tags >= 3.5 ) AND 
                (   wheel.abi_tags.contains("cp36") OR wheel.abi_tags.contains("cp37") ) AND
                (   wheel.platform_tags.contains("manylinux") AND wheel.platform_tags.contains("x86_64") ) ):
                        includeWheel(wheel)

        ** After this, if we would like to download too the files for AMD64 machines running Windows, we would specify in platform_tags those 2
           filters, and perform an 'update' command on the same package.

    """

    _incorrectInOrOutMessage: str = "Incorrect settings field 'inOrOut'! Set 'in' or 'out' in settings/wheelFilters.py."

    def __init__(self):
        settingsDir: str = os.path.join(os.getenv("PYPICKUP_INDEX_PATH", default="./.pypickup/"), "settings")
        settingsFileName: str = "wheelFiltersSettings.yaml"
        
        self._setSettingsEnvironment(settingsDir, settingsFileName)

        self._settingsFilePath = os.path.join(settingsDir, settingsFileName)

        stream = open(self._settingsFilePath, 'r')
        settingsDict = yaml.safe_load(stream)

        try:
            self._filtersEnabled: str = settingsDict["filtersEnabled_wheels"]
            self._inOrOut: str = settingsDict["inOrOut_wheels"]

            self._inFilters: Dict[str, List[str]] = settingsDict["inFilters_wheels"]
            self._outFilters: Dict[str, List[str]] = settingsDict["outFilters_wheels"]

            self._in_ORorAnd: str = settingsDict["in_ORorAnd"]
            self._in_ORorAndAttributes: Dict[str, List[str]] = settingsDict["in_ORorAndAttributes"]
            self._out_ORorAnd: str = settingsDict["out_ORorAnd"]
            self._out_ORorAndAttributes: Dict[str, List[str]] = settingsDict["out_ORorAndAttributes"]
        except KeyError as key:
            print("wheelFilterSettings.yaml file not correct. Field " + str(key) + " not found!")
            exit(0)

    @property
    def settingsFilePath(self):
        return self._settingsFilePath

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
    def in_ORorAnd(self):
        return self._in_ORorAnd

    @property
    def out_ORorAnd(self):
        return self._out_ORorAnd

    @property
    def in_ORorAndAttributes(self):
        return self._in_ORorAndAttributes

    @property
    def out_ORorAndAttributes(self):
        return self._out_ORorAndAttributes

    @property
    def incorrectInOrOutMessage(self):
        return self._incorrectInOrOutMessage

    def _setSettingsEnvironment(self, settingsDir: str, settingsFileName: str):
        if not os.path.exists(settingsDir):
            os.makedirs(settingsDir)

        wheelFiltersSettings_OriginalPath: str = os.path.join("./pypickup/settings/", settingsFileName)
        if os.path.isfile(wheelFiltersSettings_OriginalPath):
            wheelFilterSettings_UserFile = os.path.join(settingsDir, settingsFileName)

            if not os.path.isfile(wheelFilterSettings_UserFile):
                shutil.copyfile(wheelFiltersSettings_OriginalPath, wheelFilterSettings_UserFile)

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
                raise ValueError("Config::getField() - Field '" + fieldName + "' name not available in inFilters settings!")
            return self.inFilters[fieldName]
        elif self.inOrOut == "out":
            if fieldName not in self.outFilters:
                raise ValueError("Config::getField() - Field '" + fieldName + "' name not available in outFilters settings!")
            return self.outFilters[fieldName]
        else:
            raise ValueError("Config::getField() - " + self._incorrectInOrOutMessage)

    def getFilterConcatOperator(self) -> str:
        if self.inOrOut == "in":
            return self.in_ORorAnd
        elif self.inOrOut == "out":
            return self.out_ORorAnd
        else:
            raise ValueError("Config::getFilterConcatOperator() - " + self._incorrectInOrOutMessage)

    def getFieldConcatOperator(self, fieldName: str) -> str:
        if self.inOrOut == "in":
            if fieldName not in self.in_ORorAndAttributes:
                raise ValueError("Config::getField() - Field '" + fieldName + "' name not available in in_ORorAndAttributes settings!")
            return self.in_ORorAndAttributes[fieldName]
        elif self.inOrOut == "out":
            if fieldName not in self.out_ORorAndAttributes:
                raise ValueError("Config::getField() - Field '" + fieldName + "' name not available in out_ORorAndAttributes settings!")
            return self.out_ORorAndAttributes[fieldName]
        else:
            raise ValueError("Config::getField() - " + self._incorrectInOrOutMessage)
