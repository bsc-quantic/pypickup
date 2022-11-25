import os

import re

from typing import Tuple, Dict, List

from bs4 import BeautifulSoup, element as bs4Element
import wheel_filename
from multimethod import multimethod

from pypickup.settings.wheelFilters import WheelsConfig


class WheelsManager:
    """
    A class to manage Python wheels.
    """

    _aprox_char: str = "~"
    _lt_char: str = "<"
    _gt_char: str = ">"
    _lte_char: str = "<="
    _gte_char: str = ">="

    def __init__(self):
        self._wheelsConfig = WheelsConfig()

        self.__checkFilters()

    @property
    def wheelsConfig(self):
        return self._wheelsConfig

    @wheelsConfig.setter
    def packageName(self, new_wheelsConfig: str):
        self._wheelsConfig = new_wheelsConfig

    def getWheelFiltersSettingsFilePath(self) -> str:
        return self._wheelsConfig.settingsFilePath

    def areWheelFiltersEnabled(self) -> bool:
        return self._wheelsConfig.filtersEnabled == "yes"
    
    def inOrOutFilterEnabled(self) -> str:
        return self.wheelsConfig.inOrOut

    def __getSimplifiedPythonVersionFromFilterFormat(self, pythonVersionInFilterFormat: str) -> str:
        simplifiedPythonVersion: str = pythonVersionInFilterFormat.replace(".", "")

        simplifiedPythonVersion = re.sub(rf"({self._lte_char}|{self._gte_char}|{self._gt_char}|{self._lt_char})", r"", simplifiedPythonVersion)

        return simplifiedPythonVersion

    def __isCastableToInt(self, stringToCast: str) -> bool:
        try:
            int(stringToCast)
        except ValueError:
            return False
        return True

    def __checkFilters(self):
        filterNames: List[str] = self.wheelsConfig.getFilterKeys()
        for filterName in filterNames:

            filtersForWheel: List[str] = self.wheelsConfig.getField(filterName)
            for filter in filtersForWheel:

                if re.search(rf"({self._lt_char}|{self._gt_char})", filter):
                    if filterName != "python_tags":
                        raise ValueError("WheelsManager::__checkFilters - NOT SUPPORTED inequalities for filter '" + filterName + "'.")
                    else:
                        filterSimplifiedPythonVersion: str = self.__getSimplifiedPythonVersionFromFilterFormat(filter)
                        if not self.__isCastableToInt(filterSimplifiedPythonVersion):
                            raise ValueError("WheelsManager::__checkFilters - NOT SUPPORTED Python version format in filter '" + filterName + "' (filter: " + filter + "). A version should be a number-formatted string.")
                else:
                    if re.search(rf"[^a-zA-Z1-9~_]", filter):
                        raise ValueError("WheelsManager::__checkFilters - NOT SUPPORTED format in filter '" + filterName + "' (filter: " + filter + "). Remove the non-available characters.")

    def __getLiteralFilter(self, filter: str, filterName: str) -> str:
        filterLiteral: str = filter.replace("~", "")

        if filterName == "python_tags":
            filterLiteral = self.__getSimplifiedPythonVersionFromFilterFormat(filterLiteral)

        return filterLiteral

    def __getPythonVersions(self, filterString: str, wheelString: str) -> Tuple[int, int]:
        filterStringCleaned: str = re.sub(rf"[a-zA-Z]*(\d*)", r"\1", filterString)
        wheelStringCleaned: str = re.sub(rf"[a-zA-Z]*(\d*)", r"\1", wheelString)

        resultingFilterVersion: int = int(filterStringCleaned)
        resultingWheelVersion: int = int(wheelStringCleaned)

        filterNumberOfDigits: int = len(filterStringCleaned)
        wheelNumberOfDigits: int = len(wheelStringCleaned)
        if filterNumberOfDigits < wheelNumberOfDigits:
            resultingWheelVersion = int(int(wheelStringCleaned) / pow(10, wheelNumberOfDigits - filterNumberOfDigits))
        elif filterNumberOfDigits > wheelNumberOfDigits:
            resultingFilterVersion = int(int(filterStringCleaned) / pow(10, filterNumberOfDigits - wheelNumberOfDigits))

        return resultingFilterVersion, resultingWheelVersion

    @multimethod
    def __fulfillFilterCriteria(self, wheelAttribute: str, filter: str, filterName: str) -> bool:
        filterLiteral: str = self.__getLiteralFilter(filter, filterName)

        if self._aprox_char in filter:
            if filterLiteral in wheelAttribute:
                return True
        else:
            if filterName == "python_tags":

                filter_pyVersion, wheel_pyVersion = self.__getPythonVersions(filterLiteral, wheelAttribute)
                if self._lte_char in filter:
                    if wheel_pyVersion <= filter_pyVersion:
                        return True
                elif self._gte_char in filter:
                    if wheel_pyVersion >= filter_pyVersion:
                        return True
                elif self._lt_char in filter:
                    if wheel_pyVersion < filter_pyVersion:
                        return True
                elif self._gt_char in filter:
                    if wheel_pyVersion > filter_pyVersion:
                        return True

        return False

    @__fulfillFilterCriteria.register
    def _(self, wheelAttributeList: List[str], filter: str, filterName: str) -> bool:
        for wheelAttribute in wheelAttributeList:
            if self.__fulfillFilterCriteria(wheelAttribute, filter, filterName):
                return True

        return False

    def __getDefaultBehaviourForIncludingWheels(self):
        if self.wheelsConfig.inOrOut == "in":
            return False
        elif self.wheelsConfig.inOrOut == "out":
            return True
        else:
            raise ValueError("WheelsManager::__getDefaultBehaviourForIncludingWheels - " + self.wheelsConfig.incorrectInOrOutMessage)

    def __needToBeIncluded(self, parsedWheel: wheel_filename.ParsedWheelFilename) -> bool:
        filterKeys: List[str] = self.wheelsConfig.getFilterKeys()
        for filterKey in filterKeys:
            wheelAttribute = getattr(parsedWheel, filterKey)
            filtersForWheel: List[str] = self.wheelsConfig.getField(filterKey)

            for filter in filtersForWheel:
                if self.__fulfillFilterCriteria(wheelAttribute, filter, filterKey):
                    if self.wheelsConfig.inOrOut == "in":
                        return True
                    elif self.wheelsConfig.inOrOut == "out":
                        return False
                    else:
                        raise ValueError("WheelsManager::__needToBeIncluded - " + self.wheelsConfig.incorrectInOrOutMessage)

        return self.__getDefaultBehaviourForIncludingWheels()

    def isValidWheel(self, wheelName: str) -> bool:
        """Checks out whether the 'wheelName' is a valid wheel name according to the wheel-filename package (https://pypi.org/project/wheel-filename/) and the settings file in settings/wheelFilters.py."""

        if os.path.splitext(wheelName)[1] == ".whl":
            try:
                parsedWheel = wheel_filename.parse_wheel_filename(wheelName)

                filtersEnabled: str = self._wheelsConfig.filtersEnabled
                if filtersEnabled == "no":
                    return True
                elif filtersEnabled != "yes":
                    raise ValueError("WheelsManager::isValidWheel - Incorrect value for 'filtersEnabled_wheels' field in settings/wheelFilters.py.")

                if self.__needToBeIncluded(parsedWheel):
                    return True

                return False

            except wheel_filename.InvalidFilenameError:
                print('Incorrect wheel format "' + wheelName + '". Ignored.')
                return False


