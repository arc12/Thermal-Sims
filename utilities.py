import os
import logging

from logging.handlers import RotatingFileHandler
from logging import StreamHandler
import sys

from scipy.interpolate import CubicSpline


# logging
os.makedirs("../Logs", exist_ok=True)
logging.basicConfig(
    handlers=[
        RotatingFileHandler('../Logs/thermal_sims.log', maxBytes=100000, backupCount=5),
        StreamHandler(sys.stdout)
    ],
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


# radiator with derating factor for dt(room-rad). Use standard "Stelrad" correction factor.
# It is presumed that flow rates are modulated to conserve the flow-return temperature delta.
class Radiator:
    stelrad_correction_factor_points = (
        (0, 0),
        (5, 0.05),
        (10, 0.123),
        (15, 0.209),
        (20, 0.304),
        (25, 0.406),
        (30, 0.515),
        (35, 0.629),
        (40, 0.748),
        (45, 0.872),
        (50, 1.0)
    )

    def __init__(self, power_at_dt50, flow_temp, dt):
        """

        :param power_at_dt50: power output in Watts at dT(room-rad) = 50C
        :param flow_temp: radiator flow temp
        :param dt: flow-return temp difference
        """
        self.flow_temp = flow_temp
        self.dT = dt

        # set up the output power lookup
        self._spline = CubicSpline(
            [p[0] for p in self.stelrad_correction_factor_points],
            [power_at_dt50 * p[1] for p in self.stelrad_correction_factor_points]
        )

    def output(self, room_temp, flow_temp=None):
        """
        output in W for parameter value
        :param room_temp: room temp
        :param flow_temp: override flow temp. If None, the value of the instance variable is used. If set, the instance variable is updated
        :return:
        """
        if flow_temp is not None:
            self.flow_temp = flow_temp
        mean_rad_temp = self.flow_temp - self.dT / 2
        dt_rad_room = mean_rad_temp - room_temp
        return self._spline([dt_rad_room])[0]


# Spline for COP vs temperature.
# May be set up with T = outside ambient temp (at constant LWT) or T = LWT (at constant outside ambient)
class COP:
    def __init__(self, ts, cops, extrapolate=None):
        self._spline = CubicSpline(ts, cops, bc_type="natural", extrapolate=extrapolate)  # make the 2nd derivative be 0 at the curve ends.

    def cop(self, t):
        return self._spline([t])[0]


# Spline for Daily ambient temp cycle. The temperature at 24hrs is forced to be the same as the passed 00hrs so that the iterative "solver" works OK
class AmbientTemps:
    def __init__(self, t_points, t_interval=3):
        """

        :param t_points: temps for various hours. first one is t=00hrs, next is t_interval
        :param t_interval: no of hours between t_points
        """
        t_points = t_points + [t_points[0]]  # force smooth roll-over at midnight
        self._spline = CubicSpline(range(0, 25, t_interval), t_points, bc_type="natural", extrapolate=False)

    def temp(self, hr):
        """
        Outside ambient temp for given hour.
        :param hr: can be a decimal hour
        :return:
        """
        return self._spline([hr])[0]


# A simple device to allow for hour to be treated as a decimal in the "solver" but for the target temperatures to be defined as per-hour steps
# As I would expect a target temp schedule to be defined this way.
class TargetTemp:
    def __init__(self, t_points):
        """

        :param t_points: target temps for hours 00 to 23
        """
        self.t_points = t_points

    def temp(self, hr):
        return self.t_points[int(hr)]
