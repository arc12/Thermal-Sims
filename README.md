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
- the model switches heating off when the LWT reaches a specified max. This isn't how a real pump is expected to work* but leads to a cyclic behaviour which is the objective.

(* - A real HP is expected to modulate flow downwards to attempt to keep the returning temp down, until a minimum flow threshold)