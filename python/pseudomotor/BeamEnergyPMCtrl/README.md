# Beam Energy Pseudomotor Controllers

The aim of this controller library is to provide a set of stackable pseudomotors to change the beamline energy.

The library needs a set of helper functions with the hardware characterization.
These functions has to be implemented in **undulator.py** and **mono.py**.
Examples of these files can be found in the examples directory.

Once the controller is installed, one has to add the helpers path in the PoolPath property.
