#! /usr/bin/python
from io import TextIOWrapper
import os

import argparse
import time
from typing import Tuple, Dict

import requests

from pypickup.utils.htmlManager import HTMLManager


class LocalPyPIController:

    """
    A class to download a desired package from the PyPI remote repository into a local one as a mirror.
    """

    _htmlManager = HTMLManager()

    _baseHTMLFileName: str = "index.html"
    _packageHTMLFileName: str = "index.html"
    _remotePypiBaseDir: str = "https://pypi.org/simple/"

    _regexZIPAndTars = "^(.*)\.(zip|tar.gz|tar.bz2|tar.xz|tar.Z|tar)$"

    def __init__(self):
        self._packageName: str
        self._pypiLocalPath: str

        self._onlySources: bool
        self._includeDevs: bool
        self._includeRCs: bool
        self._includePlatformSpecific: bool

        self._baseHTMLFilePath: str
        self._packageLocalFileName: str

    @property
    def packageName(self):
        return self._packageName

    @property
    def pypiLocalPath(self):
        return self._pypiLocalPath

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

    @property
    def packageLocalFileName(self):
        return self._packageLocalFileName

    @property
    def baseHTMLFilePath(self):
        return self._baseHTMLFilePath

    @property
    def remotePyPIRepository(self):
        return self._remotePypiBaseDir

    @packageName.setter
    def packageName(self, new_PackageName: str):
        self._packageName = new_PackageName

    @pypiLocalPath.setter
    def pypiLocalPath(self, new_PyPiLocalPath: str):
        self._pypiLocalPath = new_PyPiLocalPath

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

    @packageLocalFileName.setter
    def packageLocalFileName(self, new_PackageLocalFileName: str):
        self._packageLocalFileName = new_PackageLocalFileName

    @baseHTMLFilePath.setter
    def baseHTMLFilePath(self, new_baseHTMLFilePath: str):
        self._baseHTMLFilePath = new_baseHTMLFilePath

    ### Common methods ###

    def parseScriptArguments(self, args: argparse.ArgumentParser):
        """Parse the incoming arguments. A packageName and and pypiLocalPath are expected. Besides, it initializes derived class attributes."""

        self.packageName = args.packageName
        self.pypiLocalPath = args.pypiLocalPath

        self.onlySources = args.onlySources
        self.includeDevs = args.includeDevs
        self.includeRCs = args.includeRCs
        self.includePlatformSpecific = args.includePlatformSpecific

        self.pypiLocalPath = self.pypiLocalPath.replace("\\", "/")

        # ToDo: refactor these 2 following names
        self.baseHTMLFilePath = os.path.join(self.pypiLocalPath, self._baseHTMLFileName)
        self.packageLocalFileName = os.path.join(self.pypiLocalPath, self.packageName) + "/"

        self._htmlManager.setFlags(self.onlySources, self.includeDevs, self.includeRCs, self.includePlatformSpecific)

        if (self.includeDevs or self.includeRCs) and self._htmlManager.areWheelFiltersEnabled():
            print("\tWARNING! Development releases (devX) or release candidates (RCs) flags are enabled, as well as the wheel filters, so they could be discarded anyway. This is caused because of the order of application: (1st) flags, (2nd) wheel filters.")
            print("\tPLEASE, CHECK OUT YOUR WHEEL FILTERS.")

    def __getLink(self, linkURL: str, verbose: bool = True, retries: int = 10, timeBetweenRetries: float = 0.5) -> Tuple[bool, str, bytes]:
        response: requests.Response = requests.Response()

        retriesCounter: int = retries
        again: bool = True
        while again:
            retriesCounter -= 1
            if retriesCounter == 0: break

            try:
                response = requests.get(linkURL, timeout=5)
                response.raise_for_status()

                again = False
            except:
                again = True

                if verbose: 
                    print("Trying again...\t(" + linkURL + ")")
                time.sleep(timeBetweenRetries)

        if response.status_code != 200:
            if retries > 1 and verbose:
                print("Last try on...\t(" + linkURL + ")")

            try:
                response = requests.get(linkURL, timeout=5)
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
            print(str(len(packagesToDownload)) + " new packages available in the remote.")

        packageCounter: int = 1
        actuallyDownloadedPackages: int = 0
        for fileName, fileLink in packagesToDownload.items():
            print("Downloading package #" + str(packageCounter) + ": '" + fileName + "'...")
            ok, status, content = self.__getLink(fileLink)
            if not ok:
                print("\nUNABLE TO DOWNLOAD PACKAGE '" + fileName + "' (URL: " + fileLink + ")\n\tSTATUS: " + status + "\n")
            else:
                with open(self.packageLocalFileName + fileName, "wb") as f:
                    f.write(content)

                updatedHTML = self.__addPackageToIndex(updatedHTML, file, "./" + fileName, fileName)

                actuallyDownloadedPackages += 1

            packageCounter += 1

        print()
        print(str(actuallyDownloadedPackages) + "/" + str(len(packagesToDownload)) + " downloaded.")

    ### 'Add' command methods ###

    def validPackageName(self) -> bool:
        """Checks whether the package link exists or not. If not, it returns False. True otherwise."""

        ok, status, _ = self.__getLink(self._remotePypiBaseDir + self.packageName, False)
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

        self.__createBaseHTMLFileIfNeeded(self.baseHTMLFilePath)

    def __addEntryToBaseHTMLFile(self) -> bool:
        baseHTML_file = open(self.baseHTMLFilePath, "r+")
        htmlContent: str = baseHTML_file.read()

        if len(htmlContent) == 0:
            htmlContent = self._htmlManager.getBaseHTML()

        entryAlreadyExists, htmlUpdated = self._htmlManager.insertHTMLEntry(htmlContent, "a", {"href": "./" + self.packageName}, self.packageName)

        needToDownloadFiles: bool = False
        if not entryAlreadyExists:
            self.__writeFileFromTheStart(baseHTML_file, htmlUpdated)

            needToDownloadFiles = True

        baseHTML_file.close()

        return needToDownloadFiles

    def canAddNewPackage(self) -> bool:
        """Adds the self.packageName package to the base HTML index, if not exists already. If it does, it returns False, True otherwise."""

        needToDownloadFiles: bool = self.__addEntryToBaseHTMLFile()

        return needToDownloadFiles

    def addPackage(self):
        """Downloads all the files for the required package 'packageName', i.e. all the .whl, the .zip and the .tar.gz if necessary."""

        ok, status, pypiPackageHTML = self.__getLink(self._remotePypiBaseDir + self.packageName)
        if not ok:
            print(status)
        else:
            pypiPackageHTMLStr: str = pypiPackageHTML.decode("utf-8")

        pypiPackageHTMLStr = self._htmlManager.filterInHTML(pypiPackageHTMLStr, self._regexZIPAndTars)
        linksToDownload: Dict[str, str] = self._htmlManager.getHRefsList(pypiPackageHTMLStr)

        packageBaseHTML: str = self._htmlManager.getBaseHTML()
        _, packageBaseHTML = self._htmlManager.insertHTMLEntry(packageBaseHTML, "h1", {}, "Links for " + self.packageName)
        with open(self.packageLocalFileName + self._packageHTMLFileName, "w") as packageHTML_file:
            packageHTML_file.write(packageBaseHTML)

            self.__downloadFilesInLocalPath(linksToDownload, packageBaseHTML, packageHTML_file)

    ### 'Update' command methods ###

    def isAlreadyAdded(self) -> bool:
        """Returns whether the self._packageName already exists in the self._pypiLocalPath. If the local repository has not even been created previously, returns False."""

        if not os.path.exists(self.baseHTMLFilePath):
            return False

        indexHTMLFile = open(self.baseHTMLFilePath, "r")
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

        pypiRemoteIndexFiltered: str = self._htmlManager.filterInHTML(pypiRemoteIndexStr, self._regexZIPAndTars)

        # ToDo: fix the bug happening if the local repo hast the wheels&src but the update method has enabled the -s option which means we only want the source. the warning message would not apply yet
        remoteIndexHRefs: Dict[str, str] = self._htmlManager.getHRefsList(pypiRemoteIndexFiltered)
        localIndexHRefs: Dict[str, str] = self._htmlManager.getHRefsList(pypiLocalIndex)
        newPackagesToDownload: Dict[str, str] = self.__getNewPackagesInRemote(remoteIndexHRefs, localIndexHRefs)

        with open(self.packageLocalFileName + self._packageHTMLFileName, "r+") as pypiLocalIndexFile:
            self.__downloadFilesInLocalPath(newPackagesToDownload, pypiLocalIndex, pypiLocalIndexFile)

    def removePackage(self):
        """Removes the self.packageName from the local repository. Assumes it exists."""
        
        return None