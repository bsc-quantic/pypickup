[![Tests](https://github.com/UB-Quantic/pypickup/actions/workflows/python-testing.yml/badge.svg)](https://github.com/UB-Quantic/pypickup/actions/workflows/python-testing.yml)
[![Coverage](https://github.com/UB-Quantic/pypickup/actions/workflows/python-coverage.yml/badge.svg)](https://github.com/UB-Quantic/pypickup/actions/workflows/python-coverage.yml)

# pypickup

A tool to download packages from PyPI and save them locally, building a directory tree that fulfills [PEP 503](https://peps.python.org/pep-0503/). Properly configured, `pip` will install packages from there as if it was downloading them from the PyPI repository itself.

For example, the following commands will download all final versions (no `dev` and no `rc` versions), source distributions of `numpy` into the `.pypickup` folder, and then install the latest compatible version from there.

```
pypickup add -s -p ./.pypickup numpy
pip install --index-url ./.pypickup numpy
```

In order to save yourself from typing the -p parameter every time, you can just set an env variable PYPICKUP_INDEX_PATH (which you can include in your ~/.bashrc file if you feel like it):

```
export PYPICKUP_INDEX_PATH=/usr/local/pypickup
```

## Install

Before installing pypickup you should do:

```
export PYPICKUP_INDEX_PATH=MY_LOCAL_REPOSITORY_PATH
```

Then:
```
pip install pypickup
```

Alternatively, you can download this repository and perform an editable installation:

```
pip install --editable .
```

## Commands

An -h flag can be used on any command to display all the available options and its usage. For instance:

```
pypickup add -h
```

To add a package for the first time:

```
pypickup add numpy
```

This will create a folder in the default location (./.pypickup/) in which all the stablished files (.whl and .zip) for the specified package will be downloaded. Besides, it will create the corresponding metadata files (index.html) to track that package. The next time you want to synchronize the same package against the PyPI remote repository, you should do:

```
pypickup update numpy
```

This will download the new packages available in the remote, in case there is any. It'll do nothing otherwise. It also updates the index.html of the indicated package with the new downloaded packages, as expected.

To redefine another default location we may set an environment variable PYPICKUP_INDEX_PATH. 

2 more commands are available to remove packages and to list the available ones already added:

```
pypickup rm numpy

pypickup list
```

If we specify a package for the 'list' command, it will show a list of the downloaded distributions themselves.

```
pypickup list numpy
```

And additional command is in development to configure the settings file for the wheels filtering.

```
pypickup config -h
```

## Examples

To check what are all the available packages in the remote repository and which of them would be downloaded:

```
pypickup config --show                  # Shows the filters that will be applied for commands 'add' and 'update'

pypickup add numpy                      # Downloads the whole package 'numpy', considering the active filters
pypickup rm numpy                       # Removes the whole package 'numpy'

pypickup add numpy==1.8                 # Downloads the package 'numpy' (version 1.8, all patches) to the local repository for the first time
pypickup add -a --dry-run numpy         # Performs a test for command 'add', with the package 'numpy'. Prints the packages in the remote (PyPI), the ones that will be filtered out, and the actual ones that will be downloaded

pypickup update numpy==1.9              # Downloads numpy version 1.9 (all patches) to the current local repository
pypickup list numpy                     # Lists all the currently downloaded packages for the package 'numpy'
pypickup rm numpy==1.8                  # Removes only numpy version 1.8 (and patches)
pypickup rm numpy==1                    # Removes only numpy version 1 (and minors)

pypickup add -s numpy                   # Downloads only the source files (not wheels)
pypickup add --ps numpy                 # Downloads all the platform-specific packages for package 'numpy'. Some packages' wheels will only be able to be downloaded by means of this command, depending on how have they been built ('$ pypickup add --help' for documentation).

pypickup list -r pandas                 # Lists the whole set of available packages in the remote repository for 'pandas'. Does not filter out any package, i.e shows everything. Please, consider that if you do now '$ pypickup add pandas', not all the previously shown packages will be downloaded, since the command 'add' is filtering out some packages by default, like the developement releases (alphas, betas...), the release candidates, and so on. See --help for more details on command 'add'
pypickup list -r scipy==1.7.2           # Lists available packages for scipy, version 1.7.2
```

## Development

### Add new commands

To add new commands to the application, follow these steps:

1. Create a new \[commandName\].py file with a class named \[commandName\]EP (standing for EntryPoint), which should include 2 main methods: `init_subparser(...)` and `run(...)`. These methods will be automatically called by the `cli()` method at cli.py, which will be in turn called by the main script at \_\_main\_\_.py.
2. Add the new command entry in the pyproject.toml file, in the list [project.entry-points."pypickup.cmd"].
3. Add the corresponding export in the pypickup/cmd/\_\_init\_\_.py file.
4. Finally, create a new class in the controller.py that will implement the specific methods for that command. This new class should inherit from the general-purpose class LocalPyPIController and should implement, at least, a method `parseScriptArguments(...)`. This class LocalPyPIController should:
    - Add in their \_\_init\_\_(self) method the arguments for the new command you are coding.
    - Implement the getters and setters for the new command, which should be used in your new class.

    Your new class should parse **all** the arguments your command is going to use in your own method `parseScriptArguments(...)`. If some of the arguments already exist (from other commands), you use them but you should parse them anyway in your `parseScriptArguments(...)`, even if this implies "repeating" some code. This is the best approach for an application open to new features.

    Apart from the main controller file, there are 2 other controllers that should be considered properly when adding new commands/features.
    - htmlManager.py: in charge of everything related with the HTML files management. It already include methods to find, insert and delete tags into an HTML string body.
    - networkManager.py: in charge of everything related with the network (e.g. getting URL links).

### Editable installation

In order to speed up the development, we recommend an editable installation:

```
pip install --editable .
```