_TASKS: dict[str, callable] = {}

def task(name: str | None = None):
    """Decorator: register a function under an optional name."""
    def _decorate(fn):
        _TASKS[name or fn.__name__] = fn
        return fn
    return _decorate

def get(name: str):
    """Fetch a registered function by name."""
    return _TASKS[name]

def available() -> list[str]:
    return sorted(_TASKS)

def clear():
    _TASKS.clear()