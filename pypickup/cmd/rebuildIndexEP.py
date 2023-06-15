import argparse
import os

from pypickup.controller import RebuildIndex


class RebuildIndexEP:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageName", type=str, nargs="?", default="", help="[OPTIONAL] Python package for which the index will be rebuilt")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default=os.getenv("PYPICKUP_INDEX_PATH", default="./.pypickup/"), help="Local root path in which the specified package is expected to be.")

        # ToDo: add --recursive option in order to rebuild all the indices.

    @staticmethod
    def run(args: argparse.Namespace):
        controllerInstance = RebuildIndex()
        controllerInstance.parseScriptArguments(args)

        if not controllerInstance.repositoryExists():
            print("No local repository has been initialized yet.\n" + \
                  "    - Download at least one package running the 'add' command,\n" + \
                  "    - Or use 'pypickup list -r package_name[==version]' to remotely list all the available packages.")
        else:
            if args.packageName != "" and not controllerInstance.packageExists():
                print("Package " + controllerInstance.packageName + " has not been added to the local repository yet. Run the 'add' command first.")
            else:
                controllerInstance.rebuildIndex()