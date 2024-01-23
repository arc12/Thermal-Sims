from utilities import COP, AmbientTemps
from config import get_cop_point_options, get_ambient_hr_options, get_tmp_options, get_building_default_options, get_target_temp_options
import plotly.express as px
import numpy as np

from data.solver import RoomTempSolver, CyclingSolver

building_parameters = get_building_default_options()["Kitchen"]
building_parameters["tmp"] = get_tmp_options()[building_parameters["tmp_category"]]

building_parameters["fluid_volume"] += 35  # add a volumiser

solver = CyclingSolver(building_parameters,
                       cop_option="WM85_AMB+7",
                       max_lwt=40,
                       hp_capacity=2400,  # set in config but will be over-ridable in UI
                       initial_temp=14,
                       steps_per_minute=10)

while solver.iter_room_temp_delta > 0.05:
    solver.iterate()
    print(solver.iter_room_temp_delta)
    print("-----")
print(solver.on_duration, solver.off_duration)
cycle_duration_hrs = (solver.on_duration + solver.off_duration) / 60
print(f"{1/cycle_duration_hrs:.1f} starts per hour")
print(sum(solver.cycle_elec_used))
print(solver.cycle_start_room_temp)

print(f"Mean Room Temp/C = {sum(solver.cycle_room_temp) / len(solver.cycle_room_temp)}")

fig = px.line(x=solver.times_mins, y=solver.cycle_flow_temp, title="Flow Temp/C")
fig.show()

fig = px.line(x=solver.times_mins, y=solver.cycle_room_temp, title="Room Temp/C")
fig.show()
# this is per cycle, which is not very useful.
# print("Total Energy/kWh:", sum(solver.cycle_elec_used) / 1000)
# mean input power/W over cycle = mean steady state power
print(f"Mean Input Power/W = {sum(solver.cycle_elec_used) / cycle_duration_hrs}")

power = [e / solver.time_step_secs * 3600 for e in solver.cycle_elec_used]  # Wh to W
fig = px.line(x=solver.times_mins, y=power, title="Input Power/W")
fig.show()
fig = px.line(x=solver.times_mins[:len(solver.cycle_cop)], y=solver.cycle_cop, title="COP")
fig.show()
#
# power_out = [p * cop for p, cop in zip(power, solver.cops)]
# fig = px.line(x=solver.times, y=power_out, title="ASHP Output Power/W")
# fig.show()


# solver = RoomTempSolver(building_parameters,
#                         cop_option="WM85_LWT40",
#                         amb_option="Winter",
#                         target_temps_hourly=get_target_temp_options()["Moderate Burst"],
#                         initial_temp=14,
#                         steps_per_hour=6)
#
# while solver.max_t_iter_delta > 0.1:
#     solver.iterate()
#     print(solver.max_t_iter_delta, solver.mean_t_iter_delta)
#     print("-----")
# print([round(t, 1) for t in solver.iter_room_temp])
# fig = px.line(x=solver.times, y=solver.iter_room_temp, title="Room Temp/C")
# fig.show()
# print("Total Energy/kWh:", sum(solver.iter_elec_used) / 1000)
# power = [e / solver.time_step_duration for e in solver.iter_elec_used]  # Wh to W
# fig = px.line(x=solver.times, y=power, title="Input Power/W")
# fig.show()
# fig = px.line(x=solver.times, y=solver.cops, title="COP")
# fig.show()
#
# power_out = [p * cop for p, cop in zip(power, solver.cops)]
# fig = px.line(x=solver.times, y=power_out, title="ASHP Output Power/W")
# fig.show()

# >>>>>>>>>>> Ambient Temp
# amb_curve = "Mildish Winter"
#
# amb_data = get_ambient_hr_options()[amb_curve]
# print(amb_data)
# amb_est = AmbientTemps(amb_data)
#
# hrs = np.arange(0, 25, 0.5)
# temps = [round(amb_est.temp(hr), 2) for hr in hrs]
#
# print(temps)
#
# fig = px.line(x=hrs, y=temps, title=amb_curve)
# fig.show()

# >>>>>>>> COP
#
# cop_curve = "WM85_LWT45"
#
# cop_data = get_cop_point_options()[cop_curve]
# print(cop_data)
# cop_est = COP(cop_data["T_amb"], cop_data["COP"])
#
# ats = range(-10, 21)
# cops = [round(cop_est.cop(T), 2) for T in ats]
#
# print(cops)
#
# fig = px.line(x=ats, y=cops, title=cop_curve)
# fig.show()