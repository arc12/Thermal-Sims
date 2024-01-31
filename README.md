# Thermal Sims
## Efficient Heating 
### Room Temp Solver
Looks at the effect of different LWT, outside temperatures, and inside target temperatures profiles on overall energy requirement and the extent to which the
target temperatures are met.

Assumptions:
- the ASHP operates at a fixed dT (return - leaving water temp). A dT of 5C is often given in data and should be close to best operating value. Setting larger dT probably reduced overall efficiency, with better effect achieved from reducing flow temp, see bottom https://heatpumps.co.uk/cop-estimator/.

Simplifications:
- a single emitter + single envelope model.
- no heating or cooling phase for the emitters and heating water.

### Cycling Solver
This is very much a symbolic simulation which is not fit for assessing the effect on COP of cycling. The difficulty of making it realistic is that to do so would require a knowledge of the HP algorithm for regulating water flow and compressor frequency.
A realistic treatment would have to include flow and mixing, and pipework and emitter details.

The approach taken is crudely influenced by the Daikin "overshoot" configurable parameter; the documentation says the HP will stop heating when LWT overshoots by this much and resume when it has fallen to the desired LWT.
The model is to have a body of water which is heated from the desired LWT up to the overshoot and then allowed to cool again by emission to the building, with the cycle ending when the water temperature returns to the desired LWT.

Simplifications:
- as above except that the overshoot and end-cooling condition is computed from the mean water temperature with a constant dT assumption, which is not realistic.
- the HP only uses minimum power. This is probably a poor simplification; I suspect it will start the cycle at higher power.

### Constant LWT
This answers the question: what will the room temperature look like for a constant supply of hot water to emitters, given an outside temperature pattern. The assumptions and simplifications are as for Room Temp Solver

## Notes for Anyone!
Take it will with a pinch of salt.

Read the code comments, including those in config.py, which has caveats on the COP data.

I will generally not provide help on getting this stuff running but will happily engage with anyone with ideas for improvements and extensions (etc).