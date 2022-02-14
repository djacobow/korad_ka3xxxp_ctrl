#!/usr/bin/env python3

import datetime
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


