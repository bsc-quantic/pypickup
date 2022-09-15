import argparse
from importlib.metadata import entry_points


def cli():
    entrypoints = entry_points()["pypickup.cmd"]

    parser = argparse.ArgumentParser(prog="pypickup", description="Manage a local offline PyPi mirror")
    subparsers = parser.add_subparsers(help="available commands", dest="cmd")

    plugins = {}
    for name, entrypoint in entrypoints:
        # load plugin
        plugin = entrypoint.load()
        plugins[name] = plugin

        # load command subparser
        subparser = subparsers.add_parser(name)
        plugin.init_subparser(subparser)

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
        return

    _, plugin = next(filter(lambda x: x[0] == args.cmd, plugins.items()))
    plugin.run(args)