class HTMLManager:

    """
    A class used for builing and managing the HTML files needed for the PyPI local repository.
    """

    _wheelsManager = WheelsManager()

    _baseHTML_fromScratch = """
        <!DOCTYPE html>
        <html>
            <body>
            </body>
        </html>
    """

    def __init__(self):
        self._printAllFileNames: bool

        self._onlySources: bool
        self._includeDevs: bool
        self._includeRCs: bool
        self._includePlatformSpecific: bool

    @property
    def printAllFileNames(self):
        return self._printAllFileNames

    @property
    def onlySources(self):
        return self._onlySources

    @property
    def includeDevs(self):
        return self._includeDevs

    @property
    def includeRCs(self):
        return self._includeRCs

    @property
    def includePlatformSpecific(self):
        return self._includePlatformSpecific

    @printAllFileNames.setter
    def printAllFileNames(self, new_printAllFileNames: bool):
        self._printAllFileNames = new_printAllFileNames

    @onlySources.setter
    def onlySources(self, new_onlySources: bool):
        self._onlySources = new_onlySources

    @includeDevs.setter
    def includeDevs(self, new_includeDevs: bool):
        self._includeDevs = new_includeDevs

    @includeRCs.setter
    def includeRCs(self, new_includeRCs: bool):
        self._includeRCs = new_includeRCs

    @includePlatformSpecific.setter
    def includePlatformSpecific(self, new_includePlatformSpecific: bool):
        self._includePlatformSpecific = new_includePlatformSpecific

    def setFlags(self, printAllFileNames: bool, onlySources: bool, includeDevs: bool, includeRCs: bool, includePlatformSpecific: bool):
        self.printAllFileNames = printAllFileNames
        self.onlySources = onlySources
        self.includeDevs = includeDevs
        self.includeRCs = includeRCs
        self.includePlatformSpecific = includePlatformSpecific

    def getWheelFiltersSettingsFilePath(self) -> str:
        return self._wheelsManager.getWheelFiltersSettingsFilePath()

    def areWheelFiltersEnabled(self) -> bool:
        return self._wheelsManager.areWheelFiltersEnabled()

    def inOrOutFilterEnabled(self) -> str:
        return self._wheelsManager.inOrOutFilterEnabled()

    def getBaseHTML(self) -> str:
        return self._baseHTML_fromScratch

    def __getElementContentInlined(self, htmlString: str, element: str) -> str:
        """Gets inlined the specified 'element' from the 'htmlString', returning a new HTML string."""

        resultingHTML: str = ""
        resultingHTML = re.sub(rf"(<{element}.*>)[\n ]+", r"\1", htmlString)
        resultingHTML = re.sub(rf"[\n ]+(</{element}>)", r"\1", resultingHTML)

        return resultingHTML

    def __getDecodedASCII(self, htmlString: str) -> str:
        htmlCodes = (("'", "&#39;"), ('"', "&quot;"), (">", "&gt;"), ("<", "&lt;"), ("&", "&amp;"))

        for code in htmlCodes:
            htmlString = htmlString.replace(code[1], code[0])

        return htmlString

    def __prettifyHTML(self, htmlSoup: BeautifulSoup) -> str:
        """Lets the 'htmlString' formatted as desired."""

        resultingHTML: str = str(htmlSoup.prettify())

        resultingHTML = self.__getElementContentInlined(resultingHTML, "a")
        resultingHTML = self.__getDecodedASCII(resultingHTML)

        return resultingHTML

    def existsHTMLEntry(self, htmlString: str, tagName: str, entryText: str) -> bool:
        soup = BeautifulSoup(htmlString, "html.parser")

        if soup.find(tagName, string=entryText):
            return True
        return False

    def insertHTMLEntry(self, htmlString: str, tagName: str, newEntryText: str, additionalAttrs: Dict[str, str]) -> Tuple[bool, str]:
        """Appends a new element <'tagName'> into the 'htmlString' body, with the attributes in 'attributes'. Returns whether the entry already existed in the htmlString, and the updated htmlString."""

        soup = BeautifulSoup(htmlString, "html.parser")

        if soup.find(tagName, string=newEntryText):
            return True, ""

        newEntry = soup.new_tag(tagName)
        for attrName, attrValue in additionalAttrs.items():
            newEntry[attrName] = attrValue
        newEntry.string = newEntryText

        soup.html.body.append(newEntry)

        return False, self.__prettifyHTML(soup)

    def removeHTMLEntry(self, htmlString: str, tagName: str, entryText: str) -> Tuple[bool, str]:
        """Removes the element identified by a 'tagName' and 'entryText' from the 'htmlString'. Returns whether the entry already existed in the htmlString, and the updated htmlString."""

        soup = BeautifulSoup(htmlString, "html.parser")

        tagToRemove = soup.find(tagName, string=entryText)
        if not tagToRemove:
            return False, htmlString

        tagToRemove.decompose()

        return True, self.__prettifyHTML(soup)

    def __addZipsOrTarsToEntries(self, zipAndTarsDict: Dict[str, str], originalSoup: BeautifulSoup, aEntriesOutput: List[bs4Element.Tag]):
        for name, ext in zipAndTarsDict.items():

            aEntry: str = originalSoup.find("a", string=name + "." + ext)
            if not aEntry is None:
                aEntriesOutput.append(aEntry)

    def __isDevFile(self, fileName: str) -> bool:
        if re.search(rf"\.dev\d+", fileName):
            return True
        return False

    def __isRCFile(self, fileName: str) -> bool:
        if re.search(rf"\d+rc\d+", fileName):
            return True
        return False

    def __isWheel(self, fileName: str) -> bool:
        if re.search(rf".whl", fileName):
            return True
        return False

    def __isPlatformSpecificWheel(self, fileName: str) -> bool:
        if not self.__isWheel(fileName):
            return False

        if re.search(rf"-any.whl", fileName):
            return False

        return True

    def _printFilteredOutFiles(self, nonFilteredEntries: bs4Element.ResultSet[bs4Element.Tag], filteredEntries: List[bs4Element.Tag]):
        filteredCounter = 0
        print("Filtered out entries:")
        for nonFilteredEntry in nonFilteredEntries:
            if not nonFilteredEntry in filteredEntries:
                print(nonFilteredEntry.string)

                filteredCounter += 1
        if filteredCounter == 0: print("-")
        print("\n\tIF YOU OBSERVED SOME ENTRY THAT SHOULD NOT BE FILTERED OUT, CHECK YOUR CURRENT COMMAND OPTIONS (--help) AND THE WHEEL FILTERS WITH COMMAND 'config'.\n")

    def filterInHTML(self, htmlContent: str, regexZIPAndTars: str) -> str:
        """Returns an HTML that keeps all those <a> entries from 'htmlContent' that follow all the specified set of rules (command flags and wheels filtering system stated in settings/wheelFilters.py). The ones that do not match any are filtered out."""

        outputSoup = BeautifulSoup(self._baseHTML_fromScratch, "html.parser")

        zipAndTarsDict: Dict[str, str] = dict()

        originalSoup = BeautifulSoup(htmlContent, "html.parser")
        aEntries: bs4Element.ResultSet[bs4Element.Tag] = originalSoup.find_all("a")

        aEntriesOutput: List[bs4Element.Tag] = list()
        for aEntry in aEntries:
            if (self.__isDevFile(aEntry.string) and not self.includeDevs) or (self.__isRCFile(aEntry.string) and not self.includeRCs):
                continue

            if self.__isPlatformSpecificWheel(aEntry.string) and not self.includePlatformSpecific:
                continue

            if not self.onlySources and self._wheelsManager.isValidWheel(aEntry.string):
                aEntriesOutput.append(aEntry)
            else:
                reSult = re.match(regexZIPAndTars, aEntry.string)
                if reSult:
                    reSultName: str = reSult.group(1)
                    reSultExtension: str = reSult.group(2)

                    if reSultExtension == "zip":
                        zipAndTarsDict[reSultName] = reSultExtension
                    else:
                        if not reSultName in zipAndTarsDict.keys():
                            zipAndTarsDict[reSultName] = reSultExtension

        self.__addZipsOrTarsToEntries(zipAndTarsDict, originalSoup, aEntriesOutput)

        if self.printAllFileNames:
            self._printFilteredOutFiles(aEntries, aEntriesOutput)

        for aEntry in aEntriesOutput:
            outputSoup.html.body.append(aEntry)

        return self.__prettifyHTML(outputSoup)

    def getHRefsList(self, pypiPackageHTML: str) -> Dict[str, str]:
        """Returns a dict of the href attributes appearing in 'pypiPackageHTML', the package's name in the key."""

        soup = BeautifulSoup(pypiPackageHTML, "html.parser")

        resultingDict: Dict[str, str] = dict()
        for a in soup.find_all("a", href=True):
            resultingDict[str(a.string)] = a["href"]

        return resultingDict
