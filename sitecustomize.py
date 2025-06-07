import collections
from collections import abc
for name in ("MutableSet", "MutableMapping", "MutableSequence", "Mapping", "Iterable"):
    if not hasattr(collections, name):
        setattr(collections, name, getattr(abc, name))
