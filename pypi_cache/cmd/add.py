import argparse

from pypi_cache.pypiCacheManager import LocalPyPIController


class Add:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageName", type=str, default="", help="Python package to download.")
        parser.add_argument("-p", "--pypiLocalPath", dest="pypiLocalPath", type=str, default="./localPyPI/", help="Local root path to download the package from PyPI.")

    @staticmethod
    def run(args: argparse.Namespace):
        controllerInstance = LocalPyPIController()

        controllerInstance.parseScriptArguments(args)
        needToDownloadFiles: bool = controllerInstance.initLocalRepo()
        if needToDownloadFiles:
            controllerInstance.downloadFiles()
        else:
            print("Package " + controllerInstance.packageName + " is being already tracked. Try to update it instead to synchronize changes.")
