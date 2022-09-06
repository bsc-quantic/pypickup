import argparse
from pathlib import Path

from pypi_cache.pypiCacheManager import LocalPyPIController


class Add:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageName", type=str, default="", help="Python package to add to the local repository.")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default=str(Path.home()) + "/.pypi-cache/", help="Local root path in which the package from the PyPI repository will be downloaded.")

    @staticmethod
    def run(args: argparse.Namespace):
        controllerInstance = LocalPyPIController()

        controllerInstance.parseScriptArguments(args)
        controllerInstance.initLocalRepo()

        needToAddPackage: bool = controllerInstance.canAddNewPackage()
        if needToAddPackage:
            controllerInstance.addPackage()
        else:
            print("Package " + controllerInstance.packageName + " has been already added to the local repository. Try to run the 'update' command instead to synchronize changes with the remote PyPI.")
