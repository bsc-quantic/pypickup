import argparse
import os

from pypickup.controller import Config


class ConfigEP:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("-s", "--show", dest="showConfig", default=False, action="store_true", help="Prints the default wheel filters settings.")

    @staticmethod
    def run(args: argparse.Namespace):
        controllerInstance = Config()
        controllerInstance.parseScriptArguments(args)

        if args.showConfig:
            print(controllerInstance.getWheelFiltersSettings())
        else:
            print("Use config -h for usage.")