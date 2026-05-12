from typing import Any

from earthkit.data.field.component.provenance import Provenance
from earthkit.data.field.handler.provenance import ProvenanceFieldComponentHandler


class XArrayProvenance(ProvenanceFieldComponentHandler):
    def __init__(self, owner: Any, selection: Any) -> None:
        self.owner = owner
        self.selection = selection

        history = selection.attrs.get("history", None)
        # Hack: transfer history metadata from dataset to selection
        if history is None and hasattr(owner, "ds"):
            history = owner.ds.attrs.get("history", None)

        part = Provenance.from_dict({"history": history})
        super().__init__(part)
