class Signal:
    hook: str
    callback: callable

    def __init__(self, name: str) -> None:
        self.hook = name
        self.callback = f"on_{name}"
