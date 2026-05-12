# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.field.component.provenance import EmptyProvenance, ProvenanceBase, create_provenance

from .core import SimpleFieldComponentHandler


class ProvenanceFieldComponentHandler(SimpleFieldComponentHandler):
    """Provenance component handler of a field."""

    COMPONENT_CLS = ProvenanceBase
    COMPONENT_MAKER = create_provenance
    NAME = "provenance"

    def get_grib_context(self, context) -> dict:
        pass

    @classmethod
    def from_component(cls, component: ProvenanceBase) -> "ProvenanceFieldComponentHandler":
        return ProvenanceFieldComponentHandler(component)

    @classmethod
    def create_empty(cls) -> "ProvenanceFieldComponentHandler":
        return EMPTY_PROVENANCE_HANDLER


EMPTY_PROVENANCE_HANDLER = ProvenanceFieldComponentHandler(EmptyProvenance())
