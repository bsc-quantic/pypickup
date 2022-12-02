#! /usr/bin/python
from io import TextIOWrapper
import os
import argparse
import shutil
from typing import Dict, List

from tqdm import tqdm

from pypickup.utils.htmlManager import HTMLManager
from pypickup.utils.networkManager import NetworkManager


class LocalPyPIController:

    """
    A class to download a desired package from the PyPI remote repository into a local one as a mirror.
    """

    _htmlManager = HTMLManager()
    _networkManager = NetworkManager()

    _baseHTMLFileName: str = "index.html"
    _packageHTMLFileName: str = "index.html"
    _remotePypiBaseDir: str = "https://pypi.org/simple/"

    _regexZIPAndTars = r"^(.*)\.(zip|tar.gz|tar.bz2|tar.xz|tar.Z|tar)$"

    _dryRunsTmpDir = "./.pypickup_tmp/"

    def __init__(self):
        self._packageName: str = None
        self._pypiLocalPath: str = None

        self._baseHTMLFileFullName: str = None
        self._packageHTMLFileFullName: str = None
        self._packageLocalPath: str = None

        self._printDefaultConfig: bool = None
        self._printAllFileNames: bool = None
        self._printVerbose: bool = None
        self._showRetries: bool = None

        self._onlySources: bool = None
        self._includeDevs: bool = None
        self._includeRCs: bool = None
        self._includePlatformSpecific: bool = None

        self._dryRun: bool = None

    def __del__(self):
        self._removeDir(self._dryRunsTmpDir, True)

    @property
    def packageName(self):
        return self._packageName

    @property
    def pypiLocalPath(self):
        return self._pypiLocalPath

    @property
    def baseHTMLFileFullName(self):
        return self._baseHTMLFileFullName

    @property
    def packageHTMLFileFullName(self):
        return self._packageHTMLFileFullName

    @property
    def packageLocalPath(self):
        return self._packageLocalPath

    @property
    def remotePyPIRepository(self):
        return self._remotePypiBaseDir

    @property
    def printDefaultConfig(self):
        return self._printDefaultConfig

    @property
    def printAllFileNames(self):
        return self._printAllFileNames

    @property
    def printVerbose(self):
        return self._printVerbose

    @property
    def showRetries(self):
        return self._showRetries

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
    def dryRun(self):
        return self._dryRun

    @packageName.setter
    def packageName(self, new_PackageName: str):
        self._packageName = new_PackageName

        # Propagate changes
        if self._pypiLocalPath == None:
            self._pypiLocalPath = ""

        self.packageLocalPath = os.path.join(self._pypiLocalPath, self._packageName) + "/"
        self.packageHTMLFileFullName = os.path.join(self.packageLocalPath, self._packageHTMLFileName)

    @pypiLocalPath.setter
    def pypiLocalPath(self, new_PyPiLocalPath: str):
        self._pypiLocalPath = new_PyPiLocalPath

        self._pypiLocalPath = self._pypiLocalPath.replace("\\", "/")

        if "/" not in self._pypiLocalPath:
            self._pypiLocalPath = self.pypiLocalPath + "/"

        # Propagate changes
        self.baseHTMLFileFullName = os.path.join(self._pypiLocalPath, self._baseHTMLFileName)

        self.packageLocalPath = os.path.join(self._pypiLocalPath, self.packageName) + "/"
        self.packageHTMLFileFullName = os.path.join(self.packageLocalPath, self._packageHTMLFileName)

    @baseHTMLFileFullName.setter
    def baseHTMLFileFullName(self, new_baseHTMLFileFullName: str):
        self._baseHTMLFileFullName = new_baseHTMLFileFullName

    @packageHTMLFileFullName.setter
    def packageHTMLFileFullName(self, new_packageHTMLFileFullName: str):
        self._packageHTMLFileFullName = new_packageHTMLFileFullName

    @packageLocalPath.setter
    def packageLocalPath(self, new_packageLocalPath: str):
        self._packageLocalPath = new_packageLocalPath

    @printDefaultConfig.setter
    def printDefaultConfig(self, new_printDefaultConfig: bool):
        self._printDefaultConfig = new_printDefaultConfig

    @printAllFileNames.setter
    def printAllFileNames(self, new_printAllFileNames: bool):
        self._printAllFileNames = new_printAllFileNames

    @printVerbose.setter
    def printVerbose(self, new_printVerbose: bool):
        self._printVerbose = new_printVerbose

    @showRetries.setter
    def showRetries(self, new_showRetries: bool):
        self._showRetries = new_showRetries

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

    @dryRun.setter
    def dryRun(self, new_dryRun: bool):
        self._dryRun = new_dryRun

    def _removeDir(self, directory: str, recursively: bool = False):
        if os.path.exists(directory):
            if recursively:
                shutil.rmtree(directory)
            else:
                os.rmdir(directory)

    def parseScriptArguments(self, args: argparse.ArgumentParser):
        """Parse the incoming arguments. A packageName and and pypiLocalPath are expected. Besides, it initializes derived class attributes."""

        self.packageName = str(args.packageName).lower()
        self.pypiLocalPath = args.pypiLocalPath

    def printDefaultConfigIfRequired(self):
        if self.printDefaultConfig:
            print("")
            print("DEFAULT CONFIGURATION VARIABLES:")
            print("\tIndex path (current): " + self.pypiLocalPath)
            print("")
            print("\tBase HTML file: " + self._baseHTMLFileName)
            print("\tPackage HTML file dir: " + self.packageHTMLFileFullName)
            print("\tPython repository : " + self._remotePypiBaseDir)
            print("")
            print("\tWheel filters settings file path: " + self._htmlManager.getWheelFiltersSettingsFilePath())
            print("\tDry runs path: " + self._dryRunsTmpDir)
            print("")
            print("\tIncluded zips and tars: " + self._regexZIPAndTars)
            print("")
            print("\tWheel filters enabled: " + str(self._htmlManager.areWheelFiltersEnabled()))
            print("\t\tUse the 'config' command to get the whole wheel filters configuration.")
            print("")

    def packageExists(self) -> bool:
        """Returns whether the self._packageName already exists in the self._pypiLocalPath. If the local repository has not even been created previously, returns False."""

        if not os.path.exists(self.baseHTMLFileFullName):
            return False

        with open(self.baseHTMLFileFullName, "r") as baseHTMLFile:
            baseHTMLStr: str = baseHTMLFile.read()

        return self._htmlManager.existsHTMLEntry(baseHTMLStr, "a", self.packageName)

    def _writeFileFromTheStart(self, file: TextIOWrapper, textToWrite: str):
        file.seek(0)
        file.truncate(0)
        file.write(textToWrite)

    def __addPackageToIndex(self, indexHTML: str, file: TextIOWrapper, href: str, entryText: str) -> str:
        _, updatedHTML = self._htmlManager.insertHTMLEntry(indexHTML, "a", entryText, {"href": href})
        self._writeFileFromTheStart(file, updatedHTML)

        return updatedHTML

    def _printPackageNamesInHTML(self, packageFiles: List[str], message: str):
        print(message + " [" + str(len(packageFiles)) + "]:")
        for packageName in packageFiles:
            print(packageName)
        if len(packageFiles) == 0:
            print("-")
        print("")

    def _downloadFilesInLocalPath(self, packagesToDownload: Dict[str, str], indexHTML: str, htmlFile: TextIOWrapper, printVerbose: bool = False, showRetries: bool = False):
        updatedHTML: str = indexHTML

        actuallyDownloadedPackages: int = 0

        if len(packagesToDownload) == 0:
            print("No new packages in the remote to download.")
        else:
            print(str(len(packagesToDownload)) + " new packages available in the remote.")

            with tqdm(total=len(packagesToDownload), desc="Download", ncols=100, position=0, leave=True, colour="green") as progressBar:
                for fileName, fileLink in packagesToDownload.items():
                    ok, status, content = self._networkManager.getLink(fileLink, printVerbose=printVerbose, showRetries=showRetries)
                    if not ok:
                        print("\nUNABLE TO DOWNLOAD PACKAGE '" + fileName + "' (URL: " + fileLink + ")\n\tSTATUS: " + status + "\n")
                    else:
                        with open(self.packageLocalPath + fileName, "wb") as f:
                            f.write(content)

                        updatedHTML = self.__addPackageToIndex(updatedHTML, htmlFile, "./" + fileName, fileName)

                        actuallyDownloadedPackages += 1

                    progressBar.update(1)

        print()
        print(str(actuallyDownloadedPackages) + "/" + str(len(packagesToDownload)) + " downloaded.")


