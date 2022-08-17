# PyPI-cache utility

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

To add a package for the first time:

```
pypi-cache add numpy
```

This will create a folder in the default location (~/.pypi-cache/) in which all the stablished files (.whl and .zip) for the specified package will be downloaded. Besides, it will create the corresponding metadata files (index.html) to track that package. The next time you want to synchronize the same package against the PyPI remote repository, you should do:

```
pypi-cache update numpy
```

This will download the new packages available in the remote, in case there is any. It'll do nothing otherwise.