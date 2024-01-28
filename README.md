# Thermal Sims
## Efficient Heating 
### RoomTempSolver
Looks at the effect of different LWT, outside temperatures, and inside target temperatures profiles on overall energy requirement and the extent to which the
target temperatures are met.

Assumptions:
- the ASHP operates at a fixed dT (return - leaving water temp). A dT of 5C is often given in data and should be close to best operating value. Setting larger dT probably reduced overall efficiency, with better effect achieved from reducing flow temp, see bottom https://heatpumps.co.uk/cop-estimator/.

Simplifications:
- a single emitter + single envelope model.
- no heating or cooling phase for the emitters and heating water.

### CyclingSolver

Simplifications:
- the model switches heating off when the LWT reaches the specified LWT + a variable overshoot then switches it on again when the LWT falls below its setting. This is based on what I can glean from Daikin operation manual but is probably an over-simplification.
- the HP only uses minimum power. This is probably a poor simplification; I suspect it will start the cycle at higher power.
