#!/usr/bin/env python3

import sys
import time
import matplotlib.pyplot as plt
import redpitaya_scpi as scpi

IP = 'rp-f0ad96.local'        # 'rp-f066c8.local'
rp_s = scpi.scpi(IP)

wave_form = 'sine'
freq = 200e3
ampl = 1

period = 1 # [s]
rp_s.tx_txt('DIG:PIN LED' + str(2) + ',' + str(0))
rp_s.tx_txt('DIG:PIN LED' + str(3) + ',' + str(0))

for i in range(10):
    time.sleep(period/10.0)
    rp_s.tx_txt('DIG:PIN LED' + str(0) + ',' + str(1))
    time.sleep(period/10.0)
    rp_s.tx_txt('DIG:PIN LED' + str(0) + ',' + str(0))


# Reset Generation and Acquisition
rp_s.tx_txt('GEN:RST')
rp_s.tx_txt('ACQ:RST')

##### Generation #####
rp_s.tx_txt('SOUR1:FUNC ' + str(wave_form).upper())
rp_s.tx_txt('SOUR1:FREQ:FIX ' + str(freq))
rp_s.tx_txt('SOUR1:VOLT ' + str(ampl))

rp_s.tx_txt('SOUR1:BURS:STAT BURST')        # Mode set to BURST
rp_s.tx_txt('SOUR1:BURS:NCYC 3')            # 3 periods in each burst

##### Acqusition #####
rp_s.tx_txt('ACQ:DEC 1')
rp_s.tx_txt('ACQ:TRIG:LEV 0')
rp_s.tx_txt('ACQ:TRIG:DLY 0')

rp_s.tx_txt('ACQ:START')
time.sleep(1)
rp_s.tx_txt('ACQ:TRIG AWG_PE')
rp_s.tx_txt('OUTPUT1:STATE ON')
time.sleep(1)

rp_s.tx_txt('SOUR1:TRIG:INT')

# Wait for trigger
while 1:
    rp_s.tx_txt('ACQ:TRIG:STAT?')           # Get Trigger Status
    if rp_s.rx_txt() == 'TD':               # Triggerd?
        rp_s.tx_txt('DIG:PIN LED' + str(2) + ',' + str(1))
        break

while 1:
    rp_s.tx_txt('ACQ:TRIG:FILL?')
    if rp_s.rx_txt() == '1':
        rp_s.tx_txt('DIG:PIN LED' + str(3) + ',' + str(1))
        break

# Read data and plot
rp_s.tx_txt('ACQ:SOUR1:DATA?')              # Read full buffer (source 1)
data_string = rp_s.rx_txt()                 # data into a string

# Remove brackets and empty spaces + string => float
data_string = data_string.strip('{}\n\r').replace("  ", "").split(',')
data = list(map(float, data_string))        # transform data into float

plt.plot(data)
plt.show()