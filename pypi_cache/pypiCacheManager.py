#! /usr/bin/python
from io import TextIOWrapper
import os

import argparse
from site import addpackage
from unittest import registerResult, result
from urllib import request
import re

from bs4 import BeautifulSoup
import wheel_filename

from typing import Tuple, Dict


class HTMLManager:

    """
    A class used for builing and managing the HTML files needed for the PyPI local repository.
    """

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

    def __getWheelsSetOfRules(self) -> Dict[str, list]:

        # ToDo: get the set of rules for the wheels filtering from the settings¿? maybe the settings has been already read at the beginning of the execution.

        return None

    def __isValidWheel(self, entry: str, whlRules: dict) -> bool:
        try:
            parsedWheel = wheel_filename.parse_wheel_filename(entry)

            # ToDo: build a command "config" to set a file with the key words that we will use to filter out a wheel by a certain field (using the ones at 'parsedWheel')

            return True
        except wheel_filename.InvalidFilenameError:
            return False

    def __addZipsOrTarsToEntries(self, zipAndTarsDict: dict, originalSoup: BeautifulSoup, aEntriesOutput: list):
        for name, ext in zipAndTarsDict.items():

            aEntry: str = originalSoup.find("a", string=name + "." + ext)
            if not aEntry is None:
                aEntriesOutput.append(aEntry)

    def filterInHTML(self, htmlContent: str, regexZIPAndTars: str, packageName: str) -> str:
        """Keeps <a> entries in 'htmlContent' that are .whl or zip (or tar.gz, in case it doesn't exists a homonym .zip). The wheel must follow a particular set of rules. The ones that do not match any are filtered out."""

        whlRules: Dict[str, list] = self.__getWheelsSetOfRules()

        outputSoup = BeautifulSoup(self._baseHTML_fromScratch, "html.parser")
        headEntry = outputSoup.new_tag("h1")
        headEntry.string = "Links for " + packageName
        outputSoup.html.body.append(headEntry)

        zipAndTarsDict: Dict[str, str] = dict()

        originalSoup = BeautifulSoup(htmlContent, "html.parser")
        aEntries: list = originalSoup.find_all("a")

        aEntriesOutput: list = list()
        for aEntry in aEntries:
            if self.__isValidWheel(aEntry.string, whlRules):
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
            outputSoup.html.body.append(aEntry)

        return self.__prettifyHTML(outputSoup)

    def getHRefsList(self, pypiPackageHTML: str) -> dict:
        """Returns a dict of the href attributes appearing in 'pypiPackageHTML', the package's name in the key."""

        soup = BeautifulSoup(pypiPackageHTML, "html.parser")

        resultingDict: dict = dict()
        for a in soup.find_all("a", href=True):
            resultingDict[a.string] = a["href"]

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
        self._pypiLocalPath: str

        self._packageLocalFileName: str

        self._regexZIPAndTars: str

    @property
    def packageName(self):
        return self._packageName

    @property
    def pypiLocalPath(self):
        return self._pypiLocalPath

    @property
    def packageLocalFileName(self):
        return self._packageLocalFileName

    @packageName.setter
    def packageName(self, new_PackageName: str):
        self._packageName = new_PackageName

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

    def __downloadFilesInLocalPath(self, packagesToDownload: dict, outputMessage: str, indexHTML: str = "", addPackageFilesToIndex: bool = False) -> Tuple[str, str]:
        updatedHTML: str = indexHTML

        if len(packagesToDownload) == 0:
            outputMessage += "No new packages in the remote to download."
        else:
            outputMessage += str(len(packagesToDownload)) + " new packages available.\n"

        packageCounter: int = 1
        for fileName, fileLink in packagesToDownload.items():
            outputMessage += "Downloading package #" + str(packageCounter) + ": '" + fileName + "'...\n"
            # ToDo: implement a retry/resume feature in case the .urlretrieve fails
            request.urlretrieve(fileLink, self.packageLocalFileName + fileName)

            if addPackageFilesToIndex:
                _, updatedHTML = self._htmlManager.insertAEntry(updatedHTML, fileLink, fileName)

            packageCounter = packageCounter + 1

        return outputMessage, updatedHTML

    ### 'Add' command methods ###

    def __initRegexs(self):
        self._regexZIPAndTars = "^(" + self.packageName + ".*)\.(zip|tar.gz)$"

    def parseScriptArguments(self, args: argparse.ArgumentParser):
        """Parse the incoming arguments. A packageName and and pypiLocalPath are expected. Besides, it initializes derived class attributes."""

        self.packageName = args.packageName
        self.pypiLocalPath = args.pypiLocalPath

        self.packageLocalFileName = (self.pypiLocalPath + "/" + self.packageName + "/").replace("\\", "/")

        self.__initRegexs()

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

        entryAlreadyExists, htmlUpdated = self._htmlManager.insertAEntry(htmlContent, self.pypiLocalPath + self.packageName + "/", self.packageName)

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

    def addPackage(self) -> str:
        """Downloads all the files for the required package 'packageName', i.e. all the .whl, the .zip and the .tar.gz if necessary."""

        pypiPackageHTML: str = request.urlopen(self._remotePypiBaseDir + self.packageName).read().decode("utf-8")

        pypiPackageHTML: str = self._htmlManager.filterInHTML(pypiPackageHTML, self._regexZIPAndTars, self.packageName)
        packageHTML_file = open(self.packageLocalFileName + self._packageHTMLFileName, "w")
        packageHTML_file.write(pypiPackageHTML)
        packageHTML_file.close()

        linksToDownload: dict = self._htmlManager.getHRefsList(pypiPackageHTML)

        resultingMessage: str = ""
        resultingMessage, _ = self.__downloadFilesInLocalPath(linksToDownload, resultingMessage)

        return resultingMessage

    ### 'Update' command methods ###

    def isAlreadyAdded(self) -> bool:
        """Returns whether the self._packageName already exists in the self._pypiLocalPath."""

        indexHTMLFile = open(self.pypiLocalPath + "/" + self._baseHTMLFileName, "r")
        baseHTMLStr: str = indexHTMLFile.read()

        packagesDict: dict = self._htmlManager.getHRefsList(baseHTMLStr)

        if self.packageName in packagesDict:
            return True
        else:
            return False

    def __checkPackagesInLocalButNotInRemote(self, remoteIndexHRefs: Dict[str, str], localIndexHRefs: Dict[str, str]) -> str:
        additionalPackagesMessage: str = ""
        for localPackageName, localPackageURL in localIndexHRefs.items():
            if not localPackageName in remoteIndexHRefs:
                if additionalPackagesMessage == "":
                    additionalPackagesMessage += "Packages in the local but not in the remote (check filter settings):\n"
                additionalPackagesMessage += localPackageName + "\n"

        return additionalPackagesMessage

    def __getNewPackagesInRemote(self, remoteIndexHRefs: Dict[str, str], localIndexHRefs: Dict[str, str]) -> Tuple[dict, str]:
        resultingDict: dict = dict()

        for remotePackageName, remotePackageURL in remoteIndexHRefs.items():
            if not remotePackageName in localIndexHRefs:
                resultingDict[remotePackageName] = remotePackageURL

        additionalPackagesMessage: str = self.__checkPackagesInLocalButNotInRemote(remoteIndexHRefs, localIndexHRefs)

        return resultingDict, additionalPackagesMessage

    def __overwritePackageIndexFile(self, textToWrite: str):
        with open(self.packageLocalFileName + self._packageHTMLFileName, "r+") as pypiLocalIndexFile:
            self.__writeFileFromTheStart(pypiLocalIndexFile, textToWrite)

    def synchronizeWithRemote(self) -> str:
        """Synchronize the self.packageName against the PyPI remote repository. It adds the new available packages to the packageName/index.html and download them. Assumes the folders exists."""

        pypiRemoteIndex: str = request.urlopen(self._remotePypiBaseDir + self.packageName).read().decode("utf-8")
        with open(self.packageLocalFileName + self._packageHTMLFileName, "r") as pypiLocalIndexFile:
            pypiLocalIndex = pypiLocalIndexFile.read()

        pypiRemoteIndexFiltered: str = self._htmlManager.filterInHTML(pypiRemoteIndex, self._regexZIPAndTars, self.packageName)

        remoteIndexHRefs: Dict[str, str] = self._htmlManager.getHRefsList(pypiRemoteIndexFiltered)
        localIndexHRefs: Dict[str, str] = self._htmlManager.getHRefsList(pypiLocalIndex)
        newPackagesToDownload, warningMessage = self.__getNewPackagesInRemote(remoteIndexHRefs, localIndexHRefs)

        resultingMessage: str = ""
        if warningMessage != "":
            resultingMessage += "WARNING! " + warningMessage + "\n"

        resultingMessage, pypiLocalIndexUpdated = self.__downloadFilesInLocalPath(newPackagesToDownload, resultingMessage, pypiLocalIndex, True)

        self.__overwritePackageIndexFile(pypiLocalIndexUpdated)

        return resultingMessage
