# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from __future__ import annotations

import logging
import math
import os
from typing import TYPE_CHECKING

from . import Target

LOG = logging.getLogger(__name__)

if TYPE_CHECKING:
    from multio.plans import Client
    from multio.multio import Multio
    from typing import Any, Dict
    from earthkit.data.core.metadata import Metadata

GEOGRAPHY_ALIASES: dict[str, list[str]] = {
    'north': ['latitudeOfFirstGridPointInDegrees'],
    'west': ['longitudeOfFirstGridPointInDegrees'],
    'south': ['latitudeOfLastGridPointInDegrees'],
    'east': ['longitudeOfLastGridPointInDegrees'],
    'west_east_increment': ['iDirectionIncrementInDegrees'],
    'south_north_increment': ['jDirectionIncrementInDegrees'],
    'Ni': ['Ni', 'N'],
    'Nj': ['Nj'],
    'gridType': ['gridType'],
    'pl': ['pl'],
}

def geography_translate(metadata: Metadata) -> dict:
    """Translate geography metadata from earthkit to multio"""
    geo_namespace = metadata.as_namespace("geography")

    multio_geo = {}

    for multio_key, earthkit_keys in GEOGRAPHY_ALIASES.items():
        if not any(key in geo_namespace for key in earthkit_keys):
            continue
        valid_key = [key for key in earthkit_keys if key in geo_namespace]
        if len(valid_key) > 1:
            raise ValueError(f"Multiple keys found for {multio_key}: {valid_key}")
        multio_geo[multio_key] = geo_namespace.pop(valid_key[0])

    multio_geo.update(geo_namespace)
    if 'pl' in multio_geo:
        multio_geo['pl'] = ','.join(map(str, multio_geo['pl'].tolist()))
    return multio_geo


def earthkit_to_multio(metadata: Metadata):
    """Convert earthkit metadata to Multio metadata"""
    metad = metadata.as_namespace("mars")
    metad.update(geography_translate(metadata))
    metad.pop("levtype", None)
    metad.pop("param", None)
    metad.pop("bitmapPresent", None)

    metad["paramId"] = metadata["paramId"]
    metad["typeOfLevel"] = metadata["typeOfLevel"]

    return metad


class MultioTarget(Target):
    _server: Multio = None

    def __init__(self, plan: Client | os.PathLike | str | Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.plan = plan

    @property
    def server(self) -> Multio:
        from multio import MultioPlan
        from multio import Multio

        if self._server is None:
            with MultioPlan(self.plan):
                server = Multio()
                self._server = server
        return self._server

    def write(self, data=None, encoder=None, template=None, **kwargs):
        from earthkit.data.core.fieldlist import FieldList

        if encoder is None:
            encoder = self._coder

        if template is None:
            template = self.template

        if isinstance(data, FieldList):
            data.to_target(self, encoder=encoder, template=template, **kwargs)
        else:
            self._write_field(data, **kwargs)

    def _write_field(self, data, encoder=None, template=None, **kwargs):
        _ = encoder
        kwargs.pop('plan', None)

        import multio

        if template is None:
            template = self.template or data

        array = data.to_numpy()
        template_metadata: Metadata = template.metadata()

        metadata_template = dict(earthkit_to_multio(template_metadata))
        metadata_template.update(kwargs)

        metadata_template.update(
            {
                # "step": step,
                # "trigger": "step",
                "globalSize": math.prod(array.shape),
            }
        )
        with self.server as server:
            server_metadata = multio.Metadata(server, metadata_template)
            server.write_field(server_metadata, array)


target = MultioTarget
