import argparse
import os

from typing import List

from pypickup.controller import LocalPyPIController


class List:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageName", type=str, nargs="?", default="", help="Python package for which the list of downloaded files will be shown.")
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
        List.__fillUpNonUsedArguments(args)

        controllerInstance = LocalPyPIController()
        controllerInstance.parseScriptArguments(args)

        controllerInstance.listPackages()