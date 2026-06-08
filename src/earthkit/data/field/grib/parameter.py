# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .collector import GribContextCollector
from .core import GribFieldComponentHandler


class GribParameterBuilder:
    """Builder for creating parameter components from GRIB message handles.

    This builder extracts parameter metadata from GRIB messages and creates the appropriate
    parameter component subclass (:class:`~earthkit.data.field.component.parameter.Parameter`,
    :class:`~earthkit.data.field.component.parameter.ChemicalParameter`,
    :class:`~earthkit.data.field.component.parameter.OpticalParameter`,
    :class:`~earthkit.data.field.component.parameter.ChemicalOpticalParameter`, or
    :class:`~earthkit.data.field.component.parameter.WaveSpectraParameter`) based on the
    metadata contents.
    """

    @staticmethod
    def build(handle):
        from earthkit.data.field.component.parameter import create_parameter
        from earthkit.data.field.handler.parameter import ParameterFieldComponentHandler

        d = GribParameterBuilder._build_dict(handle)
        component = create_parameter(d)
        handler = ParameterFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        v = _get("shortName", None)
        if v == "~":
            v = handle.get("paramId", ktype=str, default=None)
        if v is None:
            v = _get("param", None)
        variable = v
        standard_name = _get("cfName", None)
        long_name = _get("name", None)

        units = _get("units", None)

        chem_name = _get("parameter.chemShortName", None)
        # using "parameter.chemShortName" instead of "chemShortName" avoids getting "unknown" if this key is not defined
        # cf. https://github.com/ecmwf/eccodes/blob/eac2eb507b5b44fcc3d3c58e382efde3a274b1c4/definitions/grib2/parameters.def#L29

        chem_long_name = _get("chemName", None)
        if chem_long_name == "unknown":
            chem_long_name = None

        _wavelength = _get("mars.wavelength", None)
        # The logic below follows the "mars.wavelength" key definition:
        # https://github.com/ecmwf/eccodes/blob/develop/definitions/mars/mars.wavelength.def
        if isinstance(_wavelength, (int, float)):
            wavelength = round(_wavelength)
        elif isinstance(_wavelength, str):
            # expected format is "<wlen1>-<wlen2>"
            try:
                wlen1, wlen2 = _wavelength.split("-")
                wavelength = round(float(wlen1)), round(float(wlen2))
            except Exception:
                wavelength = None
        else:
            wavelength = None

        _grib_edition = _get("edition", None)

        def _scale_value(v, scaling_factor):
            if _grib_edition == 1:
                return float(v / scaling_factor)
            elif _grib_edition >= 2:
                return float(v * 10 ** (-scaling_factor))
            raise ValueError(f"Unsupported GRIB edition: {_grib_edition}")

        # Wave direction
        try:
            scaled_directions = _get("scaledDirections", None)
            direction_number = _get("directionNumber", None)
            direction_scaling_factor = _get("directionScalingFactor", None)
            wave_direction = _scale_value(scaled_directions[direction_number - 1], direction_scaling_factor)
        except Exception:
            wave_direction = None

        # Wave frequency
        try:
            scaled_frequencies = _get("scaledFrequencies", None)
            frequency_number = _get("frequencyNumber", None)
            frequency_scaling_factor = _get("frequencyScalingFactor", None)
            wave_frequency = _scale_value(scaled_frequencies[frequency_number - 1], frequency_scaling_factor)
        except Exception:
            wave_frequency = None

        return dict(
            variable=variable,
            standard_name=standard_name,
            long_name=long_name,
            units=units,
            chem=chem_name,
            chem_long_name=chem_long_name,
            wavelength=wavelength,
            wave_direction=wave_direction,
            wave_frequency=wave_frequency,
        )


class GribParameterContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        component = handler.component
        r = {
            "shortName": component.variable(),
            # "units": param.units,
        }
        context.update(r)


COLLECTOR = GribParameterContextCollector()


class GribParameter(GribFieldComponentHandler):
    BUILDER = GribParameterBuilder
    COLLECTOR = COLLECTOR