class Add(LocalPyPIController):
    def __init__(self):
        LocalPyPIController.__init__(self)

    def parseScriptArguments(self, args: argparse.ArgumentParser):
        LocalPyPIController.parseScriptArguments(self, args)

        # 1. Set all the params we are going to use (let the ones we don't to None):
        self.printDefaultConfig = args.printDefaultConfig
        self.printAllFileNames = args.printAllFileNames
        self.printVerbose = args.printVerbose
        self.showRetries = args.showRetries

        self.onlySources = args.onlySources
        self.includeDevs = args.includeDevs
        self.includeRCs = args.includeRCs
        self.includePlatformSpecific = args.includePlatformSpecific

        self.dryRun = args.dryRun

        # 2. Use only the ones we have set:
        self._htmlManager.setFlags(self.printAllFileNames, self.onlySources, self.includeDevs, self.includeRCs, self.includePlatformSpecific)

        if (self.includeDevs or self.includeRCs) and self._htmlManager.areWheelFiltersEnabled():
            print("\tWARNING! Development releases (devX) or release candidates (RCs) flags are enabled, as well as the wheel filters, so they could be discarded anyway. This is caused because of the order of application: (1st) flags, (2nd) wheel filters.")
            print("\tPLEASE, CHECK OUT YOUR WHEEL FILTERS.")

        if self.dryRun:
            shutil.copytree(self.pypiLocalPath, self._dryRunsTmpDir)
            self.pypiLocalPath = self._dryRunsTmpDir

    def validPackageName(self) -> bool:
        """Checks whether the package link exists or not. If not, it returns False. True otherwise."""

        ok, status, _ = self._networkManager.getLink(self._remotePypiBaseDir + self.packageName)
        if not ok:
            print(status)
            return False

        return True

    def __createDirIfNeeded(self, directory: str):
        if not os.path.isdir(directory):
            os.mkdir(directory)

    def __createFileIfNeeded(self, file: str):
        if not os.path.exists(file):
            open(file, "a").close()

    def initLocalRepo(self):
        """Initializes the local repository creating the needed directories (if not exist) and updating accordingly the base HTML."""

        self.__createDirIfNeeded(self.pypiLocalPath)
        self.__createDirIfNeeded(self.packageLocalPath)

        self.__createFileIfNeeded(self.baseHTMLFileFullName)

    def __addEntryToBaseHTMLFile(self) -> bool:
        baseHTMLFile = open(self.baseHTMLFileFullName, "r+")
        htmlContent: str = baseHTMLFile.read()

        if len(htmlContent) == 0:
            htmlContent = self._htmlManager.getBaseHTML()

        entryAlreadyExists, htmlUpdated = self._htmlManager.insertHTMLEntry(htmlContent, "a", self.packageName, {"href": "./" + self.packageName})

        needToDownloadFiles: bool = False
        if not entryAlreadyExists:
            self._writeFileFromTheStart(baseHTMLFile, htmlUpdated)

            needToDownloadFiles = True

        baseHTMLFile.close()

        return needToDownloadFiles

    def canAddNewPackage(self) -> bool:
        """Adds the self.packageName package to the base HTML index, if not exists already. If it does, it returns False, True otherwise."""

        needToDownloadFiles: bool = self.__addEntryToBaseHTMLFile()

        return needToDownloadFiles

    def addPackage(self):
        """Downloads all the files for the required package 'packageName', i.e. all the .whl, the .zip and the .tar.gz if necessary."""

        ok, status, pypiPackageHTML = self._networkManager.getLink(self._remotePypiBaseDir + self.packageName)
        if not ok:
            print(status)
        else:
            pypiPackageHTMLStr: str = pypiPackageHTML.decode("utf-8")

        if self.printAllFileNames:
            packageFiles: List[str] = list(self._htmlManager.getHRefsList(pypiPackageHTMLStr).keys())
            self._printPackageNamesInHTML(packageFiles, "\nRetrieved package files (before filtering)")

        pypiPackageHTMLStr = self._htmlManager.filterInHTML(pypiPackageHTMLStr, self._regexZIPAndTars)
        linksToDownload: Dict[str, str] = self._htmlManager.getHRefsList(pypiPackageHTMLStr)

        if self.printAllFileNames:
            self._printPackageNamesInHTML(list(linksToDownload.keys()), "\nTo-be-downloaded package files (after filtering)")

        packageBaseHTML: str = self._htmlManager.getBaseHTML()
        _, packageBaseHTML = self._htmlManager.insertHTMLEntry(packageBaseHTML, "h1", "Links for " + self.packageName, {})
        with open(self.packageHTMLFileFullName, "w") as packageHTML_file:
            packageHTML_file.write(packageBaseHTML)

            self._downloadFilesInLocalPath(linksToDownload, packageBaseHTML, packageHTML_file, printVerbose=self.printVerbose, showRetries=self.showRetries)


