#!/usr/bin/env python3

import argparse
import json
import time

import korad3005p

class KoradApp(object):
    def __init__(self):
        self.args = self.getArgs()
        self.k = korad3005p.Korad3005p(self.args.port, self.args.speed, self.args.timeout)

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
