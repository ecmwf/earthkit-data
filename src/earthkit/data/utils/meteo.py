# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

# TODO: This code was copied from earthkit.meteo.solar.array to avoid
# dependency on earthkit.meteo and circular imports. It should be refactored
# to avoid code duplication.


import datetime

import numpy as np
from earthkit.utils.array import array_namespace

DAYS_PER_YEAR = 365.25


def julian_day(date):
    if date.tzinfo is not None and date.tzinfo.utcoffset(date) is not None:
        year_start = datetime.datetime(date.year, 1, 1, tzinfo=date.tzinfo)
    else:
        year_start = datetime.datetime(date.year, 1, 1)
    delta = date - year_start
    return delta.days + delta.seconds / 86400.0


def solar_declination_angle(date):
    angle = julian_day(date) / DAYS_PER_YEAR * np.pi * 2

    # declination in [degrees]
    declination = float(
        0.396372
        - 22.91327 * np.cos(angle)
        + 4.025430 * np.sin(angle)
        - 0.387205 * np.cos(2 * angle)
        + 0.051967 * np.sin(2 * angle)
        - 0.154527 * np.cos(3 * angle)
        + 0.084798 * np.sin(3 * angle)
    )
    # time correction in [ h.degrees ]
    time_correction = float(
        0.004297
        + 0.107029 * np.cos(angle)
        - 1.837877 * np.sin(angle)
        - 0.837378 * np.cos(2 * angle)
        - 2.340475 * np.sin(2 * angle)
    )
    return declination, time_correction


def cos_solar_zenith_angle(date, latitudes, longitudes):
    """Cosine of solar zenith angle.

    Parameters
    ----------
    date: datetime.datetime
        Date
    latitudes: array-like
        Latitude [degrees]
    longitudes: array-like
        Longitude [degrees]

    Returns
    -------
    float array
        Cosine of the solar zenith angle (all values, including negatives)
        [Hogan_and_Hirahara2015]_. See also:
        http://answers.google.com/answers/threadview/id/782886.html

    """
    xp = array_namespace(latitudes, longitudes)
    latitudes = xp.asarray(latitudes)
    longitudes = xp.asarray(longitudes)
    device = xp.device(latitudes)

    # declination angle + time correction for solar angle
    declination, time_correction = solar_declination_angle(date)

    declination = xp.asarray(declination, device=device)
    time_correction = xp.asarray(time_correction, device=device)

    # solar_declination_angle returns degrees
    # TODO: deg2rad() is not part of the array API standard
    declination = xp.deg2rad(declination)
    latitudes = xp.deg2rad(latitudes)

    sindec_sinlat = xp.sin(declination) * xp.sin(latitudes)
    cosdec_coslat = xp.cos(declination) * xp.cos(latitudes)

    # solar hour angle [h.deg]
    # TODO: deg2rad() is not part of the array API standard
    solar_angle = xp.deg2rad((date.hour - 12) * 15 + longitudes + time_correction)
    zenith_angle = sindec_sinlat + cosdec_coslat * xp.cos(solar_angle)

    # Clip negative values
    return xp.clip(zenith_angle, 0.0, None)


def _integrate(
    func,
    begin_date,
    end_date,
    latitudes,
    longitudes,
    *,
    intervals_per_hour=1,
    integration_order=3,
):
    xp = array_namespace(latitudes, longitudes)
    latitudes = xp.asarray(latitudes)
    longitudes = xp.asarray(longitudes)

    # Gauss-Integration coefficients
    if integration_order == 3:  # default, good speed and accuracy (3 points)
        _C1 = xp.sqrt(xp.asarray(5.0 / 9.0))
        E = xp.asarray([-_C1, xp.asarray(0.0), _C1])
        W = xp.asarray([5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0])
    elif integration_order == 1:  # fastest, worse accuracy (1 point)
        E = xp.asarray([0.0])
        W = xp.asarray([2.0])
    elif integration_order == 2:  # faster, less accurate (2 points)
        _C1 = xp.sqrt(xp.asarray(3.0))
        E = xp.asarray([-1.0 / _C1, 1.0 / _C1])
        W = xp.asarray([1.0, 1.0])
    elif integration_order == 4:  # slower, more accurate (4 points)
        _C1 = xp.sqrt(xp.asarray(6.0 / 5.0))
        _C2 = xp.sqrt(xp.asarray(30))
        E = xp.asarray(
            [
                -xp.sqrt(3.0 / 7.0 + 2.0 / 7.0 * _C1),
                -xp.sqrt(3.0 / 7.0 - 2.0 / 7.0 * _C1),
                xp.sqrt(3.0 / 7.0 - 2.0 / 7.0 * _C1),
                xp.sqrt(3.0 / 7.0 + 2.0 / 7.0 * _C1),
            ]
        )
        W = xp.asarray(
            [
                (18 - _C2) / 36,
                (18 + _C2) / 36,
                (18 + _C2) / 36,
                (18 - _C2) / 36,
            ]
        )
    else:
        raise ValueError("Invalid integration order %d", integration_order)

    assert intervals_per_hour > 0
    assert end_date > begin_date

    date = begin_date
    interval_size_hours = (end_date - begin_date).total_seconds() / 3600.0

    nsplits = int(interval_size_hours * intervals_per_hour + 0.5)

    assert nsplits > 0

    time_steps = xp.linspace(0, interval_size_hours, num=nsplits + 1)

    integral = xp.zeros_like(latitudes)
    for s in range(len(time_steps) - 1):
        ti = time_steps[s]
        tf = time_steps[s + 1]

        deltat = tf - ti
        jacob = deltat / 2.0

        w = jacob * W
        w /= interval_size_hours  # average of integral
        t = jacob * E
        t += (tf + ti) / 2.0

        for n in range(len(w)):
            integral += w[n] * func(
                date + datetime.timedelta(hours=float(t[n])),
                latitudes,
                longitudes,
            )

    return integral


def incoming_solar_radiation(date):
    # To be replaced with improved formula
    (a, b) = (165120.0, 4892416.0)
    angle = julian_day(date) / DAYS_PER_YEAR * np.pi * 2
    return np.cos(angle) * a + b


def toa_incident_solar_radiation(
    begin_date,
    end_date,
    latitudes,
    longitudes,
    *,
    intervals_per_hour=1,
    integration_order=3,
):
    def func(date, latitudes, longitudes):
        isr = incoming_solar_radiation(date)
        csza = cos_solar_zenith_angle(date, latitudes, longitudes)
        return isr * csza

    return _integrate(
        func,
        begin_date,
        end_date,
        latitudes,
        longitudes,
        intervals_per_hour=intervals_per_hour,
        integration_order=integration_order,
    )
