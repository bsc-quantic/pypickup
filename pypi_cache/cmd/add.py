import argparse
import os

from pypi_cache.pypiCacheManager import LocalPyPIController


class Add:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageName", type=str, default="", help="Python package to add to the local repository.")
        parser.add_argument("-s", "--only-src", dest="onlySources", default=False, action="store_true", help="Download only the source files (.zip and .tar.gz). Disabled by default.")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default=os.getenv('PYPICACHE_INDEX_PATH', default="."), help="Local root path in which the package from the PyPI repository will be downloaded.")

    @staticmethod
    def run(args: argparse.Namespace):
        controllerInstance = LocalPyPIController()

        controllerInstance.parseScriptArguments(args)
        
        if controllerInstance.validPackageName():
            controllerInstance.initLocalRepo()

            needToAddPackage: bool = controllerInstance.canAddNewPackage()
            if needToAddPackage:
                controllerInstance.addPackage()
            else:
                print("Package " + controllerInstance.packageName + " has been already added to the local repository. Try to run the 'update' command instead to synchronize changes with the remote PyPI.")
        else:
            print("Package " + controllerInstance.packageName + " does not exist in the remote repository (" + controllerInstance.remotePyPIRepository + ")")
