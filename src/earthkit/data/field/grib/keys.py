from .ensemble import ENSEMBLE_INDEXER_COLLECTOR
from .geography import GEOGRAPHY_INDEXER_COLLECTOR
from .parameter import PARAMETER_INDEXER_COLLECTOR
from .proc import PROC_INDEXER_COLLECTOR
from .time import TIME_INDEXER_COLLECTOR
from .vertical import VERTICAL_INDEXER_COLLECTOR

_COLLECTORS = [
    PARAMETER_INDEXER_COLLECTOR,
    ENSEMBLE_INDEXER_COLLECTOR,
    TIME_INDEXER_COLLECTOR,
    VERTICAL_INDEXER_COLLECTOR,
    GEOGRAPHY_INDEXER_COLLECTOR,
    PROC_INDEXER_COLLECTOR,
]


def collect(handle, context):
    for collector in _COLLECTORS:
        collector._collect(handle, context)
