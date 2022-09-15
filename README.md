# pypickup

An utility to download packages from PyPI and save them locally, building a tree as if it were the PyPI repository itself.

Python3 libraries required:

- os, typing, re, urllib, argparse (built-in libs)
- bs4, wheel-filename (in PyPI.org, available on 'pip')

#### Deploy

To use its commands, go to the project root and do:

```
pip install --editable .
```

#### Utilities

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