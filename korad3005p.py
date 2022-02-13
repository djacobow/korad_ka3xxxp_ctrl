#!/usr/bin/env python3

import argparse
import datetime
import json
import re
import serial
import time

#
# Simple Korad PSU control library
#
# Author  : Dave Jacobowitz
# Version : 0 (Feb 2022)
#
# Free to use by any and all, with attribution.

"""
Commands cribbed from:
    https://sigrok.org/wiki/Korad_KAxxxxP_series#Protocol
"""


class Korad3005p(object):
    def __init__(self, port = 'COM3', speed = 9600, timeout=2):
        self.s = serial.Serial(port, speed, timeout=timeout)
        self._cmdb('')
        init_str = self._cmds('*IDN?')
        if init_str is None:
            raise Exception('Could not get response from PSU')

        m = re.search(r'KORAD KA(\d+)P V(\d+\.?\d+) SN:(\d+)', init_str)
        if not m:
            raise Exception(f'Could not identify a Korad PSU: {init_str}')
        self.hw = {
            'version': m[2],
            'model':   'KA' + m[1] + 'P',
            'serial':  m[3],
        }

    def _append10(self, c, t):
        return ''.join([c,'1' if t else '0'])

    def enable(self, on=True): 
        self._cmdbn(self._append10('OUT',on))

    def disable(self, off=True):
        self.enable(on = not off)

    def enableOVP(self, on=True):
        self._cmdbn(self._append10('OVP',on))

    def enableOCP(self, on=True):
        self._cmdbn(self._append10('OCP',on))

    def setVolts(self, v):
        self._cmdbn(f'VSET1:{v:.2f}')

    def setCurr(self, i = 0):
        self._cmdbn(f'ISET1:{i:.2f}')

    def _slew(self, what, end, count, duration):
        s = self.status()
        start = s['settings'][what]

        incr = (end - start) / count
        time_step = duration / count
        v = start

        fn = None
        if what == 'volts':
            fn = self.setVolts
        elif what == 'curr':
            fn = self.setCurr
        else:
            raise Exception(f'No function found. What was {what}')

        for i in range(count):
            v += incr
            v = int(v * 1000 + 0.5) / 1000
            if fn:
                fn(v)
            time.sleep(time_step)

        if fn:
            fn(end)

    def slewVolts(self, end_v, count = 20, duration = 5):
        return self._slew('volts', end_v, count, duration)

    def slewCurr(self, end_v, count = 20, duration = 5):
        return self._slew('curr', end_v, count, duration)

    def m_store(self, n):
        if (n > 0) and (n <= 5):
            self._cmdbn(f'SAV{n}')

    def m_recall(self, n):
        if (n > 0) and (n <= 5):
            self._cmdbn(f'RCL{n}')

    def showTime(self):
        self.disable()
        now = time.localtime()
        t_num = now.tm_hour
        t_num += now.tm_min / 100
        i_num = now.tm_sec / 100
        self.setVolts(t_num)
        self.setCurr(i_num)

    def status(self):
        s = self._cmdb('STATUS?')
        if s is None:
           raise Exception('Could not get PSU status')
        s_byte = s[0]

        now = datetime.datetime.now()
        timestamps = {
            'iso': now.isoformat(),
            'epoch': now.timestamp(),
        }

        trk_bits = (s_byte >> 2) & 0x3
        status = {
            'ch0_mode': 'CV' if s_byte & 0x1 else 'CC',
            'ch1_mode': 'CV' if s_byte & 0x2 else 'CC',
            'tracking': 'independent' if trk_bits == 0 else ('parallel' if trk_bits == 0x3 else 'series'),
            'beep': True if s_byte & 0x10 else False,
            'lock': True if s_byte & 0x20 else False,
            'output': True if s_byte & 0x40 else False,
        }
        settings = {
            'volts': float(self._cmds('VSET1?')),
            'curr': float(self._cmds('ISET1?')),
        }
        v = float(self._cmds('VOUT1?'))
        i = float(self._cmds('IOUT1?'))
        output = {
            'volts': v,
            'curr': i,
            'power': v * i,
        }
        return {
            'status': status,
            'settings': settings,
            'output': output,
            'hw': self.hw,
            'time': timestamps,
        }

    def _cmdbn(self,c):
        s = c + '\n'
        # print(f'==> {s}')
        b = s.encode('ascii',errors='ignore')
        self.s.write(b)

    def _cmdb(self,c):
        self._cmdbn(c)
        return self.s.readline()

    def _cmds(self, c):
        return self._cmdb(c).decode('ascii',errors='ignore')



