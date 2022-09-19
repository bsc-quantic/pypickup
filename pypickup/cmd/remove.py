import argparse
import os

from typing import List

from pypickup.controller import Remove


class RemoveEP:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageNameList", type=str, nargs="+", default="", help="Python packages list to be removed from the local repository.")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default=os.getenv("PYPICKUP_INDEX_PATH", default="./.pypickup/"), help="Local root path in which the specified package is expected to be.")

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
