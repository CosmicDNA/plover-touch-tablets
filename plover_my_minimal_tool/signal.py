class Signal:
    hook: str
    callback: callable

    def __init__(self, name: str, obj: any) -> None:
        self.hook = name
        self.callback = getattr(obj, f"on_{name}")
