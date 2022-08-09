#! /usr/bin/python
import os

import argparse

from bs4 import BeautifulSoup
from urllib import request
import re


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

    def __prettifyHTML(self, htmlSoup: BeautifulSoup) -> str:
        """Lets the 'htmlString' formatted as desired."""

        resultingHTML: str = str(htmlSoup.prettify())

        resultingHTML = self.__getElementContentInlined(resultingHTML, "a")

        return resultingHTML

    def insertPackageEntry(self, htmlString: str, pypiLocalPath: str, packageName: str) -> tuple[bool, str]:
        """Appends a new element <a> into the 'htmlString' body whose href attribute is the 'packageName'. Returns whether the entry already exists in the htmlString."""

        soup = BeautifulSoup(htmlString, "html.parser")

        if soup.find("a", string=packageName):
            return True, ""

        newEntry = soup.new_tag("a", href=pypiLocalPath + packageName + "/")
        newEntry.string = packageName
        soup.html.body.append(newEntry)

        return False, self.__prettifyHTML(soup)

    def filterInHTML(self, htmlContent: str, regexList: list, packageName: str) -> str:
        """Keeps <a> entries in 'htmlContent' that matches some regular expressión in 'regexList'. The ones that do not match are filtered out."""

        outputSoup = BeautifulSoup(self._baseHTML_fromScratch, "html.parser")
        newEntry = outputSoup.new_tag("h1")
        newEntry.string = "Links for " + packageName
        outputSoup.html.body.append(newEntry)

        originalSoup = BeautifulSoup(htmlContent, "html.parser")
        for regexEntry in regexList:
            # inEntries: list = originalSoup.find_all(string = re.compile(regexEntry))
            inEntries: list = originalSoup.find_all("a", string=re.compile(regexEntry))

            for inEntry in inEntries:
                outputSoup.html.body.append(inEntry)

        return self.__prettifyHTML(outputSoup)

    def getHRefsList(self, pypiPackageHTML: str) -> dict:
        """Returns a list of the href attributes appearing in 'pypiPackageHTML'."""

        soup = BeautifulSoup(pypiPackageHTML, "html.parser")

        resultingDict: dict = {}
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

    _regexListIn: list = list()
    _regexListOut: list = list()

    def __init__(self):
        self._packageName: str
        self._pypiLocalPath: str

    @property
    def packageName(self):
        return self._packageName

    @property
    def pypiLocalPath(self):
        return self._pypiLocalPath

    @packageName.setter
    def packageName(self, new_PackageName: str):
        self._packageName = new_PackageName

    @pypiLocalPath.setter
    def pypiLocalPath(self, new_PyPiLocalPath: str):
        self._pypiLocalPath = new_PyPiLocalPath

    def __initRegexs(self):
        self._regexListIn.append("^" + self.packageName + ".*\.(zip|tar.gz)$")  # .zip or tar.gz files
        # self._regexListIn.append("^numpy-.+cp\.whl$")

    def parseScriptArguments(self):
        """Parses the application arguments."""

        parser = argparse.ArgumentParser(description="Download PyPI into local folder.")
        parser.add_argument("packageName", type=str, default="", help="Python package to download.")
        parser.add_argument("-p", "--pypiLocalPath", dest="pypiLocalPath", type=str, default="./localPyPI/", help="Local root path to download the package from PyPI.")

        args = parser.parse_args()

        self.packageName = args.packageName
        self.pypiLocalPath = args.pypiLocalPath

        self.__initRegexs()

    def __createDirIfNeeded(self, directory: str):
        if not os.path.isdir(directory):
            os.mkdir(directory)

    def __createBaseHTMLFileIfNeeded(self, baseHTMLFilePath: str):
        if not os.path.exists(baseHTMLFilePath):
            open(baseHTMLFilePath, "a").close()

    def __addEntryToBaseHTMLFile(self, baseHTMLFilePath: str) -> bool:
        baseHTML_file = open(baseHTMLFilePath, "r+")
        htmlContent: str = baseHTML_file.read()

        if len(htmlContent) == 0:
            htmlContent = self._htmlManager.getBaseHTML()

        entryAlreadyExists, htmlUpdated = self._htmlManager.insertPackageEntry(htmlContent, self.pypiLocalPath, self.packageName)

        needToDownloadFiles: bool = False
        if not entryAlreadyExists:
            baseHTML_file.seek(0)
            baseHTML_file.truncate()
            baseHTML_file.write(htmlUpdated)

            needToDownloadFiles = True

        baseHTML_file.close()

        return needToDownloadFiles

    def initLocalRepo(self) -> bool:
        """Initializes the local repository creating the needed directories (if not exist) and updating accordinly the base HTML. Returns whether the self.packageName packages need to be downloaded or not (because it already exists in the corresponding directory)."""

        self.__createDirIfNeeded(self.pypiLocalPath)
        self.__createDirIfNeeded(self.pypiLocalPath + "/" + self.packageName + "/")

        baseHTMLFilePath: str = self.pypiLocalPath + "/" + self._baseHTMLFileName
        self.__createBaseHTMLFileIfNeeded(baseHTMLFilePath)
        needToDownloadFiles: bool = self.__addEntryToBaseHTMLFile(baseHTMLFilePath)

        return needToDownloadFiles

    def downloadFiles(self):
        """Downloads all the files for the required package 'packageName', i.e. all the .whl, the .zip (source code) and the HTML ¿?."""

        pypiPackageHTML: str = request.urlopen(self._remotePypiBaseDir + self.packageName).read().decode("utf-8")

        pypiPackageHTML: str = self._htmlManager.filterInHTML(pypiPackageHTML, self._regexListIn, self.packageName)
        packageHTML_file = open(self.pypiLocalPath + "/" + self.packageName + "/" + self._packageHTMLFileName, "w")
        packageHTML_file.write(pypiPackageHTML)
        packageHTML_file.close()

        linksToDownload: dict = self._htmlManager.getHRefsList(pypiPackageHTML)
        for fileName, fileLink in linksToDownload.items():
            print("Downloading package '" + fileName + "'...", flush=True)
            request.urlretrieve(fileLink, self.pypiLocalPath + "/" + self.packageName + "/" + fileName)


def main():
    controllerInstance = LocalPyPIController()

    controllerInstance.parseScriptArguments()
    needToDownloadFiles: bool = controllerInstance.initLocalRepo()
    if needToDownloadFiles:
        controllerInstance.downloadFiles()


if __name__ == "__main__":
    main()
