import argparse
from ast import parse


class Add:
    @staticmethod
    def init_subparser(parser: argparse.ArgumentParser):
        parser.add_argument("pkg", help="Package(s) to track", action="store")

    @staticmethod
    def run(args: argparse.Namespace):
        pass
