#!/usr/bin/env python3

import argparse
import csv
import time
import re
import signal
import sys

import korad3005p

class KoradLipoCharger(object):
    def __init__(self):
        self.args = self.getArgs()
        self.k = korad3005p.Korad3005p(self.args.port, self.args.speed, self.args.timeout)
        signal.signal(signal.SIGINT, self.graceful_exit)
        self.ofh = None
        self.csvw = None

    def graceful_exit(self, signum, frame):
        print('Caught SIGINT. Exiting')
        self.k.disable()

        if self.ofh:
            try:
                self.ofh.close()
            except Exception as e:
                pass
     
        sys.exit(1)


    def getArgs(self):
        parser = argparse.ArgumentParser(description='Korad LiPo Charger')

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
            '--capacity','-c',
            type=float,
            default=None,
            required=True,
            help='Battery capacity in Ah'
        )
        parser.add_argument(
            '--rate','-r',
            type=float,
            default=0.5,
            help='Max charge rate in "C"'
        )
        parser.add_argument(
            '--volts','-v',
            type=float,
            default=4.175,
            help='CC/CV transition voltage'
        )
        parser.add_argument(
            '--cutoff','-e',
            type=float,
            default=0.02,
            help='completion cutoff in "C"',
        )
        parser.add_argument(
            '--max-time','-m',
            type=int,
            default=4,
            help='maximum charge time in hours',
        )
        parser.add_argument(
            '--check-interval','-i',
            type=int,
            default=60,
            help='how often to check charge, in seconds',
        )
        parser.add_argument(
            '--log','-l',
            type=str,
            default=None,
            help='name of file to log to',
        )
        return parser.parse_args()

    def charge(self):
        self.k.disable()
        cc_current  = self.args.capacity * self.args.rate
        eoc_current = self.args.capacity * self.args.cutoff
        cv_voltage  = self.args.volts
        
        disp_hours = int(self.args.max_time)
        disp_minutes = int((self.args.max_time - disp_hours) * 60)
        print('Plan:')
        print(f'     CC: charge at {cc_current:.2f} A until {cv_voltage:.2f} V')
        print(f'     CV: continue until current below {eoc_current:.2f}')
        print(f'                        or {disp_hours}h{disp_minutes:02}m elapsed')
        if self.args.log:
            print(f'     Logging to {self.args.log}')
            self.ofh = open(self.args.log,'w',newline='',encoding='utf-8')
            self.csvw = csv.writer(self.ofh)

        print('Starting in 5s')
        time.sleep(5)

        print('Starting.')

        self.k.setVolts(cv_voltage)
        self.k.setCurr(cc_current)
        self.k.enable()

        finished = False
        now = time.time()
        end_time = now + self.args.max_time * 3600

        time.sleep(1)
        
        first_iter = True
        while not finished and now < end_time:
            s = self.k.status()
            time_iso = re.sub(r'\.\d+','',s['time']['iso'])
            print(f"    {time_iso} {s['status']['ch0_mode']} {s['output']['volts']:.3f} V, {s['output']['curr']:.3f} A")
            if self.csvw:
                if first_iter:
                    self.csvw.writerow(korad3005p.listify_dict(s,True))
                    first_iter = False
                self.csvw.writerow(korad3005p.listify_dict(s,False))

            if s['output']['curr'] <= eoc_current:
                finished = True
            else:
                time.sleep(self.args.check_interval)

        self.k.disable()
        if self.ofh:
            self.ofh.close()

        print('Charging complete.')

if __name__ == '__main__':
    charger = KoradLipoCharger()
    charger.charge()

