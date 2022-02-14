#!/usr/bin/env python3

import argparse
import csv
import datetime
import json
import re
import signal
import sys
import time

import korad3005p

# A simple logging-to-csv program for Korad PSUs
#
# Author  : Dave Jacobowitz
# Version : 0 (Feb 2022)
#
# Free to use by any and all, with attribution.

class KoradCsvApp(object):
    def __init__(self):
        self.args = self.getArgs()
        self.k = korad3005p.Korad3005p(self.args.port, self.args.speed, self.args.timeout)
        signal.signal(signal.SIGINT, self.graceful_exit)

    def graceful_exit(self, signum, frame):
        print('Caught SIGINT. Exiting')
        try:
            self.ofh.close()
        except Exception as e:
            pass

        sys.exit(1)

    def getArgs(self):
        parser = argparse.ArgumentParser(description='Korad PSU Data Logger')
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

        ts = re.sub(r'[:\-]','',
            re.sub(r'\.\d+','',
                datetime.datetime.now().isoformat()
            )
        )

        parser.add_argument(
            '--output','-o',
            type=str,
            default=f'korad_data_{ts}.csv',
            help='name of file to write',
        )

        parser.add_argument(
            '--rate','-r',
            type=float,
            default=1,
            help='sample rate in Hz',
        )

        parser.add_argument(
            '--duration','-d',
            type=float,
            default=300,
            help='how long to run in seconds',
        )

        return parser.parse_args()
       
    def writeLine(self, data, first=False):
        if first:
            self.csvw.writerow(korad3005p.listify_dict(data, labels_only=True))
        self.csvw.writerow(korad3005p.listify_dict(data, labels_only=False))

    def go(self):

        with open(self.args.output, 'w', newline='', encoding='utf-8') as self.ofh:
            print(f'Opened file: {self.args.output}')
            print(f'Sampling at {self.args.rate:.2f} Hz for {self.args.duration} seconds')

            self.csvw = csv.writer(self.ofh)

            now      = time.time()
            end      = now + self.args.duration
            period   = 1.0 / self.args.rate
            deadline = now + period

            first = True
            while now < end:
                now = time.time()
                self.writeLine(self.k.status(), first)
                first = False
                sleep_time = deadline - now
                deadline += period
                if sleep_time > 0:
                    time.sleep(sleep_time)

            print('Done')



if __name__ == '__main__':

    a = KoradCsvApp()
    a.go()
