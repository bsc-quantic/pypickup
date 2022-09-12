import argparse
import os

from pypi_cache.pypiCacheManager import LocalPyPIController


class Update:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageName", type=str, default="", help="Python package to add to the local repository.")
        parser.add_argument("-s", "--only-src", dest="onlySources", default=False, action="store_true", help="Download only the source files (.zip and .tar.gz). Disabled by default.")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default=os.getenv('PYPICACHE_INDEX_PATH', default="."), help="Local root path in which the package from the PyPI repository will be synchronized.")

    @staticmethod
    def run(args: argparse.Namespace):
        controllerInstance = LocalPyPIController()

        controllerInstance.parseScriptArguments(args)

        canSynchronize: bool = controllerInstance.isAlreadyAdded()
        if canSynchronize:
            controllerInstance.synchronizeWithRemote()
        else:
            print("Package " + controllerInstance.packageName + " has not been added to the local repository yet. Run the 'add' command first.")
