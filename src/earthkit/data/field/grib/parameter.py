# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.field.component.parameter import create_parameter
from earthkit.data.field.handler.parameter import ParameterFieldComponentHandler

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
        d = GribParameterBuilder._build_dict(handle)
        component = create_parameter(d)
        handler = ParameterFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        # Core metadata keys for identifying the parameter
        v = _get("shortName", None)
        if v == "~":
            v = handle.get("paramId", ktype=str, default=None)
        if v is None:
            v = _get("param", None)
        variable = v
        standard_name = _get("cfName", None)
        long_name = _get("name", None)

        units = _get("units", None)

        d = dict(
            variable=variable,
            standard_name=standard_name,
            long_name=long_name,
            units=units,
        )

        # Metadata for chemical parameters
        if _get("chemId", None) is not None:
            # "chemId" is defined for chemical parameters
            chem = _get("parameter.chemShortName", None)
            # using "parameter.chemShortName" instead of "chemShortName"
            # avoids getting "unknown" if this key is not defined
            # cf. https://github.com/ecmwf/eccodes/blob/eac2eb507b5b44fcc3d3c58e38/definitions/grib2/parameters.def#L29

            chem_long_name = _get("chemName", None)
            if chem_long_name == "unknown":
                chem_long_name = None

            d["chem"] = chem
            d["chem_long_name"] = chem_long_name

        # Metadata for optical parameters
        _wavelength = _get("mars.wavelength", None)
        wavelength = None
        wavelength_bounds = None
        # The logic below follows the "mars.wavelength" key definition:
        # https://github.com/ecmwf/eccodes/blob/develop/definitions/mars/mars.wavelength.def
        if isinstance(_wavelength, (int, float)):
            wavelength = round(_wavelength)
        elif isinstance(_wavelength, str):
            # expected format is "<wlen1>-<wlen2>"
            try:
                wlen1, wlen2 = _wavelength.split("-")
                wavelength_bounds = round(float(wlen1)), round(float(wlen2))
                wavelength = round((wavelength_bounds[1] + wavelength_bounds[0]) / 2)
            except Exception:
                pass

        if wavelength is not None:
            d["wavelength"] = wavelength
            d["wavelength_bounds"] = wavelength_bounds

        _grib_edition = _get("edition", None)

        def _scale_value(v, scaling_factor):
            if _grib_edition == 1:
                return float(v / scaling_factor)
            elif _grib_edition >= 2:
                return float(v * 10 ** (-scaling_factor))
            raise ValueError(f"Unsupported GRIB edition: {_grib_edition}")

        # 2D wave spectra: direction
        try:
            direction_number = _get("directionNumber", None)
            if direction_number is not None:
                direction_index = direction_number - 1  # convert to 0-based index
                number_of_directions = _get("numberOfDirections", None)
                direction_scaling_factor = _get("directionScalingFactor", None)
                scaled_directions = _get("scaledDirections", None)
                wave_direction = _scale_value(scaled_directions[direction_index], direction_scaling_factor)

                d["wave_direction"] = wave_direction
                d["wave_direction_index"] = direction_index

                # wave direction bounds
                if number_of_directions > 1:
                    if direction_index > 0:
                        prev_wave_direction = _scale_value(
                            scaled_directions[direction_index - 1], direction_scaling_factor
                        )
                        delta = (wave_direction - prev_wave_direction) / 2
                    else:
                        next_wave_direction = _scale_value(
                            scaled_directions[direction_index + 1], direction_scaling_factor
                        )
                        delta = (next_wave_direction - wave_direction) / 2
                    d["wave_direction_bounds"] = (wave_direction - delta, wave_direction + delta)
                else:
                    d["wave_direction_bounds"] = None
        except Exception:
            pass

        # 2D wave spectra: frequency
        try:
            frequency_number = _get("frequencyNumber", None)
            if frequency_number is not None:
                frequency_index = frequency_number - 1  # convert to 0-based index
                number_of_frequencies = _get("numberOfFrequencies", None)
                frequency_scaling_factor = _get("frequencyScalingFactor", None)
                scaled_frequencies = _get("scaledFrequencies", None)
                wave_frequency = _scale_value(scaled_frequencies[frequency_index], frequency_scaling_factor)

                d["wave_frequency"] = wave_frequency
                d["wave_frequency_index"] = frequency_index

                # wave frequency bounds: frequencies are equally spaced on the log scale
                if number_of_frequencies > 1:
                    if frequency_index > 0:
                        prev_wave_frequency = _scale_value(
                            scaled_frequencies[frequency_index - 1], frequency_scaling_factor
                        )
                        factor = (wave_frequency / prev_wave_frequency) ** 0.5
                    else:
                        next_wave_frequency = _scale_value(
                            scaled_frequencies[frequency_index + 1], frequency_scaling_factor
                        )
                        factor = (next_wave_frequency / wave_frequency) ** 0.5
                    d["wave_frequency_bounds"] = (round(wave_frequency / factor, 6), round(wave_frequency * factor, 6))
                else:
                    d["wave_frequency_bounds"] = None

        except Exception:
            pass

        return d


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
