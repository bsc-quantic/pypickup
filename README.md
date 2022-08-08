# PyPI-cache utility

An utility to download packages from PyPI and save them locally, building a tree as if it were the PyPI repository itself.

Python3 libraries required:

- os, re, urllib, argparse (built-in libs)
- bs4

#### Utilities

To download a package for the first time, the pypi-download command should be used.

```
python pypi-download.py numpy -p ./localPyPI/
```