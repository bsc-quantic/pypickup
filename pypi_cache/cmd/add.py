import argparse

from pypi_cache.pypiCacheManager import LocalPyPIController


class Add:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageName", type=str, default="", help="Python package to download.")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default="~/.pypi-cache/", help="Local root path in which the package from the PyPI repository will be downloaded.")

    @staticmethod
    def run(args: argparse.Namespace):
        controllerInstance = LocalPyPIController()

        controllerInstance.parseScriptArguments(args)
        needToDownloadFiles: bool = controllerInstance.initLocalRepo()
        if needToDownloadFiles:
            controllerInstance.downloadFiles()
        else:
            print("Package " + controllerInstance.packageName + " is being already tracked. Try to update it instead to synchronize changes.")
