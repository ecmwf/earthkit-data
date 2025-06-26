# (C) Copyright 2024 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import datetime
import logging
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from earthkit.data.utils.dates import to_datetime

from .coordinates import Coordinate
from .variable import Variable

LOG = logging.getLogger(__name__)


class Time(ABC):
    """Base class for different time representations."""

    @classmethod
    def from_coordinates(cls, coordinates: List[Coordinate]) -> "Time":
        """Create a Time instance from a list of coordinates.

        Returns
        -------
        Union[ForecastFromValidTimeAndStep, Analysis, Constant, ForecastFromValidTimeAndBaseTime, ForecastFromBaseTimeAndDate]
            An instance of a subclass of Time.

        Args
        ----
        coordinates : List[Coordinate]
            List of coordinate objects.
        """
        time_coordinate = [c for c in coordinates if c.is_time]
        step_coordinate = [c for c in coordinates if c.is_step]
        date_coordinate = [c for c in coordinates if c.is_date]

        if len(date_coordinate) == 0 and len(time_coordinate) == 1 and len(step_coordinate) == 1:
            return ForecastFromValidTimeAndStep(time_coordinate[0], step_coordinate[0])

        if len(date_coordinate) == 0 and len(time_coordinate) == 1 and len(step_coordinate) == 0:
            return Analysis(time_coordinate[0])

        if len(date_coordinate) == 0 and len(time_coordinate) == 0 and len(step_coordinate) == 0:
            return Constant()

        if len(date_coordinate) == 1 and len(time_coordinate) == 1 and len(step_coordinate) == 0:
            return ForecastFromValidTimeAndBaseTime(date_coordinate[0], time_coordinate[0])

        if len(date_coordinate) == 1 and len(time_coordinate) == 0 and len(step_coordinate) == 1:
            return ForecastFromBaseTimeAndDate(date_coordinate[0], step_coordinate[0])

        if len(date_coordinate) == 1 and len(time_coordinate) == 1 and len(step_coordinate) == 1:
            return ForecastFromValidTimeAndStep(time_coordinate[0], step_coordinate[0], date_coordinate[0])

        LOG.error("")
        LOG.error(f"{len(date_coordinate)} date_coordinate")
        for c in date_coordinate:
            LOG.error("    %s %s %s %s", c, c.is_date, c.is_time, c.is_step)
            # LOG.error('    %s', c.variable)

        LOG.error("")
        LOG.error(f"{len(time_coordinate)} time_coordinate")
        for c in time_coordinate:
            LOG.error("    %s %s %s %s", c, c.is_date, c.is_time, c.is_step)
            # LOG.error('    %s', c.variable)

        LOG.error("")
        LOG.error(f"{len(step_coordinate)} step_coordinate")
        for c in step_coordinate:
            LOG.error("    %s %s %s %s", c, c.is_date, c.is_time, c.is_step)
            # LOG.error('    %s', c.variable)

        raise NotImplementedError(f"{len(date_coordinate)=} {len(time_coordinate)=} {len(step_coordinate)=}")

    @abstractmethod
    def select_valid_datetime(self, variable: Variable) -> Optional[str]:
        """Select the valid datetime for a given variable.

        Parameters
        ----------
        variable : Variable
            The variable to select the datetime for.

        Returns
        -------
        Optional[str]
            The name of the time coordinate.
        """
        pass

    @abstractmethod
    def fill_time_metadata(self, coords_values: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        """Fill metadata with time information.

        Args
        ----
        coords_values : Dict[str, Any]
            Coordinate values.
        metadata : Dict[str, Any]
            Metadata dictionary.
        """

        pass


class Constant(Time):
    """Represents a constant time."""

    def fill_time_metadata(self, coords_values: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        """Fill metadata with time information.

        Parameters
        ----------
        coords_values : Dict[str, Any]
            Coordinate values.
        metadata : Dict[str, Any]
            Metadata dictionary.
        """
        return None

    def select_valid_datetime(self, variable: Variable) -> None:
        """Select the valid datetime for a given variable.

        Parameters
        ----------
        variable : Variable
            The variable to select the datetime for.
        """
        return None


class Analysis(Time):
    """Represents an analysis time."""

    def __init__(self, time_coordinate: Coordinate) -> None:
        """Initialize Analysis with a time coordinate.

        Parameters
        ----------
        time_coordinate : Coordinate
            The time coordinate.
        """
        self.time_coordinate_name = time_coordinate.variable.name

    def forecast_reference_time(self, selection: Optional[Variable] = None) -> Optional[str]:
        """Return the forecast reference time.

        Returns
        -------
        Optional[str]
            The name of the time coordinate.
        """
        return to_datetime(selection[self.time_coordinate_name].values[0])

    def valid_time(self, selection: Optional[Variable] = None) -> Optional[str]:
        """Return the forecast reference time.

        Returns
        -------
        Optional[str]
            The name of the time coordinate.
        """
        return self.forecast_reference_time(selection)

    def step(self, selection: Optional[Variable] = None) -> datetime.timedelta:
        """Return the step for the analysis time.

        Parameters
        ----------
        selection : Optional[Variable]
            The variable selection.

        Returns
        -------
        datetime.timedelta
            The step duration.
        """
        return datetime.timedelta(0)

    def fill_time_metadata(self, coords_values: Dict[str, Any], metadata: Dict[str, Any]) -> Any:
        """Fill metadata with time information.

        Parameters
        ----------
        coords_values : Dict[str, Any]
            Coordinate values.
        metadata : Dict[str, Any]
            Metadata dictionary.

        Returns
        -------
        Any
            The valid datetime.
        """
        valid_datetime = coords_values[self.time_coordinate_name]

        metadata["date"] = to_datetime(valid_datetime).strftime("%Y%m%d")
        metadata["time"] = to_datetime(valid_datetime).strftime("%H%M")
        metadata["step"] = 0

        return valid_datetime

    def select_valid_datetime(self, variable: Variable) -> str:
        """Select the valid datetime for a given variable.

        Parameters
        ----------
        variable : Variable
            The variable to select the datetime for.

        Returns
        -------
        str
            The name of the time coordinate.
        """
        return self.time_coordinate_name


class ForecastFromValidTimeAndStep(Time):
    """Represents a forecast time derived from valid time and step."""

    def __init__(
        self,
        time_coordinate: Coordinate,
        step_coordinate: Coordinate,
        date_coordinate: Optional[Coordinate] = None,
    ) -> None:
        """Initialize ForecastFromValidTimeAndStep with time, step, and optional date coordinates.

        Args
        ----
        time_coordinate : Coordinate
            The time coordinate.
        step_coordinate : Coordinate
            The step coordinate.
        date_coordinate : Optional[Coordinate]
            The date coordinate.
        """
        self.time_coordinate_name = time_coordinate.variable.name
        self.step_coordinate_name = step_coordinate.variable.name
        self.date_coordinate_name = date_coordinate.variable.name if date_coordinate else None

    def fill_time_metadata(self, coords_values: Dict[str, Any], metadata: Dict[str, Any]) -> Any:
        """Fill metadata with time information.

        Returns
        -------
        Any
            The valid datetime.

        Args
        ----
        coords_values : Dict[str, Any]
            Coordinate values.
        metadata : Dict[str, Any]
            Metadata dictionary.
        """
        valid_datetime = coords_values[self.time_coordinate_name]
        step = coords_values[self.step_coordinate_name]

        assert isinstance(step, datetime.timedelta)
        base_datetime = valid_datetime - step

        hours = step.total_seconds() / 3600
        assert int(hours) == hours

        metadata["date"] = to_datetime(base_datetime).strftime("%Y%m%d")
        metadata["time"] = to_datetime(base_datetime).strftime("%H%M")
        metadata["step"] = int(hours)

        # When date is present, it should be compatible with time and step

        if self.date_coordinate_name is not None:
            # Not sure that this is the correct assumption
            assert coords_values[self.date_coordinate_name] == base_datetime, (
                coords_values[self.date_coordinate_name],
                base_datetime,
            )

        return valid_datetime

    def select_valid_datetime(self, variable: Variable) -> str:
        """Select the valid datetime for a given variable.

        Parameters
        ----------
        variable : Variable
            The variable to select the datetime for.

        Returns
        -------
        str
            The name of the time coordinate.
        """
        return self.time_coordinate_name


class ForecastFromValidTimeAndBaseTime(Time):
    """Represents a forecast time derived from valid time and base time."""

    def __init__(self, date_coordinate: Coordinate, time_coordinate: Coordinate) -> None:
        """Initialize ForecastFromValidTimeAndBaseTime with date and time coordinates.

        Args
        ----
        date_coordinate : Coordinate
            The date coordinate.
        time_coordinate : Coordinate
            The time coordinate.
        """
        self.date_coordinate_name = date_coordinate.name
        self.time_coordinate_name = time_coordinate.name

    def fill_time_metadata(self, coords_values: Dict[str, Any], metadata: Dict[str, Any]) -> Any:
        """Fill metadata with time information.

        Returns
        -------
        Any
            The valid datetime.

        Args
        ----
        coords_values : Dict[str, Any]
            Coordinate values.
        metadata : Dict[str, Any]
            Metadata dictionary.
        """
        valid_datetime = coords_values[self.time_coordinate_name]
        base_datetime = coords_values[self.date_coordinate_name]

        step = valid_datetime - base_datetime

        hours = step.total_seconds() / 3600
        assert int(hours) == hours

        metadata["date"] = to_datetime(base_datetime).strftime("%Y%m%d")
        metadata["time"] = to_datetime(base_datetime).strftime("%H%M")
        metadata["step"] = int(hours)

        return valid_datetime

    def select_valid_datetime(self, variable: Variable) -> str:
        """Select the valid datetime for a given variable.

        Parameters
        ----------
        variable : Variable
            The variable to select the datetime for.

        Returns
        -------
        str
            The name of the time coordinate.
        """
        return self.time_coordinate_name


class ForecastFromBaseTimeAndDate(Time):
    """Represents a forecast time derived from base time and date."""

    def __init__(self, date_coordinate: Coordinate, step_coordinate: Coordinate) -> None:
        """Initialize ForecastFromBaseTimeAndDate with date and step coordinates.

        Args
        ----
        date_coordinate : Coordinate
            The date coordinate.
        step_coordinate : Coordinate
            The step coordinate.
        """
        self.date_coordinate_name = date_coordinate.name
        self.step_coordinate_name = step_coordinate.name

    def fill_time_metadata(self, coords_values: Dict[str, Any], metadata: Dict[str, Any]) -> Any:
        """Fill metadata with time information.

        Returns
        -------
        Any
            The valid datetime.

        Args
        ----
        coords_values : Dict[str, Any]
            Coordinate values.
        metadata : Dict[str, Any]
            Metadata dictionary.
        """
        date = coords_values[self.date_coordinate_name]
        step = coords_values[self.step_coordinate_name]
        assert isinstance(step, datetime.timedelta)

        metadata["date"] = to_datetime(date).strftime("%Y%m%d")
        metadata["time"] = to_datetime(date).strftime("%H%M")

        hours = step.total_seconds() / 3600

        assert int(hours) == hours
        metadata["step"] = int(hours)

        return date + step

    def select_valid_datetime(self, variable: Variable) -> Optional[str]:
        """Select the valid datetime for a given variable.

        Parameters
        ----------
        variable : Variable
            The variable to select the datetime for.

        Returns
        -------
        Optional[str]
            The name of the time coordinate.
        """
        raise NotImplementedError("ForecastFromBaseTimeAndDate.select_valid_datetime")
