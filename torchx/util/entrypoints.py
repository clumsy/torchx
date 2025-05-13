# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-strict

from typing import Any, Dict, Optional

import importlib_metadata as metadata
from importlib_metadata import EntryPoint


# pyre-ignore-all-errors[3, 2]
def load(group: str, name: str, default=None):
    """
    Loads the entry point specified by

    ::

     [group]
     name1 = this.is:a_function
     -- or --
     name2 = this.is.a.module

    In case such an entry point is not found, an optional
    default is returned. If the default is not specified
    and the entry point is not found, then this method
    raises an error.
    """

    entrypoints = metadata.entry_points().select(group=group)

    if name not in entrypoints.names and default is not None:
        return default

    ep = entrypoints[name]
    return ep.load()


def _defer_load_ep(ep: EntryPoint) -> object:
    def run(*args: object, **kwargs: object) -> object:
        if ep.attr is None:  # this is a module
            return ep.load()
        else:
            return ep.load()(*args, **kwargs)

    return run


# pyre-ignore-all-errors[3, 2]
def load_group(
    group: str, default: Optional[Dict[str, Any]] = None, skip_defaults: bool = False
):
    """
    Loads all the entry points specified by ``group`` and returns
    the entry points as a map of ``name (str) -> deferred_load_fn``.
    where the ``deferred_load_fn`` (as the name implies) defers the
    loading of the entrypoint (e.g. ``entrypoint.load()``) until the
    caller explicitly executes the funtion.
    If there are entry points with the group matching exactly they are the only ones returned.
    Otherwise all entry points that have a group ending with ``group`` are returned with a prefix.

    For the following ``entry_point.txt``:

    ::

     [foo]
     bar = this.is:a_fn
     baz = this.is:b_fn

    1. ``load_group("foo")["bar"]("baz")`` -> equivalent to calling ``this.is.a_fn("baz")``
    1. ``load_group("food")`` -> ``None``
    1. ``load_group("food", default={"hello": this.is.c_fn})["hello"]("world")`` -> equivalent to calling ``this.is.c_fn("world")``
    1. ``load_group("food", default={"hello": this.is.c_fn}, skip_defaults=True)`` -> ``None``


    If the entrypoint is a module (versus a function as shown above), then calling the ``deferred_load_fn``
    simply loads the module and ignores any ``*args`` or ``**kwargs`` passed. For example:

    ::

     [foo]
     bar = this.is.a.module

    1. ``load_group("foo")["bar"]()`` -> loads ``this.is.a.module`` and returns a ``module`` type
    1. ``load_group("foo")["bar"]("baz", hello="world")`` -> same as above (ignores ``*args`` and ``**kwargs``)

    """

    entrypoints_prefixed, entrypoints_override = [], []
    for ep in metadata.entry_points():
        if ep.group == group:
            entrypoints_override.append(ep)
        elif ep.group.endswith(group):
            entrypoints_prefixed.append(ep)

    entrypoints = entrypoints_override or entrypoints_prefixed
    if len(entrypoints) == 0:
        if skip_defaults:
            return None
        return default

    eps: Dict[str, Any] = {}
    if not skip_defaults and default:
        eps.update(default)
    for ep in entrypoints:
        prefix = ep.group.replace(group, "")
        eps[prefix + ep.name] = _defer_load_ep(ep)
    return eps
