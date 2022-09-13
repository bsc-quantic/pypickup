#! /usr/bin/python
from io import TextIOWrapper
import os

import argparse
import requests
from typing import Tuple, Dict

from pypi_cache.utils.htmlManager import HTMLManager


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

    def __getLink(self, linkURL: str) -> Tuple[bool, str, bytes]:
        response: requests.Response = requests.Response()
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

    def __writeFileFromTheStart(self, file: TextIOWrapper, textToWrite: str):
        file.seek(0)
        file.truncate(0)
        file.write(textToWrite)

    def __addPackageToIndex(self, indexHTML: str, file: TextIOWrapper, href: str, entryText: str) -> str:
        _, updatedHTML = self._htmlManager.insertHTMLEntry(indexHTML, "a", {"href": href}, entryText)
        self.__writeFileFromTheStart(file, updatedHTML)

        return updatedHTML

    def __downloadFilesInLocalPath(self, packagesToDownload: Dict[str, str], indexHTML: str, file: TextIOWrapper):
        updatedHTML: str = indexHTML

        if len(packagesToDownload) == 0:
            print("No new packages in the remote to download.")
        else:
            print(str(len(packagesToDownload)) + " new packages available.")

        packageCounter: int = 1
        actuallyDownloadedPackages: int = 0
        for fileName, fileLink in packagesToDownload.items():
            print("Downloading package #" + str(packageCounter) + ": '" + fileName + "'...")
            # ToDo: implement a retry/resume feature in case the .urlretrieve fails
            ok, status, content = self.__getLink(fileLink)
            if not ok:
                print("Error downloading link: " + fileLink + " (status: " + status + ")")
            else:
                with open(self.packageLocalFileName + fileName, "wb") as f:
                    f.write(content)

                updatedHTML = self.__addPackageToIndex(updatedHTML, file, fileLink, fileName)

                actuallyDownloadedPackages += 1

            packageCounter += 1

        print()
        print(str(actuallyDownloadedPackages) + "/" + str(len(packagesToDownload)) + " downloaded.")

    ### 'Add' command methods ###

    def __initRegexs(self):
        self._regexZIPAndTars = "^(.*)\.(zip|tar.gz|tar.bz2|tar.xz|tar.Z|tar)$"

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

        ok, status, _ = self.__getLink(self._remotePypiBaseDir + self.packageName)
        if not ok:
            print(status)
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

        entryAlreadyExists, htmlUpdated = self._htmlManager.insertHTMLEntry(htmlContent, "a", {"href": "./" + self.packageName}, self.packageName)

        needToDownloadFiles: bool = False
        if not entryAlreadyExists:
            # ToDo: refactor these lines with the method __writeFileFromTheStart()
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
        linksToDownload: Dict[str, str] = self._htmlManager.getHRefsList(pypiPackageHTMLStr)

        packageBaseHTML: str = self._htmlManager.getBaseHTML()
        _, packageBaseHTML = self._htmlManager.insertHTMLEntry(packageBaseHTML, "h1", {}, "Links for " + self.packageName)
        with open(self.packageLocalFileName + self._packageHTMLFileName, "w") as packageHTML_file:
            packageHTML_file.write(packageBaseHTML)

            self.__downloadFilesInLocalPath(linksToDownload, packageBaseHTML, packageHTML_file)

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

        with open(self.packageLocalFileName + self._packageHTMLFileName, "w") as pypiLocalIndexFile:
            self.__downloadFilesInLocalPath(newPackagesToDownload, pypiLocalIndex, pypiLocalIndexFile)
