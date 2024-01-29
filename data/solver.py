import numpy as np
from math import fabs

from utilities import Radiator, COP, AmbientTemps, TargetTemp
from config import get_cop_point_options, get_ambient_hr_options


class RoomTempSolver:
    def __init__(self, building_parameters, cop_option, amb_option, target_temps_hourly, passive_heat=0, initial_temp=16, steps_per_hour=6):
        """
        Computes room temperature against time and associated performance statistics for a target set of room temperatures, given
        building, ambient outside temperatures (varying with time), and heat pump properties.

        :param building_parameters: dict with same keys as returned by get_building_defaults() except that there should be a "tmp" key with a value for thermal mass parameter
        :param cop_option: key into return from get_cop_point_options()
        :param amb_option: key into return from get_ambient_hr_options()
        :param target_temps_hourly: list of target temps for each hour
        :param passive_heat: passive heating (people, computers, etc) in W
        :param initial_temp: starting temp
        :param steps_per_hour: number of steps per hour in the solver and for the iter_* variables.
        """
        cop_defn = get_cop_point_options()[cop_option]
        amb_defn = get_ambient_hr_options()[amb_option]

        # building setup
        self.heat_loss_factor = building_parameters["heat_loss_factor"]
        self.emitter = Radiator(building_parameters["emitter_std_power"], cop_defn["LWT"] - cop_defn["dT"] / 2)
        self.heat_capacity = building_parameters["tmp"] * building_parameters["floor_area"] / 3.6  # Watt.hours per Kelvin

        # other setup
        self.steps_per_hour = steps_per_hour
        self.time_step_duration = 1 / steps_per_hour
        self.hysteresis = 0.5  # interval between on and off temps for a given target
        self.cop_model = COP(cop_defn["T_amb"], cop_defn["COP"])
        self.passive_heat = passive_heat

        # current state
        self.heating_on = False
        self.current_temp = initial_temp

        # time series after last iteration. lists of length 24 * steps_per_hour
        iter_steps = 24 * steps_per_hour
        self.iter_room_temp = [initial_temp] * iter_steps  # used to record temps at each iteration to check for convergence
        self.iter_elec_used = [0] * iter_steps

        # Convenient to get a list of ambient temperatures etc to match the iter_* data. Used internally and useful for plotting
        amb_model = AmbientTemps(amb_defn)
        target_temp_lookup = TargetTemp(target_temps_hourly)
        self.times = list(np.arange(0, 24, 1 / steps_per_hour))
        self.ambient_temps = [amb_model.temp(hr) for hr in self.times]
        self.cops = list()  # this gets updated each iteration so that NAs are applied when the heating is not on. THIS IS RELIED ON in Dash app
        self.target_temps = [target_temp_lookup.temp(hr) for hr in self.times]

        # use as a "result" and to assess convergence
        self.full_day_energy = 0  # kWh
        self.full_day_energy_delta = 99  # absolute change

        # use to assess convergence. These are ABSOLUTE changes, i.e. |delta|
        # Beware that max_t_iter_delta (in particular) can show instability. I suspect this is down to switch on/off events landing in different time slices.
        # This can be mitigated by increasing the number of steps per hour.
        self.max_t_iter_delta = 99
        self.mean_t_iter_delta = 99
        # and an iteration counter for non-convergence exit
        self.n_iterations = 0

    def iterate(self):
        max_t_iter_delta = 0
        sum_t_iter_delta = 0
        self.n_iterations += 1
        self.cops = list()

        for ix, hr in enumerate(self.times):
            amb = self.ambient_temps[ix]
            cop = self.cop_model.cop(amb)
            target = self.target_temps[ix]
            t = self.current_temp

            if t >= target + self.hysteresis / 2:
                self.heating_on = False
            else:
                if not self.heating_on:
                    self.heating_on = target - t > self.hysteresis / 2

            # heat loss and supplied by emitter
            lost = self.heat_loss_factor * (self.current_temp - amb) * self.time_step_duration
            if self.heating_on:
                self.cops.append(cop)
                emitted = self.emitter.output(t) * self.time_step_duration  # Watt.hours
                elec_used = emitted / cop
            else:
                self.cops.append(None)
                emitted = 0
                elec_used = 0

            room_temp_change = (emitted - lost + self.passive_heat * self.time_step_duration) / self.heat_capacity
            self.current_temp += room_temp_change
            room_temp_iter_delta = fabs(self.iter_room_temp[ix] - self.current_temp)
            max_t_iter_delta = max(max_t_iter_delta, room_temp_iter_delta)
            sum_t_iter_delta += room_temp_iter_delta

            self.iter_room_temp[ix] = self.current_temp
            self.iter_elec_used[ix] = elec_used

        self.max_t_iter_delta = max_t_iter_delta
        self.mean_t_iter_delta = sum_t_iter_delta / len(self.times)

        energy_kwh = sum(self.iter_elec_used) / 1000
        self.full_day_energy_delta = fabs(self.full_day_energy - energy_kwh)
        self.full_day_energy = energy_kwh


