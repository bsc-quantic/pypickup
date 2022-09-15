import argparse
import os

from typing import List

from pypickup.controller import LocalPyPIController


class Update:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageNameList", type=str, nargs="+", default="", help="Python packages list to add to the local repository.")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default=os.getenv("PYPICKUP_INDEX_PATH", default="./.pypickup/"), help="Local root path in which the package from the PyPI repository will be synchronized.")

        parser.add_argument("-s", "--only-src", dest="onlySources", default=False, action="store_true", help="Download only the source files (.zip and .tar.gz). Disabled by default.")
        parser.add_argument("--dev", dest="includeDevs", default=False, action="store_true", help="Download also the new development releases (alpha, betas), which are not included by default.")
        parser.add_argument("--rc", dest="includeRCs", default=False, action="store_true", help="Download also the release candidates (rc), which are not included by default.")
        parser.add_argument("--ps", "--platform-specific", dest="includePlatformSpecific", default=False, action="store_true", help="Download also the platform-specific wheels, which are not included by default. If this flag is not set, only platform-agnostic files are considered.")

    @staticmethod
    def run(args: argparse.Namespace):
        listOfPackages: List[str] = args.packageNameList
        for packageName in listOfPackages:

            args.packageName = packageName
            print("Updating the local index for '" + packageName + "':")

            controllerInstance = LocalPyPIController()
            controllerInstance.parseScriptArguments(args)

            canSynchronize: bool = controllerInstance.isAlreadyAdded()
            if canSynchronize:
                controllerInstance.synchronizeWithRemote()
            else:
                print("Package " + controllerInstance.packageName + " has not been added to the local repository yet. Run the 'add' command first.")

            print()