class Update(LocalPyPIController):
    def __init__(self):
        Add.__init__(self)

    def parseScriptArguments(self, args: argparse.ArgumentParser):
        LocalPyPIController.parseScriptArguments(self, args)

        # 1. Set all the params we are going to use (let the ones we don't to None):
        self.printDefaultConfig = args.printDefaultConfig
        self.printAllFileNames = args.printAllFileNames
        self.printVerbose = args.printVerbose
        self.showRetries = args.showRetries

        self.onlySources = args.onlySources
        self.includeDevs = args.includeDevs
        self.includeRCs = args.includeRCs
        self.includePlatformSpecific = args.includePlatformSpecific

        self.dryRun = args.dryRun

        # 2. Use only the ones we have set:
        self._htmlManager.setFlags(self.printAllFileNames, self.onlySources, self.includeDevs, self.includeRCs, self.includePlatformSpecific)

        if (self.includeDevs or self.includeRCs) and self._htmlManager.areWheelFiltersEnabled():
            print("\tWARNING! Development releases (devX) or release candidates (RCs) flags are enabled, as well as the wheel filters, so they could be discarded anyway. This is caused because of the order of application: (1st) flags, (2nd) wheel filters.")
            print("\tPLEASE, CHECK OUT YOUR WHEEL FILTERS.")

        if self.dryRun:
            shutil.copytree(self.pypiLocalPath, self._dryRunsTmpDir)
            self.pypiLocalPath = self._dryRunsTmpDir

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

        ok, status, pypiRemoteIndex = self._networkManager.getLink(self._remotePypiBaseDir + self.packageName)
        if not ok:
            print(status)
        else:
            pypiRemoteIndexStr: str = pypiRemoteIndex.decode("utf-8")

        if self.printAllFileNames:
            packageFiles: List[str] = list(self._htmlManager.getHRefsList(pypiRemoteIndexStr).keys())
            self._printPackageNamesInHTML(packageFiles, "\nRetrieved package files (before filtering)")

        with open(self.packageHTMLFileFullName, "r") as pypiLocalIndexFile:
            pypiLocalIndex: str = pypiLocalIndexFile.read()

        pypiRemoteIndexFiltered: str = self._htmlManager.filterInHTML(pypiRemoteIndexStr, self._regexZIPAndTars)

        remoteIndexHRefs: Dict[str, str] = self._htmlManager.getHRefsList(pypiRemoteIndexFiltered)
        localIndexHRefs: Dict[str, str] = self._htmlManager.getHRefsList(pypiLocalIndex)
        newPackagesToDownload: Dict[str, str] = self.__getNewPackagesInRemote(remoteIndexHRefs, localIndexHRefs)

        if self.printAllFileNames:
            self._printPackageNamesInHTML(list(remoteIndexHRefs.keys()), "\nIn-the-remote package files (after filtering)")
            self._printPackageNamesInHTML(list(localIndexHRefs.keys()), "\nIn-the-local package files")
            self._printPackageNamesInHTML(list(newPackagesToDownload.keys()), "\nTo-be-downloaded package files (after filtering, in-the-remote minus in-the-local ones)")

        with open(self.packageHTMLFileFullName, "r+") as pypiLocalIndexFile:
            self._downloadFilesInLocalPath(newPackagesToDownload, pypiLocalIndex, pypiLocalIndexFile, printVerbose=self.printVerbose, showRetries=self.showRetries)


