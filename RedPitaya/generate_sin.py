#!/usr/bin/env python3

import sys
import redpitaya_scpi as scpi

IP = "rp-f0ad96.local"
rp_s = scpi.scpi(IP)

wave_form = 'sine'
freq = 200000
ampl = 1

rp_s.tx_txt('GEN:RST')

rp_s.tx_txt('SOUR1:FUNC ' + str(wave_form).upper())
rp_s.tx_txt('SOUR1:FREQ:FIX ' + str(freq))
rp_s.tx_txt('SOUR1:VOLT ' + str(ampl))

# Enable output
rp_s.tx_txt('OUTPUT1:STATE ON')
rp_s.tx_txt('SOUR1:TRIG:INT')

rp_s.close()