class MarsKey:
    def __init__(self, name, key, default=None):
        self.name = name
        self.key = key
        self.default = default

    def value(self, request):
        return {self.key: request.get(self.name, self.default)}


class LevTypeKey(MarsKey):
    def value(self, request):
        v = request.get(self.name, self.default)
        if v is None:
            return {}
        if v == "sfc":
            return {"vertical.type": "surface"}
        if v == "pl":
            return {"vertical.type": "pressure"}
        return {self.key: v}


KEYS = [
    MarsKey("date", "time.base_date"),
    MarsKey("time", "time.base_time"),
    MarsKey("step", "time.step", 0),
    MarsKey("levelist", "vertical.level"),
    LevTypeKey("levtype", "vertical.type", "pl"),
    MarsKey("param", "parameter.variable"),
    MarsKey("number", "parameter.shortName"),
]

rules = {
    "date": "time.base_date",
    "time": "time.base_time",
    "step": "time.step",
    "levelist": "vertical.level",
}


def normalise_request(request):
    r = request.copy()

    if "date" in r:
        r["base_date"] = r.pop("date")
    if "time" in r:
        r["base_time"] = r.pop("time")

    level = r.get("levelist")
    if level is not None:
        r["level"] = level

    return r
