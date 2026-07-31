# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
def create_grib_field(metadata, handle, data=None, values=None, geography=None, reference_field=None):
    r"""Create a Field object from XArray."""
    from earthkit.data.core.field import Field
    from earthkit.data.field.grib.data import GribData

    # from earthkit.data.field.mars.time import MarsTimeBuilder
    # from earthkit.data.field.mars.vertical import MarsVerticalBuilder
    # from earthkit.data.field.handler.geography import GeographyFieldComponentHandler
    # from earthkit.data.field.handler.labels import SimpleLabels
    # from earthkit.data.field.mars.ensemble import MarsEnsembleBuilder
    # from earthkit.data.field.grib_index.parameter import IndexParameterBuilder
    from earthkit.data.field.handler.data import ArrayDataFieldComponentHandler

    if data is None:
        data = GribData(handle)

    if values is not None:
        data = ArrayDataFieldComponentHandler(values)

    ensemble = IndexEnsembleBuilder.build(metadata)
    parameter = IndexParameterBuilder.build(metadata)
    time = IndexTimeBuilder.build(metadata)
    vertical = IndexVerticalBuilder.build(metadata)
    # labels = SimpleLabels({"mars": index})
    if geography is not None:
        geography = IndexGeographyBuilder.build(geography)
    else:
        geography = IndexGeographyBuilder.build(metadata)

    grib = metadata

    _kwargs = dict(
        data=data,
        parameter=parameter,
        time=time,
        geography=geography,
        vertical=vertical,
        ensemble=ensemble,
        # labels=labels,
    )

    if reference_field is not None:
        r = Field.from_field(reference_field, **_kwargs)
    else:
        r = Field(**_kwargs)

    r._set_private_data("metadata", grib)
    return r


class IndexParameterBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.grib.parameter import GribParameterBuilder

        return GribParameterBuilder.build(handle)


class IndexTimeBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.grib.time import GribTimeBuilder

        return GribTimeBuilder.build(handle)


class IndexProcBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.grib.proc import GribProcBuilder

        return GribProcBuilder.build(handle)


class IndexVerticalBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.grib.vertical import GribVerticalBuilder

        return GribVerticalBuilder.build(handle)


class IndexGeographyBuilder:
    @staticmethod
    def build(handle):
        grid_spec = handle.get("gridSpec", None)
        print(f"IndexGeographyBuilder: grid_spec={grid_spec}")
        if grid_spec is not None:
            from earthkit.data.field.component.geography import GridsSpecBasedGeography
            from earthkit.data.field.handler.geography import GeographyFieldComponentHandler

            if isinstance(grid_spec, str) and grid_spec != "":
                component = GridsSpecBasedGeography(grid_spec)
            else:
                raise ValueError(
                    (
                        "GribGeographyBuilder: cannot use unstructured grid because gridSpec"
                        "  is not available in the handle"
                    )
                )
            return GeographyFieldComponentHandler.from_component(component)
        else:
            from earthkit.data.field.grib.geography import GribGeographyBuilder

            return GribGeographyBuilder.build(handle)


class IndexEnsembleBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.grib.ensemble import GribEnsembleBuilder

        return GribEnsembleBuilder.build(handle)