class Remove(LocalPyPIController):
    def __init__(self):
        LocalPyPIController.__init__(self)

    def parseScriptArguments(self, args: argparse.ArgumentParser):
        LocalPyPIController.parseScriptArguments(self, args)

        # 1. Set all the params we are going to use (let the ones we don't to None):
        self.dryRun = args.dryRun

        # 2. Use only the ones we have set:
        if self.dryRun:
            shutil.copytree(self.pypiLocalPath, self._dryRunsTmpDir)
            self.pypiLocalPath = self._dryRunsTmpDir

    def removePackage(self):
        """Removes the self.packageName from the local repository. Assumes it exists."""

        with open(self.baseHTMLFileFullName, "r+") as baseHTMLFile:
            baseHTMLStr: str = baseHTMLFile.read()
            packageExisted, updatedHTML = self._htmlManager.removeHTMLEntry(baseHTMLStr, "a", self.packageName)

            if not packageExisted:
                print("Package '" + self.packageName + "' was not being tracked yet.")
                return

            self._writeFileFromTheStart(baseHTMLFile, updatedHTML)

        self._removeDir(self.packageLocalPath, True)

        print("'" + self.packageName + "' package successfully removed.")


class List(LocalPyPIController):
    def __init__(self):
        LocalPyPIController.__init__(self)

    def parseScriptArguments(self, args: argparse.ArgumentParser):
        LocalPyPIController.parseScriptArguments(self, args)

    def repositoryExists(self) -> bool:
        return os.path.exists(self.baseHTMLFileFullName)

    def listPackages(self):
        """Lists all the packages in the root HTML index, if self.packageName == None. Lists the downloaded files for package self.packageName otherwise."""

        printMessage: str = ""

        htmlString: str = ""
        if self.packageName == "":
            with open(self.baseHTMLFileFullName, "r") as baseHTMLFile:
                htmlString = baseHTMLFile.read()

            printMessage = "Found {} packages:"
        else:
            with open(self.packageHTMLFileFullName, "r") as packageHTMLFile:
                htmlString = packageHTMLFile.read()

            printMessage = "Found {} files for package '" + self.packageName + "':"

        packagesDict: Dict[str, str] = self._htmlManager.getHRefsList(htmlString)

        print(printMessage.format(len(packagesDict)))
        for key, _ in packagesDict.items():
            print(key)

