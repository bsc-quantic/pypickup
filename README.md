# pypickup

A tool to download packages from PyPI and save them locally, building a directory tree that fulfills [PEP 503](https://peps.python.org/pep-0503/). Properly configured, `pip` will install packages from there as if it was downloading them from the PyPI repository itself.

For example, the following commands will download all final versions (no `dev` versions), source distributions of `numpy` into the `.pypickup` folder, and then install the lates compatible version from there.
```
pypickup add -s -p ./.pypickup numpy
pip install --index-url ./.pypickup numpy
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

This will create a folder in the default location (~/.pypickup/) in which all the stablished files (.whl and .zip) for the specified package will be downloaded. Besides, it will create the corresponding metadata files (index.html) to track that package. The next time you want to synchronize the same package against the PyPI remote repository, you should do:

```
pypickup update numpy
```

This will download the new packages available in the remote, in case there is any. It'll do nothing otherwise. It also updates the index.html of the indicated package with the new downloaded packages, as expected.

2 more commands are available to remove packages and to list the available ones already added:

```
pypickup rm numpy

pypickup list
```

If we specify a package for the 'list' command, it will show a list of the downloaded distributions themselves.

```
pypickup list numpy
```

## Development

In order to speed up development, we recommend an editable installation:
```
pip install --editable .
```