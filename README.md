# korad_ka3xxxp_ctrl

Simple python library and command-line utility for controlling Korad PSUs

## Why?

There are many other bits of code out there to control these units,
but I wanted one that was simple and coded per my preferences.

The only dependency is on `serial`.

## How

You can use this one of two ways. 

### Library

First, you can use it as a library:

```python3
import korad3005p

psu = korad3005p.Korad3005p(port='/dev/ttyUSB2')

psu.setVolts(3.3)
psu.setCurr(0.2)
psu.enable()
...
```

### Command line

Or, you can use it from the command line:

```sh
./korad3005p.py --volts 3.3 --curr 0.2 --enable
```

Use `--help` to see all the potential options.

#### Fun

A pointless trick mode is to turn your PSU into a clock:

```sh
./korad3005p.py --clock
```

This disables the output and puts the time on the volts
display and the seconds on the current display. The program
will not exit until you CTRL-C.

## Logging

There is a companion program, `logcsv.py` which uses the Korad controller as a
library and simply logs status to a csv file at the rate and duration you
specify. Very simple, but works nicely for getting some charts.