class CyclingSolver:
    def __init__(self, building_parameters, cop_option, lwt, hp_capacity, initial_temp, lwt_overshoot=4, steps_per_minute=5):
        """
        Computes HP on/off cycles and system fluid temp (actual LWT) against time and associated performance statistics for a variable HP capacity and max LWT,
        given building, fixed ambient outside temperatures, and heat pump properties.

        The HP is assumed to be working at a fixed compressor frequency. For scenarios of interest this is expected to be the manufacturer's minimum
            inverter frequency capacity and cop_option values should correspond with this.

        :param building_parameters: dict with same keys as returned by get_building_defaults() except that there should be a "tmp" key with a value for thermal mass parameter
        :param cop_option: key into return from get_cop_point_options(vs="lwt"), which also gives fixed ambient temp
        :param lwt: LWT which the HP is aiming at. It will switch off when this is reached.
        :param hp_capacity: output power in Watts of the HP
        :param initial_temp: starting room temp
        :param steps_per_minute: number of steps per minute in the solver and for the iter_* variables.
        """
        cop_defn = get_cop_point_options(vs="lwt")[cop_option]
        self.cop_model = COP(cop_defn["LWT"], cop_defn["COP"])
        self.hp_dT = cop_defn["dT"]
        self.ambient_temp = cop_defn["T_amb"]

        # building setup
        self.heat_loss_factor = building_parameters["heat_loss_factor"]
        self.emitter = Radiator(building_parameters["emitter_std_power"], lwt - cop_defn["dT"] / 2)
        self.heat_capacity = building_parameters["tmp"] * building_parameters["floor_area"] / 3.6  # Watt.hours per Kelvin
        self.fluid_volume = building_parameters["fluid_volume"]  # litres

        # other setup
        self.time_step_secs = 60 / steps_per_minute
        self.lwt = lwt  # this is the desired, not necessarily the actual lwt
        self.hp_capacity = hp_capacity
        self.lwt_overshoot = lwt_overshoot  # difference above max_lwt at which the HP will switch off.

        # current state
        self.cycle_start_room_temp = initial_temp

        # time series after last iteration. Unknown length but limited to max_steps
        self.max_steps = 600  # for shorter cycle periods, steps_per_minute should be higher and vice versa
        self.times_mins = list()  # mins into cycle for each step.
        self.cycle_flow_temp = list()  # used to record flow temps for each iteration. This is the flow temp at the start of each time step
        self.cycle_return_temp = list()
        self.mean_emitter_temp = list()
        self.cycle_elec_used = list()  # elec used during the step in W.h
        self.cycle_cop = list()  # COP based on the flow temp at the start of the step
        self.cycle_room_temp = list()
        self.cycle_emitter_output = list()
        # aggregate for cycle
        self.on_duration = None
        self.off_duration = None

        # use to test for convergence. These are ABSOLUTE changes, i.e. |delta|
        self.iter_room_temp_delta = 99
        # and an iteration counter for non-convergence exit
        self.n_iterations = 0

    def iterate(self):
        """
        Computes flow temps for a single cycle (of unspecified duration but subject to a software limit!).
        The difference in room temperature (at the start of a cycle) at the start and end of an iteration is available as a sign of convergence.
        :return:
        """
        self.n_iterations += 1
        self.times_mins = list()
        self.cycle_flow_temp = list()
        self.cycle_return_temp = list()
        self.mean_emitter_temp = list()
        self.cycle_elec_used = list()
        self.cycle_cop = list()
        self.cycle_room_temp = list()
        self.cycle_emitter_output = list()
        # reset to None so they can be used to detect exceeding max steps
        self.on_duration = None  # minutes
        self.off_duration = None

        room_temp = self.cycle_start_room_temp
        # start cycle as it should end
        return_temp = self.lwt - self.hp_dT
        flow_temp = return_temp
        mean_emitter_temp = self.lwt - 3 * self.hp_dT / 4
        heating_on = True

        step = 0
        # NB unit of time in steps is seconds self.time_step_secs
        while step < self.max_steps:
            step += 1
            self.times_mins.append(step * self.time_step_secs / 60)

            # Emitter to room.
            emitter_output = self.emitter.output(room_temp, mean_emitter_temp)
            energy_from_fluid = self.time_step_secs * emitter_output

            # HP input. Could add circulation pump input too.
            if heating_on:
                cop = self.cop_model.cop(flow_temp)
                # hackery to get initial heating boost.
                boost = 0 if flow_temp > self.lwt - 1 else self.hp_capacity * (self.lwt - flow_temp + self.hp_dT / 2) / self.hp_dT
                energy_to_fluid = self.time_step_secs * (self.hp_capacity + boost)  # Joules
                self.cycle_cop.append(cop)
                self.cycle_elec_used.append(energy_to_fluid / 3600 / cop)  # to Watt.hours
                # update fluid temp
                flow_temp += energy_to_fluid / (4.2 * self.fluid_volume * 1000)
                met_delta = (energy_to_fluid - energy_from_fluid) / (4.2 * self.fluid_volume * 1000)
                mean_emitter_temp += met_delta
                # funky guesswork at return temp. avoid having flow rate explicit
                return_temp = max(flow_temp - self.hp_dT, return_temp + met_delta / 2)
            else:
                self.cycle_cop.append(None)
                self.cycle_elec_used.append(0)
                # update fluid temp
                met_delta = energy_from_fluid / (4.2 * self.fluid_volume * 1000)
                mean_emitter_temp -= met_delta
                return_temp -= met_delta / 2
                flow_temp = return_temp

            self.cycle_emitter_output.append(emitter_output)
            self.cycle_flow_temp.append(flow_temp)
            self.cycle_return_temp.append(return_temp)
            self.mean_emitter_temp.append(mean_emitter_temp)
            self.cycle_room_temp.append(room_temp)

            # update room temperature. NB these are in Watt.hours
            room_lost = self.heat_loss_factor * (room_temp - self.ambient_temp) * self.time_step_secs / 3600
            room_gained = energy_from_fluid / 3600
            room_temp_change = (room_gained - room_lost) / self.heat_capacity
            room_temp += room_temp_change

            # check if the max LWT was reached => turn compressor off
            if flow_temp > self.lwt + self.lwt_overshoot:
                heating_on = False
                self.on_duration = step * self.time_step_secs / 60
            # if the heating is off and we've got below the desired, the cycle has ended
            elif (return_temp < self.lwt - self.hp_dT) and not heating_on:
                print(f"Cycle ended after {step} steps")
                self.off_duration = step * self.time_step_secs / 60 - self.on_duration
                break

        if step == self.max_steps:
            print("Reached MAX STEPS!")

        # these will be bad if exit was due to max steps being reached
        self.iter_room_temp_delta = fabs(self.cycle_start_room_temp - room_temp)
        self.cycle_start_room_temp = room_temp
