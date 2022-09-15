import argparse
import os

from typing import List

from pypickup.controller import LocalPyPIController


class Remove:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageNameList", type=str, nargs="+", default="", help="Python packages list to be removed from the local repository.")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default=os.getenv("PYPICKUP_INDEX_PATH", default="./.pypickup/"), help="Local root path in which the specified package is expected to be.")

    @staticmethod
    def __fillUpNonUsedArguments(args: argparse.Namespace) -> argparse.Namespace:
        argsResult: argparse.Namespace = args
        argsResult.onlySources = None
        argsResult.includeDevs = None
        argsResult.includeRCs = None
        argsResult.includePlatformSpecific = None

    @staticmethod
    def run(args: argparse.Namespace):
        Remove.__fillUpNonUsedArguments(args)

        listOfPackages: List[str] = args.packageNameList
        for packageName in listOfPackages:

            args.packageName = packageName
            print("Removing '" + packageName + "' from the local index:")

            controllerInstance = LocalPyPIController()
            controllerInstance.parseScriptArguments(args)

            if controllerInstance.isAlreadyAdded():
                controllerInstance.removePackage()
            else:
                print("Package " + controllerInstance.packageName + " has not been added to the local repository yet. Run the 'add' command first.")

            print()
