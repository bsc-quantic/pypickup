#! /usr/bin/python
from genericpath import isdir
from io import TextIOWrapper
from multiprocessing.sharedctypes import Value
import os

import argparse
import shutil
from wsgiref.util import shift_path_info
import requests
import re
from typing import Tuple, Dict, List, Union

from bs4 import BeautifulSoup, element as bs4Element
import wheel_filename
from multimethod import multimethod

from pypi_cache.settings.wheelFilters import WheelsConfig


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
                else:
                    print('Wheel ignored because of filters: "' + wheelName + '".')

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
        return None

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

    def insertAEntry(self, htmlString: str, hrefURL: str, newEntryText: str) -> Tuple[bool, str]:
        """Appends a new element <a> into the 'htmlString' body, with the 'hrefURL' and the 'newEntryText' parameters. Returns whether the entry already exists in the htmlString, and the updated htmlString."""

        soup = BeautifulSoup(htmlString, "html.parser")

        if soup.find("a", string=newEntryText):
            return True, ""

        newEntry = soup.new_tag("a", href=hrefURL)
        newEntry.string = newEntryText
        soup.html.body.append(newEntry)

        return False, self.__prettifyHTML(soup)

    def __addZipsOrTarsToEntries(self, zipAndTarsDict: Dict[str, str], originalSoup: BeautifulSoup, aEntriesOutput: List[bs4Element.Tag]):
        for name, ext in zipAndTarsDict.items():

            aEntry: str = originalSoup.find("a", string=name + "." + ext)
            if not aEntry is None:
                aEntriesOutput.append(aEntry)

    def filterInHTML(self, htmlContent: str, regexZIPAndTars: str, packageName: str, onlySources: bool) -> str:
        """Keeps <a> entries in 'htmlContent' that are .whl or zip (or tar.gz, in case it doesn't exists a homonym .zip). The wheel must follow a particular set of rules. The ones that do not match any are filtered out."""

        outputSoup = BeautifulSoup(self._baseHTML_fromScratch, "html.parser")
        headEntry = outputSoup.new_tag("h1")
        headEntry.string = "Links for " + packageName
        outputSoup.html.body.append(headEntry)

        zipAndTarsDict: Dict[str, str] = dict()

        originalSoup = BeautifulSoup(htmlContent, "html.parser")
        aEntries: bs4Element.ResultSet[bs4Element.Tag] = originalSoup.find_all("a")

        aEntriesOutput: List[bs4Element.Tag] = list()
        for aEntry in aEntries:
            if not onlySources and self._wheelsManager.isValidWheel(aEntry.string):
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

        for aEntry in aEntriesOutput:
            # ToDo: the href for the aEntry must be the URL or the local path to the wheel/zip file?
            outputSoup.html.body.append(aEntry)

        return self.__prettifyHTML(outputSoup)

    def getHRefsList(self, pypiPackageHTML: str) -> Dict[str, str]:
        """Returns a dict of the href attributes appearing in 'pypiPackageHTML', the package's name in the key."""

        soup = BeautifulSoup(pypiPackageHTML, "html.parser")

        resultingDict: Dict[str, str] = dict()
        for a in soup.find_all("a", href=True):
            resultingDict[str(a.string)] = a["href"]

        return resultingDict


