# (C) Copyright 2024 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_timedelta

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

        print("time_coordinate:", time_coordinate)
        print("step_coordinate:", step_coordinate)
        print("date_coordinate:", date_coordinate)

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
    def spec(self, coords_values: Dict[str, Any]):
        """Return the time specification based on coordinate values.

        Parameters
        ----------
        coords_values : Dict[str, Any]
            Coordinate values.

        Returns
        -------
        TimeSpec
            The time specification.
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

    def spec(self, coords_values: Dict[str, Any]):
        return {}


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

    def spec(self, coords_values: Dict[str, Any]):
        valid_time = to_datetime(coords_values[self.time_coordinate_name])
        return {"valid_datetime": valid_time}


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

    def spec(self, coords_values: Dict[str, Any]):
        valid_datetime = to_datetime(coords_values[self.time_coordinate_name])
        step = to_timedelta(coords_values[self.step_coordinate_name])

        print("time_coordinate_name:", self.time_coordinate_name)
        print("step_coordinate_name:", self.step_coordinate_name)
        print("date_coordinate_name:", self.date_coordinate_name)

        if self.date_coordinate_name is not None and self.date_coordinate_name in coords_values:
            base_datetime_ref = valid_datetime - step
            base_datetime = to_datetime(coords_values[self.date_coordinate_name])
            # Not sure that this is the correct assumption
            assert base_datetime == base_datetime_ref, (
                base_datetime,
                valid_datetime,
                step,
                base_datetime_ref,
            )

        return {"valid_datetime": valid_datetime, "step": step}


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

    def spec(self, coords_values: Dict[str, Any]):
        valid_datetime = to_datetime(coords_values[self.time_coordinate_name])
        base_datetime = to_datetime(coords_values[self.date_coordinate_name])
        step = valid_datetime - base_datetime

        return {"base_datetime": base_datetime, "step": step}


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

    def spec(self, coords_values: Dict[str, Any]):
        date = coords_values[self.date_coordinate_name]
        step = coords_values[self.step_coordinate_name]

        return {"base_datetime": date, "step": step}