class Config(LocalPyPIController):
    def __init__(self):
        self._printWheelFilters: bool = None

    @property
    def printWheelFilters(self):
        return self._printWheelFilters

    @printWheelFilters.setter
    def printWheelFilters(self, new_printWheelFilters: str):
        self._printWheelFilters = new_printWheelFilters

    def parseScriptArguments(self, args: argparse.ArgumentParser):
        # 1. Set all the params we are going to use (let the ones we don't to None):
        self.printWheelFilters = args.showConfig

    def _getTextInGreen(self, text: str) -> str:
        CSI = "\x1B["
        resultingText = CSI+"32;40m" + text + CSI + "0m"

        return resultingText

    def getWheelFiltersSettings(self) -> str:
        """Gets the current settings at the settings location for the wheels filtering."""

        resultingString: str = ""

        resultingString += "Wheel filters settings file @ " + self._htmlManager.getWheelFiltersSettingsFilePath() + "\n"
        resultingString += "\n"

        filterEnabled: bool = self._htmlManager.areWheelFiltersEnabled()
        inOrOut: str = self._htmlManager.inOrOutFilterEnabled()

        resultingString += "Wheel filters enabled: " + str(filterEnabled) + " [applying=" + inOrOut + "]" + "\n"
        if self._htmlManager.areWheelFiltersEnabled():
            inFilterStr = "\n"
            inFilterStr += "\tIN filters ('" + str(self._htmlManager._wheelsManager.wheelsConfig.in_ORorAnd) + "'):\t" + str(self._htmlManager._wheelsManager.wheelsConfig.inFilters) + "\n"
            inFilterStr += "\t\t\t\t" + str(self._htmlManager._wheelsManager.wheelsConfig.in_ORorAndAttributes)

            if inOrOut == "in":
                resultingString += self._getTextInGreen(inFilterStr)
            else:
                resultingString += inFilterStr

            resultingString += "\n"

            outFilterStr = "\n"
            outFilterStr += "\tOUT filters ('" + str(self._htmlManager._wheelsManager.wheelsConfig.out_ORorAnd) + "'):\t" + str(self._htmlManager._wheelsManager.wheelsConfig.outFilters) + "\n"
            outFilterStr += "\t\t\t\t" + str(self._htmlManager._wheelsManager.wheelsConfig.out_ORorAndAttributes)

            if inOrOut == "out":
                resultingString += self._getTextInGreen(outFilterStr)
            else:
                resultingString += outFilterStr
            
            resultingString += "\n"

        return resultingString