class LocalPyPIController:

    """
    A class to download a desired package from the PyPI remote repository into a local one as a mirror.
    """

    _htmlManager = HTMLManager()

    _baseHTMLFileName: str = "index.html"
    _packageHTMLFileName: str = "index.html"
    _remotePypiBaseDir: str = "https://pypi.org/simple/"

    def __init__(self):
        self._packageName: str
        self._onlySources: bool
        self._pypiLocalPath: str

        self._packageLocalFileName: str

        self._regexZIPAndTars: str

    @property
    def packageName(self):
        return self._packageName

    @property
    def onlySources(self):
        return self._onlySources

    @property
    def pypiLocalPath(self):
        return self._pypiLocalPath

    @property
    def packageLocalFileName(self):
        return self._packageLocalFileName

    @property
    def remotePyPIRepository(self):
        return self._remotePypiBaseDir

    @packageName.setter
    def packageName(self, new_PackageName: str):
        self._packageName = new_PackageName

    @onlySources.setter
    def onlySources(self, new_onlySources: bool):
        self._onlySources = new_onlySources

    @pypiLocalPath.setter
    def pypiLocalPath(self, new_PyPiLocalPath: str):
        self._pypiLocalPath = new_PyPiLocalPath

    @packageLocalFileName.setter
    def packageLocalFileName(self, new_PackageLocalFileName: str):
        self._packageLocalFileName = new_PackageLocalFileName

    ### Common methods ###

    def __writeFileFromTheStart(self, file: TextIOWrapper, textToWrite: str):
        file.seek(0)
        file.truncate(0)
        file.write(textToWrite)

    def __getLink(self, linkURL: str) -> Tuple[bool, str, bytes]:
        try:
            response = requests.get(linkURL)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            return False, "HTTP Error: " + str(errh), response.content
        except requests.exceptions.ConnectionError as errc:
            return False, "Error Connecting: " + str(errc), response.content
        except requests.exceptions.Timeout as errt:
            return False, "Timeout Error: " + str(errt), response.content
        except requests.exceptions.RequestException as err:
            return False, "OOps: Something Else: " + str(err), response.content

        return True, "200 OK", response.content

    def __downloadFilesInLocalPath(self, packagesToDownload: Dict[str, str], indexHTML: str = "", addPackageFilesToIndex: bool = False) -> str:
        updatedHTML: str = indexHTML

        if len(packagesToDownload) == 0:
            print("No new packages in the remote to download.")
        else:
            print(str(len(packagesToDownload)) + " new packages available.")

        packageCounter: int = 1
        for fileName, fileLink in packagesToDownload.items():
            print("Downloading package #" + str(packageCounter) + ": '" + fileName + "'...")
            # ToDo: implement a retry/resume feature in case the .urlretrieve fails
            ok, status, content = self.__getLink(fileLink)
            with open(self.packageLocalFileName + fileName, "wb") as f:
                f.write(content)

            if addPackageFilesToIndex:
                _, updatedHTML = self._htmlManager.insertAEntry(updatedHTML, fileLink, fileName)

            packageCounter = packageCounter + 1

        return updatedHTML

    ### 'Add' command methods ###

    def __initRegexs(self):
        self._regexZIPAndTars = "^(" + self.packageName + ".*)\.(zip|tar.gz)$"

    def parseScriptArguments(self, args: argparse.ArgumentParser):
        """Parse the incoming arguments. A packageName and and pypiLocalPath are expected. Besides, it initializes derived class attributes."""

        self.packageName = args.packageName
        self.onlySources = args.onlySources
        self.pypiLocalPath = args.pypiLocalPath

        self.pypiLocalPath = self.pypiLocalPath.replace("\\", "/")

        self.packageLocalFileName = os.path.join(self.pypiLocalPath, self.packageName) + "/"

        self.__initRegexs()

    def validPackageName(self) -> bool:
        """Checks whether the package link exists or not. If not, it returns False. True otherwise."""
        
        ok, _, _ = self.__getLink(self._remotePypiBaseDir + self.packageName)
        if not ok:
            return False
        
        return True

    def __createDirIfNeeded(self, directory: str):
        if not os.path.isdir(directory):
            os.mkdir(directory)

    def __createBaseHTMLFileIfNeeded(self, baseHTMLFilePath: str):
        if not os.path.exists(baseHTMLFilePath):
            open(baseHTMLFilePath, "a").close()

    def initLocalRepo(self):
        """Initializes the local repository creating the needed directories (if not exist) and updating accordingly the base HTML."""

        self.__createDirIfNeeded(self.pypiLocalPath)
        self.__createDirIfNeeded(self.packageLocalFileName)

        baseHTMLFilePath: str = self.pypiLocalPath + "/" + self._baseHTMLFileName
        self.__createBaseHTMLFileIfNeeded(baseHTMLFilePath)

    def __addEntryToBaseHTMLFile(self, baseHTMLFilePath: str) -> bool:
        baseHTML_file = open(baseHTMLFilePath, "r+")
        htmlContent: str = baseHTML_file.read()

        if len(htmlContent) == 0:
            htmlContent = self._htmlManager.getBaseHTML()

        entryAlreadyExists, htmlUpdated = self._htmlManager.insertAEntry(htmlContent, self.packageLocalFileName, self.packageName)

        needToDownloadFiles: bool = False
        if not entryAlreadyExists:
            baseHTML_file.seek(0)
            baseHTML_file.truncate()
            baseHTML_file.write(htmlUpdated)

            needToDownloadFiles = True

        baseHTML_file.close()

        return needToDownloadFiles

    def canAddNewPackage(self) -> bool:
        """Adds the self.packageName package to the base HTML index, if not exists already. If it does, it returns False, True otherwise."""

        baseHTMLFilePath: str = self.pypiLocalPath + "/" + self._baseHTMLFileName
        needToDownloadFiles: bool = self.__addEntryToBaseHTMLFile(baseHTMLFilePath)

        return needToDownloadFiles

    def addPackage(self):
        """Downloads all the files for the required package 'packageName', i.e. all the .whl, the .zip and the .tar.gz if necessary."""

        ok, status, pypiPackageHTML = self.__getLink(self._remotePypiBaseDir + self.packageName)
        if not ok:
            print(status)
        else:
            pypiPackageHTMLStr: str = pypiPackageHTML.decode("utf-8")

        pypiPackageHTMLStr = self._htmlManager.filterInHTML(pypiPackageHTMLStr, self._regexZIPAndTars, self.packageName, self.onlySources)
        packageHTML_file = open(self.packageLocalFileName + self._packageHTMLFileName, "w")
        packageHTML_file.write(pypiPackageHTMLStr)
        packageHTML_file.close()

        linksToDownload: Dict[str, str] = self._htmlManager.getHRefsList(pypiPackageHTMLStr)

        self.__downloadFilesInLocalPath(linksToDownload)

    ### 'Update' command methods ###

    def isAlreadyAdded(self) -> bool:
        """Returns whether the self._packageName already exists in the self._pypiLocalPath."""

        indexHTMLFile = open(self.pypiLocalPath + "/" + self._baseHTMLFileName, "r")
        baseHTMLStr: str = indexHTMLFile.read()

        packagesDict: Dict[str, str] = self._htmlManager.getHRefsList(baseHTMLStr)

        if self.packageName in packagesDict:
            return True
        else:
            return False

    def __checkPackagesInLocalButNotInRemote(self, remoteIndexHRefs: Dict[str, str], localIndexHRefs: Dict[str, str]) -> str:
        additionalPackagesMessage: str = ""
        for localPackageName, localPackageURL in localIndexHRefs.items():

            if not localPackageName in remoteIndexHRefs:
                if not (self.onlySources and os.path.splitext(localPackageName)[1] == ".whl"):
                    if additionalPackagesMessage == "":
                        additionalPackagesMessage += "Packages in the local but not in the remote (check filter settings):\n"
                    additionalPackagesMessage += localPackageName + "\n"

        return additionalPackagesMessage

    def __getNewPackagesInRemote(self, remoteIndexHRefs: Dict[str, str], localIndexHRefs: Dict[str, str]) -> Dict[str, str]:
        resultingDict: Dict[str, str] = dict()

        for remotePackageName, remotePackageURL in remoteIndexHRefs.items():
            if not remotePackageName in localIndexHRefs:
                resultingDict[remotePackageName] = remotePackageURL

        additionalPackagesMessage: str = self.__checkPackagesInLocalButNotInRemote(remoteIndexHRefs, localIndexHRefs)
        if additionalPackagesMessage != "":
            print("WARNING! " + additionalPackagesMessage)

        return resultingDict

    def __overwritePackageIndexFile(self, textToWrite: str):
        with open(self.packageLocalFileName + self._packageHTMLFileName, "r+") as pypiLocalIndexFile:
            self.__writeFileFromTheStart(pypiLocalIndexFile, textToWrite)

    def synchronizeWithRemote(self):
        """Synchronize the self.packageName against the PyPI remote repository. It adds the new available packages to the packageName/index.html and download them. Assumes the folders exists."""

        ok, status, pypiRemoteIndex = self.__getLink(self._remotePypiBaseDir + self.packageName)
        if not ok:
            print(status)
        else:
            pypiRemoteIndexStr: str = pypiRemoteIndex.decode("utf-8")

        with open(self.packageLocalFileName + self._packageHTMLFileName, "r") as pypiLocalIndexFile:
            pypiLocalIndex: str = pypiLocalIndexFile.read()

        pypiRemoteIndexFiltered: str = self._htmlManager.filterInHTML(pypiRemoteIndexStr, self._regexZIPAndTars, self.packageName, self.onlySources)

        # ToDo: fix the bug happening if the local repo hast the wheels&src but the update method has enabled the -s option which means we only want the source. the warning message would not apply yet
        remoteIndexHRefs: Dict[str, str] = self._htmlManager.getHRefsList(pypiRemoteIndexFiltered)
        localIndexHRefs: Dict[str, str] = self._htmlManager.getHRefsList(pypiLocalIndex)
        newPackagesToDownload: Dict[str, str] = self.__getNewPackagesInRemote(remoteIndexHRefs, localIndexHRefs)

        pypiLocalIndexUpdated, _ = self.__downloadFilesInLocalPath(newPackagesToDownload, pypiLocalIndex, True)

        self.__overwritePackageIndexFile(pypiLocalIndexUpdated)
