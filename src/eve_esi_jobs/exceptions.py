class BadRequestParameter(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class MissingParameter(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class BadOpId(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
