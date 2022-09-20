import argparse
import os

from typing import List

from pypickup.controller import Remove


class RemoveEP:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageNameList", type=str, nargs="+", default="", help="Python packages list to be removed from the local repository.")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default=os.getenv("PYPICKUP_INDEX_PATH", default="./.pypickup/"), help="Local root path in which the specified package is expected to be.")

        parser.add_argument("-d", "--dry-run", dest="dryRun", default=False, action="store_true", help="Display the changes that would be performed without actually making them.")

    @staticmethod
    def run(args: argparse.Namespace):
        listOfPackages: List[str] = args.packageNameList
        for packageName in listOfPackages:

            args.packageName = packageName
            print("Removing '" + packageName + "' from the local index:")

            controllerInstance = Remove()
            controllerInstance.parseScriptArguments(args)

            controllerInstance.removePackage()

            print()
