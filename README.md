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

### Command line Tools

#### Control the unit directy

```sh
./korad_control.py --volts 3.3 --curr 0.2 --enable
```
Sets the output voltage to 3.3, the maximum output current to
200mA, and turns on the output.

Something silly you can do it make the PSU tell the time:

```sh
./korad3005p.py --clock
```

This disables the output and puts the time on the volts
display and the seconds on the current display. The program
will not exit until you CTRL-C.

#### Logging

```sh
./korad_log.py --output foo.csv
```

Samples the status of the PSU at regular interviews (that you can specify)
and writes the results to a csv file.

#### Battery Charging

```sh
./korad_charge.py --capacity 2.5
```

Set up to charge Li-Ion batteries, this will set up the PSU for a
maximum voltage of 4.175 v (default) and a maximum charge rate of
the specified capacity times 0.5 (default).

It will charge and log the progress, and then disable the unit when
the current drops below 0.02 "C"

All these paremeters have reasonable defaults for Li-Ion, but they
can all be overridden. See `--help`.