class KoradApp(object):
    def __init__(self):
        self.args = self.getArgs()
        self.k = Korad3005p(self.args.port, self.args.speed, self.args.timeout)

    def getArgs(self):
        parser = argparse.ArgumentParser(description='Korad Command Line Tool')
        parser.add_argument(
            '--port','-p',
            type=str,
            help='Unit\'s serial port',
            default='COM3'
        )
        parser.add_argument(
            '--speed','-s',
            type=int,
            default=9600,
            help='Unit\'s serial speed',
        )
        parser.add_argument(
            '--timeout','-t',
            type=int,
            default=1,
            help='serial interface timeout',
        )

        parser.add_argument(
            '--volts','-v',
            type=float,
            default=None,
            help='specify output voltage',
        )

        parser.add_argument(
            '--curr','-i',
            type=float,
            default=None,
            help='specify output (max) current',
        )

        parser.add_argument(
            '--slew',
            nargs=2,
            type=int,
            metavar=('COUNT','TIME'),
            default=None,
            help='slew V or I taking COUNT steps over TIME duration',
        )

        output_g = parser.add_mutually_exclusive_group()

        output_g.add_argument(
            '--enable','-e',
            action='store_true',
            help='enable output',
        )

        output_g.add_argument(
            '--disable','-d',
            action='store_true',
            help='disable output',
        )

        status_g = parser.add_mutually_exclusive_group()

        status_g.add_argument(
            '--status','-g',
            action='store_true',
            help='read and print status',
        )

        status_g.add_argument(
            '--json','-j',
            action='store_true',
            help='print status as json blob',
        )

        status_g.add_argument(
            '--clock','-c',
            action='store_true',
            help='make the psu tell the time',
        )


        memory_g = parser.add_mutually_exclusive_group()

        memory_g.add_argument(
            '--recall','-r',
            type=int,
            choices=(1,2,3,4,5),
            default=None,
            help='recall stored setting'
        )
        memory_g.add_argument(
            '--store',
            type=int,
            choices=(1,2,3,4,5),
            default=None,
            help='save settings'
        )

        ocp_g = parser.add_mutually_exclusive_group()

        ocp_g.add_argument(
            '--ocp-on',
            action='store_true',
            help='enable overcurrent protection',
        )
        ocp_g.add_argument(
            '--ocp-off',
            action='store_true',
            help='disable overcurrent protection',
        )

        ovp_g = parser.add_mutually_exclusive_group()

        ovp_g.add_argument(
            '--ovp-on',
            action='store_true',
            help='enable overvoltage protection',
        )
        ovp_g.add_argument(
            '--ovp-off',
            action='store_true',
            help='disable overvoltage protection',
        )

        return parser.parse_args()
       
    def showStatus(self):
        s = self.k.status()
        f0 = 'Hardware : Model {model} / FW Ver {version} / Serial# {serial}'
        print(f0.format(**s['hw']))
        f1 = 'Set      : {volts:.2f} V, {curr:.3f} A'
        f2 = 'Meas     : {volts:.2f} V, {curr:.3f} A, {power:.2f} W'
        print(f1.format(**s['settings']))
        print(f2.format(**s['output']))
        f3 = 'Status   : Output {onoff}, Mode {ch0_mode}'
        s['status']['onoff'] = 'ON' if s['status']['output'] else 'OFF'
        print(f3.format(**s['status']))


    def go(self):
        if self.args.volts is not None:
            if self.args.slew is not None:
                self.k.slewVolts(self.args.volts, self.args.slew[0], self.args.slew[1])
            else:
                self.k.setVolts(self.args.volts)

        if self.args.curr is not None:
            if self.args.slew is not None:
                self.k.slewCurr(self.args.curr, self.args.slew[0], self.args.slew[1])
            else:
                self.k.setCurr(self.args.curr)

        if self.args.enable:
            self.k.enable(True)

        if self.args.disable:
            self.k.disable(True)

        if self.args.ovp_on:
            self.k.enableOVP(True)

        if self.args.ovp_on:
            self.k.enableOVP(False)

        if self.args.ocp_on:
            self.k.enableOCP(True)

        if self.args.ocp_on:
            self.k.enableOCP(False)

        if self.args.recall is not None:
            self.k.m_recall(self.args.recall)

        if self.args.store is not None:
            self.k.m_store(self.args.store)

        if self.args.json:
            print(json.dumps(self.k.status(), indent=2, sort_keys=True))
        if self.args.status:
            self.showStatus()

        if self.args.clock:
            while True:
                self.k.showTime()
                time.sleep(1)

     
    def enableOVP(self, on=True):
        self._cmdbn(self._append10('OVP',on))

    def enableOCP(self, on=True):
        self._cmdbn(self._append10('OCP',on))

if __name__ == '__main__':

    a = KoradApp()
    a.go()
