
import yaml

_SETTINGS = {
    "harmonisor": None,
    "harmonisor_kwargs": dict(),
}

class set:
    # TODO: Add docstring
    def __init__(self, **kwargs):

        try:
            self._old = {key: _SETTINGS[key] for key in kwargs}
        except KeyError as ex:
            raise KeyError(
                f"Wrong settings. Available settings: {list(_SETTINGS)}"
            ) from ex

        _SETTINGS.update(kwargs)
        
    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ) -> None:
        _SETTINGS.update(self._old)


def get(key):
    return _SETTINGS.get(key)