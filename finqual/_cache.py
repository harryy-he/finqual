"""
Shared caching utilities for the finqual package.

This module provides ``weak_lru`` — an LRU-cache decorator that keeps only a
weak reference to ``self`` so that cached methods do not extend the lifetime
of their owning instance (and therefore do not leak memory).

Previously the same decorator was duplicated in ``core.py``, ``cca.py``,
``sec_api.py`` and ``form_parsers.py``. All four call sites now import from
here.
"""

from __future__ import annotations

import functools
import weakref
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable[..., object])


def weak_lru(maxsize: int = 128, typed: bool = False) -> Callable[[F], F]:
    """
    LRU cache decorator that stores a **weak reference** to ``self``.

    This pattern allows caching of bound instance methods while avoiding
    the memory leak that ``functools.lru_cache`` introduces (a strong
    reference to ``self`` would keep the instance alive for as long as
    the cache lives).

    Parameters
    ----------
    maxsize : int, default 128
        Maximum number of cached entries.
    typed : bool, default False
        If True, arguments of different types are cached separately.

    Returns
    -------
    Callable
        Decorator suitable for instance methods.
    """

    def wrapper(func: F) -> F:
        @functools.lru_cache(maxsize=maxsize, typed=typed)
        def _cached(self_ref, *args, **kwargs):
            return func(self_ref(), *args, **kwargs)

        @functools.wraps(func)
        def inner(self, *args, **kwargs):
            return _cached(weakref.ref(self), *args, **kwargs)

        return inner  # type: ignore[return-value]

    return wrapper


__all__ = ["weak_lru"]
