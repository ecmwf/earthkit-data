class Units:
    def __init__(self, units: str = None) -> None:
        self._units = units

    @property
    def units(self) -> str:
        return self._units
