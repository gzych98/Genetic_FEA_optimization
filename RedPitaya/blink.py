#!/usr/bin/env python3

import sys
import time
import redpitaya_scpi as scpi

IP = 'rp-f0ad96.local'
rp_s = scpi.scpi(IP)

if (len(sys.argv) > 2):
    print(sys.argv[2])
    led = int(sys.argv[2])
else: led = 0

print (f'Blinking LED [{str(led)}]')

period = 1 #seconds

while 1:
    time.sleep(period/10.0)
    rp_s.tx_txt('DIG:PIN LED' + str(led) + ',' + str(1))
    time.sleep(period/10.0)
    rp_s.tx_txt('DIG:PIN LED' + str(led) + ',' + str(0))

rp_s.close()