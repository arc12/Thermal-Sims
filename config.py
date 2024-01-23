"""Global configs"""
from os import environ, path

from os import listdir
import json

basedir = path.abspath(path.dirname(__file__))


class Config(object):
    """Base config class"""
    CSRF_ENABLED = True


# various bits of reference and config data. Done as functions to allow for migration to JSON if required.
# def get_xxx_config():
#     with open("xxx_config.json", 'r') as j:
#         config = json.load(j)
#     return config

def get_building_default_options():
    # initial parameters for building.
    d = {
        "Kitchen": {  # Current kitchen
            "heat_loss_factor": 100,  # W/K
            "emitter_std_power": 4500,  # W @ dT(rad-room)=50C
            "tmp_category": "Lower Medium",  # thermal mass parameter lookup name
            "floor_area": 28,
            # volume of circulating water (pipes + rads) in litres. Excl volumiser (option in UI)
            "fluid_volume": 20  # 7.5l for 20m x 22mm pipe; 6.5l for 600x1000 K2; 4l for 300x1200 K2
        },
        "Whole": {  # TODO THESE VALUES NEED SETTING
            "heat_loss_factor": 100,  # W/K
            "emitter_std_power": 4500,  # W @ dT(rad-room)=50C
            "tmp_category": "Lower Medium",  # thermal mass parameter lookup name
            "floor_area": 28,
            # volume of circulating water (pipes + rads) in litres. Excl volumiser (option in UI)
            "fluid_volume": 20  # 7.5l for 20m x 22mm pipe; 6.5l for 600x1000 K2; 4l for 300x1200 K2
        }
    }
    return d


def get_cop_point_options(vs="ambient"):
    """
    Dict of sets of COP values for:
    a) if vs == "ambient", different ambient temps for a given LWT and fixed dT(LWT-RWT).
    b) if vs == "lwt" (or any other value), different LTWs for a fixed ambient temp (and fixed dT)

    These are input to a COP spline estimator.

    :return:
    """
    if vs == "ambient":
        cops = {
            # Mitsubishi PUZ-WM85VAA. dT is only implied (and only for 35 and 45 LWT)
            # Using the "Nominal" compressor frequency rows in the Performance data table for COP
            "WM85_LWT35": {
                "LWT": 35,
                "dT": 5,
                "T_amb": (-15, -10, -7, 2, 7, 12, 15),
                "COP": (2.15, 2.30, 2.60, 3.51, 4.80, 5.20, 5.95),
                "capacity": 8500  # Watts
            },
            "WM85_LWT40": {
                "LWT": 40,
                "dT": 5,
                "T_amb": (-15, -10, -7, 2, 7, 12, 15),
                "COP": (1.95, 2.15, 2.40, 3.15, 4.20, 4.60, 5.20),
                "capacity": 8500  # Watts
            },
            "WM85_LWT45": {
                "LWT": 45,
                "dT": 5,
                "T_amb": (-15, -10, -7, 2, 7, 12, 15),
                "COP": (1.80, 2.05, 2.25, 2.86, 3.70, 4.00, 4.45),
                "capacity": 8500  # Watts
            },
            "WM85_LWT50": {
                "LWT": 50,
                "dT": 5,
                "T_amb": (-10, -7, 2, 7, 12, 15),
                "COP": (1.85, 2.05, 2.55, 3.25, 3.45, 3.80),
                "capacity": 8500  # Watts
            },
            # this is about what the oil boiler does "full-on".
            # the mean flow temp is generally around 50 once room up to 15C or so
            "Direct_LWT70": {
                "LWT": 70,
                "dT": 5,
                "T_amb": (-10, 15),
                "COP": (1.0, 1.0),
                "capacity": 10000  # Watts
            },

            # !!!! The Daikin data is rather sparse !!!!!!
            # Used EHPA (+BAFA for 10C) certification programme COPs from capacity tables in the Daikin Databook.
            "EDLA09_LWT35": {
                "LWT": 35,
                "dT": 5,
                "T_amb": (-7, 2, 7, 10),
                "COP": (2.81, 3.79, 4.91, 5.32),
                "capacity": 6290  # Watts. Use minimum over all T_amb
            },
            # Used combination of MCS and EHPA certification programme COPs from capacity tables in the Daikin Databook.
            "EDLA09_LWT45": {
                "LWT": 45,
                "dT": 5,
                "T_amb": (-7, -2, 7),
                "COP": (2.22, 2.35, 3.71),
                "capacity": 7760  # Watts. Use minimum over all T_amb
            },
            # only 2 points is dangerous straight line!
            "EDLA09_LWT55": {
                "LWT": 55,
                "dT": 8,
                "T_amb": (-7, 7),
                "COP": (1.8, 2.91),
                "capacity": 7130  # Watts. Use minimum over all T_amb
            },
        }
    else:
        # vs LWT. Capacities chosen for LWT=40.
        cops = {
            "WM85_AMB-7": {
                "T_amb": -7,
                "dT": 5,
                "LWT": (25, 35, 40, 45, 50, 55),
                "COP": (2.70, 2.50, 2.30, 2.10, 1.85, 1.65),
                "capacity": 3200  # Watts
            },
            "WM85_AMB+2": {
                    "T_amb": 2,
                    "dT": 5,
                    "LWT": (25, 35, 40, 45, 50, 55),
                    "COP": (4.65, 4.15, 3.65, 3.15, 2.75, 2.40),
                    "capacity": 3400  # Watts
            },
            "WM85_AMB+7": {
                    "T_amb": 7,
                    "dT": 5,
                    "LWT": (25, 35, 40, 45, 50, 55),
                    "COP": (5.95, 5.20, 4.45, 3.75, 3.20, 2.65),
                    "capacity": 3100  # Watts
            },
            "WM85_AMB+12": {
                    "T_amb": 12,
                    "dT": 5,
                    "LWT": (25, 35, 40, 45, 50, 55),
                    "COP": (6.90, 6.05, 5.20, 4.40, 3.70, 3.05),
                    "capacity": 2700  # Watts
            }
        }
    return cops


# These are made to start and end at the same temperature when the spline is generated, so that the iterative "solver" works OK
# => make sure that there isn't a big interval from 21 to 00
def get_ambient_hr_options():
    """
    List of temps for 3 hour points for various day profile stereotypes.

    :return:
    """
    amb = {
        "Winter": [
            4.2,  # 00
            3.8,  # 03
            3.3,  # 06
            4.0,  # 09
            6.5,  # 12
            6.0,  # 15
            5.5,  # 18
            4.8  # 21
        ],
        "Constant 10": [10.0] * 8
    }
    return amb


# Inside target temperatures. These are the defaults which users can play around with using slider controls.
# make all entries 2 chars wide for visual
def get_target_temp_options():
    tt = {
        #    00, 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23
        "Moderate Burst":  # Our current CH controller default profile but with rounding off the 0.5 settings
            [14,  5,  5,  5,  5,  5,  5, 12, 13, 15, 16, 14, 14, 14, 14, 15, 15, 16, 16, 16, 17, 17, 16, 15],
        "Constant 14": [14] * 24
    }
    return tt


def get_tmp_options():
    """Thermal mass parameter. Units kJ.m^-2.K^-1"""
    tmp = {
        "Low": 90,
        "Lower Medium": 110,
        "Upper Medium": 200,
        "High": 300,
        "Very High": 450
    }
    return tmp
