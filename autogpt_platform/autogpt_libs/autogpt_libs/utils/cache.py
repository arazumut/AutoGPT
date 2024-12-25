import threading
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def thread_cached(func: Callable[P, R]) -> Callable[P, R]:
    thread_local = threading.local()

    def sarmalayıcı(*args: P.args, **kwargs: P.kwargs) -> R:
        cache = getattr(thread_local, "cache", None)
        if cache is None:
            cache = thread_local.cache = {}
        anahtar = (args, tuple(sorted(kwargs.items())))
        if anahtar not in cache:
            cache[anahtar] = func(*args, **kwargs)
        return cache[anahtar]

    return sarmalayıcı
