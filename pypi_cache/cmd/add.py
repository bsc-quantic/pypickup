import argparse
import os

from typing import List

from pypi_cache.pypiCacheManager import LocalPyPIController


class Add:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageNameList", type=str, nargs='+', default="", help="Python packages list to add to the local repository.")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default=os.getenv('PYPICACHE_INDEX_PATH', default="./.pypi-cache/"), help="Local root path in which the package from the PyPI repository will be downloaded.")

        parser.add_argument("-s", "--only-src", dest="onlySources", default=False, action="store_true", help="Download only the source files (.zip and .tar.gz). Disabled by default.")
        parser.add_argument("--dev", dest="includeDevs", default=False, action="store_true", help="Download also the new development releases (alpha, betas), which are not included by default.")
        parser.add_argument("--rc", dest="includeRCs", default=False, action="store_true", help="Download also the release candidates (rc), which are not included by default.")

    @staticmethod
    def run(args: argparse.Namespace):
        listOfPackages: List[str] = args.packageNameList
        for packageName in listOfPackages:
            
            args.packageName = packageName
            print("Adding '" + packageName + "' to the local index:")

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
            
            print()
