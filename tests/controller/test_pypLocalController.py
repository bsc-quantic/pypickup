import pytest
import os
import time

import argparse
import tempfile

import sys
sys.path.append(".")

from pypickup.controller import LocalPyPIController, Add, Update, Remove, List

# GENERAL VARIABLES #
htmlIndexName = "index.html"

#### Battery test 1 ####

testData = [
    ("a", "b", ("a", "b/", "b/" + htmlIndexName, "b/a/", "b/a/" + htmlIndexName)),
    ("a", "b\\", ("a", "b/", "b/" + htmlIndexName, "b/a/", "b/a/" + htmlIndexName))
]

@pytest.mark.parametrize("packageName, pypiLocalPath, expected_instance", testData, ids=["no_slashed", "double_slashed"])
def test_parseScriptArguments(packageName, pypiLocalPath, expected_instance):
    args = argparse.ArgumentParser()
    args.packageName = packageName
    args.pypiLocalPath = pypiLocalPath

    instance = LocalPyPIController()
    instance.parseScriptArguments(args)

    assert instance.packageName == expected_instance[0]
    assert instance.pypiLocalPath == expected_instance[1]
    assert instance.baseHTMLFileFullName == expected_instance[2]
    assert instance.packageLocalPath == expected_instance[3]
    assert instance.packageHTMLFileFullName == expected_instance[4]

#### Battery test 2 ####

testData = [
    ({"bs4-0.0.0.tar.gz": "https://files.pythonhosted.org/packages/50/fe/c4bf5083af20ec85ac5d278dfd12a9756724100c308b7bdccbaa7cbf5715/bs4-0.0.0.tar.gz#sha256=28408ebf82f66e2cf1e2a484c62f6e5d901fd6bdf1d9a6787207599538f0dbe6"},
"\
<!DOCTYPE html>\
<html>\
 <body>\
  <h1>\
   Links for bs4\
  </h1>\
  <a href=\"./bs4-0.0.1.tar.gz\">bs4-0.0.1.tar.gz</a>\
 </body>\
</html>",
"\
<!DOCTYPE html>\
<html>\
 <body>\
  <h1>\
   Links for bs4\
  </h1>\
  <a href=\"./bs4-0.0.1.tar.gz\">bs4-0.0.1.tar.gz</a>\
  <a href=\"./bs4-0.0.0.tar.gz\">bs4-0.0.0.tar.gz</a>\
 </body>\
</html>"
)
]

def getInitializedController():
    """Creates a temp dir and an inicialized LocalPyPIController instance, both returned."""

    tempDir = tempfile.TemporaryDirectory()
    # tempFile = tempfile.TemporaryFile()

    args = argparse.ArgumentParser()
    args.packageName = "pn"
    args.pypiLocalPath = tempDir.name

    instance = LocalPyPIController()
    instance.parseScriptArguments(args)

    # return instance, tempDir, tempFile
    return instance, tempDir

@pytest.mark.parametrize("packagesToDownload, currentHTML, expectedHTML", testData, ids=["1st"])
def test_downloadFilesInLocalPath(packagesToDownload, currentHTML, expectedHTML):
    instance, tempDir = getInitializedController()

    packageDirectory = os.path.join(tempDir.name, instance.packageName)
    os.makedirs(packageDirectory)

    htmlFile = open(os.path.join(packageDirectory, htmlIndexName), "w+")
    instance._downloadFilesInLocalPath(packagesToDownload, currentHTML, htmlFile)

    # Check if the HTML index file has been properly updated:
    htmlFile.seek(0)
    assert htmlFile.read().replace("\n", "") == expectedHTML

    # Check if the files (.whl, .zip, ...) have been properly downloaded:
    # for fileName in packagesToDownload.keys():
    #     assert os.path.exists(fileName)

    htmlFile.close()
    tempDir.cleanup()

# class TestAdd(unittest.TestCase):


# class TestUpdate(unittest.TestCase):


# class TestRemove(unittest.TestCase):


# class TestList(unittest.TestCase):