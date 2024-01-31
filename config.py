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
        "Kitchen FC": {  # with new fan coil rather than kickspace
            "heat_loss_factor": 88,  # W/K; 100 from MCS spreadsheet with 2 air changes, 88 with 1.5 changes (yr 2000+ build).
            "emitter_std_power": 5900,  # W @ dT(rad-room)=50C; current rads = 2.9kW + fan coil on high = 3kW
            "tmp_category": "Mid Medium",  # thermal mass parameter lookup name
            "floor_area": 28,  # kitchen = 26 + utility = 10
            # volume of circulating water (pipes + rads) in litres. Excl volumiser (option in UI)
            "fluid_volume": 22  # 7.5l for 20m x 22mm pipe; 6.5l for 600x1000 K2; 4l for 300x1200 K2
        },
        "Kitchen": {  # Current kitchen emitters for power output but h2o volume closer to intended. Actual room cooling rates are lower than sim with 88W/K and Mid-Medium
            "heat_loss_factor": 88,  # W/K; 100 from MCS spreadsheet with 2 air changes, 88 with 1.5 changes (yr 2000+ build).
            "emitter_std_power": 4500,  # W @ dT(rad-room)=50C; current rads = 2.9kW + kickspace at low speed = 1.7kW. Reduce slightly for cooler water in KS
            "tmp_category": "Mid Medium",  # thermal mass parameter lookup name.
            "floor_area": 28,  # kitchen = 26 + utility = 10
            # volume of circulating water (pipes + rads) in litres. Excl volumiser (option in UI)
            "fluid_volume": 22  # 7.5l for 20m x 22mm pipe; 6.5l for 600x1000 K2; 4l for 300x1200 K2
        },
        "Whole": {
            "heat_loss_factor": 215,  # W/K; 215 from MCS spreadsheet with "category B" ventilation rates (yr 2000 + build date).
            "emitter_std_power": 15500,  # W @ dT(rad-room)=50C; 12kW from rads + new fancoils in kitchen and bathroom *
            # * - kitchen max assume 3kW min 2.2kW; bathroom only use on low 650W. For cycling sims, use without fancoils (would be off if mild weather)
            "tmp_category": "Mid Medium",  # thermal mass parameter lookup name
            "floor_area": 80,
            # volume of circulating water (pipes + rads) in litres. Excl volumiser (option in UI)
            "fluid_volume": 45  # TODO NOT properly estimated !!
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
            # WM112
            "WM112_LWT35": {
                "LWT": 35,
                "dT": 5,
                "T_amb": (-15, -10, -7, 2, 7, 12, 15),
                "COP": (2.55, 2.75, 3.00, 3.44, 4.70, 6.05, 6.85),
                "capacity": 11200  # Watts
            },
            "WM112_LWT40": {
                "LWT": 40,
                "dT": 5,
                "T_amb": (-15, -10, -7, 2, 7, 12, 15),
                "COP": (2.30, 2.50, 2.75, 3.05, 4.20, 5.45, 6.15),
                "capacity": 11200  # Watts
            },
            "WM112_LWT45": {
                "LWT": 45,
                "dT": 5,
                "T_amb": (-15, -10, -7, 2, 7, 12, 15),
                "COP": (2.05, 2.25, 2.50, 2.74, 3.70, 4.85, 5.50),
                "capacity": 11200  # Watts
            },
            "WM112_LWT50": {
                "LWT": 50,
                "dT": 5,
                "T_amb": (-10, -7, 2, 7, 12, 15),
                "COP": (1.75, 1.90, 2.20, 2.30, 3.35, 4.20, 4.75),
                "capacity": 10600  # Watts
            },
            # this is about what the oil boiler does "full-on".
            # the mean flow temp is generally around 50 once room up to 15C or so
            "Direct_LWT60": {
                "LWT": 60,
                "dT": 8,
                "T_amb": (-10, 15),
                "COP": (1.0, 1.0),
                "capacity": 10000  # Watts
            },

            # Certification programme COPs. These are higher than Daikin capacity table COPs at full load
            # !!!! The Daikin data is rather sparse!!!!!!
            # Used EHPA (+BAFA for 10C) certification programme COPs from capacity tables in the Daikin Databook + SOME GUESSWORK (see below)
            "EDLA09_LWT35 Cert": {  # Sufficient data for this one. Curve roughly follows WM85 but is slightly higher
                "LWT": 35,
                "dT": 5,
                "T_amb": (-7, 2, 7, 10),
                "COP": (2.81, 3.79, 4.91, 5.32),
                "capacity": 6290  # Watts. Use minimum over all T_amb
            },
            "EDLA09_LWT40 Cert": {  # MADE UP to be between 35 and 45 (which is what WM85 data shows)
                "LWT": 40,
                "dT": 5,
                "T_amb": (-7, -2, 2, 7, 10),
                "COP": (2.51, 2.77, 3.37, 4.4, 4.6),
                "capacity": 6290  # Watts. Use minimum over all T_amb
            },
            # Used combination of MCS and EHPA certification programme COPs from capacity tables in the Daikin Databook.
            "EDLA09_LWT45 Cert": {  # very close to WM85 but the Daikin data ends at +7C, whereas the LWT=35 case and WM85 show we should not linear-extrapolate
                "LWT": 45,
                "dT": 5,
                "T_amb": (-7, -2, 7, 12),  # added 12C by analogy to WM85
                "COP": (2.22, 2.35, 3.71, 4.1),
                "capacity": 7760  # Watts. Use minimum over all T_amb
            },
            # only 2 points in data is dangerous straight line!
            "EDLA09_LWT55 Cert": {
                "LWT": 55,
                "dT": 8,
                "T_amb": (-7, 2, 7, 12),  # added points at 0C and 12C to match shape of LWT=45 and WM85
                "COP": (1.8, 2.25, 2.91, 3.05),
                "capacity": 7130  # Watts. Use minimum over all T_amb
            },

            # COPs computed from Daikin capacity tables. For EDLA09 there are no tabulated values for "optimised for sound", so these are estimated based on ratio for EDLA08
            # Capacity in Watts. Used minimum over all T_amb
            # As a rule, COPs are not at their maxiumum at full compressor load but "optimised for sound" may mean "100%" is not actually max compressor)
            "EDLA09_LWT35": {
                "LWT": 35,
                "dT": 5,
                "T_amb": (-7, -2, 2, 7, 12),
                "COP": (2.48, 2.73, 3, 4.82, 4.26),
                "capacity": 7200
            },
            "EDLA09_LWT40": {
                "LWT": 40,
                "dT": 5,
                "T_amb": (-7, -2, 2, 7, 12),
                "COP": (2.32, 2.54, 2.71, 3.99, 3.83),
                "capacity": 7700
            },
            "EDLA09_LWT45": {
                "LWT": 45,
                "dT": 5,
                "T_amb": (-7, -2, 2, 7, 12),
                "COP": (2.21, 2.38, 2.49, 3.43, 3.44),
                "capacity": 7900
            },
            "EDLA09_LWT55": {
                "LWT": 55,
                "dT": 5,
                "T_amb": (-7, -2, 2, 7, 12),
                "COP": (1.79, 1.92, 2.09, 3.32, 2.76),
                "capacity": 7900
            },

            # COP computed from Daikin capacity table (100% load, optimised for sound). Capacity in Watts. Used minimum over all T_amb
            # COPs are not at their maxiumum at full compressor load but "optimised for sound" may mean "100%" is not actually max compressor)
            "EDLA08_LWT35": {
                "LWT": 35,
                "dT": 5,
                "T_amb": (-7, -2, 2, 7, 12),
                "COP": (2.7, 3, 3.31, 4.53, 5.38),
                "capacity": 6300
            },
            "EDLA08_LWT40": {
                "LWT": 40,
                "dT": 5,
                "T_amb": (-7, -2, 2, 7, 12),
                "COP": (2.39, 2.68, 2.97, 3.94, 4.64),
                "capacity": 6500
            },
            "EDLA08_LWT45": {
                "LWT": 45,
                "dT": 5,
                "T_amb": (-7, -2, 2, 7, 12),
                "COP": (2.17, 2.42, 2.7, 3.48, 4.02),
                "capacity": 6000
            },
            "EDLA08_LWT55": {
                "LWT": 55,
                "dT": 8,
                "T_amb": (-7, -2, 2, 7, 12),
                "COP": (1.62, 1.82, 2.05, 2.87, 3.05),
                "capacity": 5200
            }
        }
    else:
        # vs LWT. Intended for cycling simulation. Capacities chosen for LWT=40 and are MINIMUM capacities
        cops = {
            # WM85 is approx 8kW capacity
            "WM85_AMB+12": {
                "T_amb": 12,
                "dT": 5,
                "LWT": (25, 35, 40, 45, 50, 55),
                "COP": (6.90, 6.05, 5.20, 4.40, 3.70, 3.05),
                "capacity": 2700  # Watts
            },
            "WM85_AMB+7": {
                    "T_amb": 7,
                    "dT": 5,
                    "LWT": (25, 35, 40, 45, 50, 55),
                    "COP": (5.95, 5.20, 4.45, 3.75, 3.20, 2.65),
                    "capacity": 3100  # Watts
            },
            "WM85_AMB+2": {
                    "T_amb": 2,
                    "dT": 5,
                    "LWT": (25, 35, 40, 45, 50, 55),
                    "COP": (4.65, 4.15, 3.65, 3.15, 2.75, 2.40),
                    "capacity": 3400  # Watts
            },
            "WM85_AMB-7": {
                "T_amb": -7,
                "dT": 5,
                "LWT": (25, 35, 40, 45, 50, 55),
                "COP": (2.70, 2.50, 2.30, 2.10, 1.85, 1.65),
                "capacity": 3200  # Watts
            },
            # WM112 is approx 11kW capacity
            "WM112_AMB+12": {
                "T_amb": 12,
                "dT": 5,
                "LWT": (25, 35, 40, 45, 50, 55),
                "COP": (6.3, 5.85, 5.4, 4.95, 4.3, 3.65),
                "capacity": 3800  # Watts
            },
            "WM112_AMB+7": {
                "T_amb": 7,
                "dT": 5,
                "LWT": (25, 35, 40, 45, 50, 55),
                "COP": (4.95, 4.45, 3.95, 3.50, 3.05, 2.60),
                "capacity": 3700  # Watts
            },
            "WM112_AMB+2": {
                "T_amb": 2,
                "dT": 5,
                "LWT": (25, 35, 40, 45, 50, 55),
                "COP": (4.25, 3.75, 3.25, 2.75, 2.4, 2.1),
                "capacity": 4000  # Watts
            },
            "WM112_AMB-7": {
                "T_amb": -7,
                "dT": 5,
                "LWT": (25, 35, 40, 45, 50, 55),
                "COP": (3.15, 2.85, 2.55, 2.30, 2.00, 1.70),
                "capacity": 3700  # Watts
            },
            # !!!! EDLA are probably NOT good to use because there are no tabulated COPs for the compressor running a min frequency, unlike Ecodan.
            # EDLA - 04-08 min input 300W? 09-16 min input 900W.
            # HOWEVER: looking at the Ecodan, its capacity at min freq is fairly constant over ambient temps, even though COP changes, so I suspect that
            # the HP varies its minimum compressor frequency, keeping it higher for lower ambient temps
            # Values taken from earlier "_LTW* Cert" entries, using the splines to fill in.
            "EDLA09_AMB+10": {
                "T_amb": 10,
                "dT": 5,
                "LWT": (35, 40, 45, 55),
                "COP": (5.32, 4.60, 4.10, 3.05),
                "capacity": 4000  # Watts. GUESS
            },
            "EDLA09_AMB+7": {
                "T_amb": 7,
                "dT": 5,
                "LWT": (35, 40, 45, 55),
                "COP": (4.91, 4.4, 3.71, 2.91),
                "capacity": 4000  # Watts. GUESS
            },
            "EDLA09_AMB+2": {
                "T_amb": 2,
                "dT": 5,
                "LWT": (35, 40, 45, 55),
                "COP": (3.79, 3.37, 2.90, 2.25),
                "capacity": 4000  # Watts. GUESS
            },
            "EDLA09_AMB-2": {
                "T_amb": -2,
                "dT": 5,
                "LWT": (35, 40, 45, 55),
                "COP": (3.19, 2.77, 2.35, 1.92),
                "capacity": 4000  # Watts. GUESS
            },
            "EDLA09_AMB-7": {
                "T_amb": -7,
                "dT": 5,
                "LWT": (35, 40, 45, 55),
                "COP": (2.81, 2.51, 2.22, 1.8),
                "capacity": 4000  # Watts. GUESS
            },
            "EDLA08_AMB+10": {
                "T_amb": 10,
                "dT": 5,
                "LWT": (35, 40, 45, 55),
                "COP": (4.72, 4.45, 3.80, 2.84),
                "capacity": 1400  # Watts. GUESS
            },
            "EDLA08_AMB+7": {
                "T_amb": 7,
                "dT": 5,
                "LWT": (35, 40, 45, 55),
                "COP": (4.6, 4.2, 3.5, 2.7),
                "capacity": 1400  # Watts. GUESS
            },
            "EDLA08_AMB+2": {
                "T_amb": 2,
                "dT": 5,
                "LWT": (35, 40, 45, 55),
                "COP": (3.65, 3.17, 2.75, 2.1),
                "capacity": 1400  # Watts. GUESS
            },
            "EDLA08_AMB-2": {
                "T_amb": -2,
                "dT": 5,
                "LWT": (35, 40, 45, 55),
                "COP": (3.07, 2.7, 2.39, 1.81),
                "capacity": 1400  # Watts. GUESS
            },
            "EDLA08_AMB-7": {
                "T_amb": -7,
                "dT": 5,
                "LWT": (35, 40, 45, 55),
                "COP": (2.7, 2.4, 2.21, 1.7),
                "capacity": 1400  # Watts. GUESS
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
        "Mild Winter": [
            5.5,  # 00
            5,  # 03
            5,  # 06
            7,  # 09
            10,  # 12
            10,  # 15
            7,  # 18
            6  # 21
        ],
        "Coldish Winter": [
            1.0,  # 00
            0,  # 03
            -2,  # 06
            -1,  # 09
            1.5,  # 12
            2.5,  # 15
            2,  # 18
            1.5  # 21
        ],
        "Cold Snap": [
            -6,  # 00
            -7,  # 03
            -8,  # 06
            -7,  # 09
            -3,  # 12
            -2,  # 15
            -4,  # 18
            -5  # 21
        ],
        "Spring": [
            5,  # 00
            5,  # 03
            5,  # 06
            8,  # 09
            13,  # 12
            12,  # 15
            8,  # 18
            6  # 21
        ],
        "Spring Clear": [
            5,  # 00
            2,  # 03
            1,  # 06
            5,  # 09
            13,  # 12
            15,  # 15
            12,  # 18
            6.5  # 21
        ],
        "Constant 10": [10.0] * 8,
        "Constant 7": [7.0] * 8,
        "Constant 4": [4.0] * 8,
        "Constant 2": [2.0] * 8,
        "Constant -2": [-2.0] * 8,
        "Constant -7": [-7.0] * 8
    }
    return amb


# Inside target temperatures. These are the defaults which users can play around with using slider controls.
# make all entries 2 chars wide for visual
def get_target_temp_options():
    tt = {
        #    00, 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23
        "Moderate Burst":  # Our current CH controller default profile but with rounding off the 0.5 settings
            [14,  5,  5,  5,  5,  5,  5, 12, 13, 15, 16, 14, 14, 14, 14, 15, 15, 16, 16, 16, 17, 17, 16, 15],
        "Daytime 17":  # A guess at a reasonable economical profile for an ASHP, adopting "steady principle"
            [12] * 6 + [13, 14, 15, 16] + [17] * 14,
        "Constant 14": [14] * 24,
        "Constant 16": [16] * 24,
        "Constant 18": [18] * 24,
        "Constant 21": [21] * 24
    }
    return tt


def get_tmp_options():
    """Thermal mass parameter. Units kJ.m^-2.K^-1"""
    tmp = {
        "Low": 90,
        "Lower Medium": 110,
        "Mid Medium": 150,
        "Upper Medium": 200,
        "High": 300,
        "Very High": 450
    }
    return tmp
