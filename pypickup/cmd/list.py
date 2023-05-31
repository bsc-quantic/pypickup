import argparse
import os

from pypickup.controller import List


class ListEP:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("packageName", type=str, nargs="?", default="", help="Python package for which the list of downloaded files will be shown.")
        parser.add_argument("-p", "--index-path", dest="pypiLocalPath", type=str, default=os.getenv("PYPICKUP_INDEX_PATH", default="./.pypickup/"), help="Local root path in which the specified package is expected to be.")

        parser.add_argument("-r", "--remote", dest="remote", default=False, action="store_true", help="List all packages available in the remote repository.")

    @staticmethod
    def run(args: argparse.Namespace):
        controllerInstance = List()
        controllerInstance.parseScriptArguments(args)

        if args.remote:
                controllerInstance.listPackagesInTheRemote()
        elif not controllerInstance.repositoryExists():
            print("No local repository has been initialized yet.\n" + \
                  "    - Download at least one package running the 'add' command,\n" + \
                  "    - Or use 'pypickup list -r package_name[==version]' to remotely list all the available packages.")
        else:
            if args.packageName != "" and not controllerInstance.packageExists():
                print("Package " + controllerInstance.packageName + " has not been added to the local repository yet. Run the 'add' command first.")
            else:
                controllerInstance.listPackages()