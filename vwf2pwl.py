#!/usr/bin/env python3

# Dan White <dan@whiteaudio.com>

import fileinput
import os
import re
import sys

from decimal import Decimal

try:
    import psyco
    psyco.full()
except ImportError:
    pass


def info(s):
    print('INFO:', s, file=sys.stderr)

def error(s):
    print('ERROR:', s, file=sys.stderr)
    sys.exit(1)

def warn(s):
    print('WARNING:', s, file=sys.stderr)


def usage():
    error('''
Usage: vwf2pwl.py digitalinputs.vwf

vwf file format:
    [one name=value parameter per line]
    [space-separated column labels for voltage source names AND node names]
    [one line per bit interval of 0 or 1 for each column, no spaces between]

Example .vwf contents for testing an adder:
    clockdelay=500p
    clockrisefall = 100p
    risefall=200p
    bittime=1n
    bitlow=0
    bithigh=5
    a3 a2 a1 a0 b3 b2 b1 b0
    00000000
    00010001
    00010010
    11111111
    01011010
    01011011

Include the generated file, which also includes the Voltage-source definitons
for the input nodes as:
    .include "foo.pwl"

The "clockdelay=" parameter, if present, also generates a voltage source for a
clock as "Vclock clock 0 PWL ..." with a rising edge at every bittime with an
offset of clockdelay.  Hence, set "clockdelay=" to the maximum setup time of
your registers and the data on each line will be clocked in at the right time.
Parameter "clockrisefall=" is optional to separately specify the clock rise/
fall time if it is different from the data lines rise/fall.
''')




def mkpwl(d, bitlow, bithigh, risefall, bittime, outfile):
    t = Decimal('0.0')

    #first bit interval starts at t=0, start from this value
    lastbit = d[0]
    bitv = Decimal(lastbit) * (bithigh - bitlow) + bitlow
    s = '+ 0 %s' % str(bitv)
    outfile.write(s + '\n')

    trf = risefall
    tb = bittime - risefall
    t += trf + tb
    for bit in d[1:]:
        # only output a point when there is a change
        if bit != lastbit:
            ti = t + trf
            tf = ti + tb
            lastbitv = Decimal(lastbit) * (bithigh - bitlow) + bitlow
            bitv = Decimal(bit) * (bithigh - bitlow) + bitlow
            outfile.write('+ %s %s' % (str(t), str(lastbitv)) + '\n')
            outfile.write('+ %s %s' % (str(ti), str(bitv)) + '\n')
            #outfile.write('+ %s %s' % (str(tf), str(bitv)) + '\n')

        t += trf + tb
        lastbit = bit


RE_UNIT = re.compile(r'^([0-9e\+\-\.]+)(t|g|meg|x|k|mil|m|u|n|p|f)?')
def unit(s):
    """Takes a string and returns the equivalent float.
    '3.0u' -> 3.0e-6"""
    mult = {'t'  :Decimal('1.0e12'),
            'g'  :Decimal('1.0e9'),
            'meg':Decimal('1.0e6'),
            'x'  :Decimal('1.0e6'),
            'k'  :Decimal('1.0e3'),
            'mil':Decimal('25.4e-6'),
            'm'  :Decimal('1.0e-3'),
            'u'  :Decimal('1.0e-6'),
            'n'  :Decimal('1.0e-9'),
            'p'  :Decimal('1.0e-12'),
            'f'  :Decimal('1.0e-15')}

    m = RE_UNIT.search(s.lower())
    try:
        if m.group(2):
            return Decimal(Decimal(m.group(1)))*mult[m.group(2)]
        else:
            return Decimal(m.group(1))
    except:
        error("Bad unit: %s" % s)


def read_line(f):
    """Returns a line from a file, stripped of comments.  Will return the next
    non-comment line."""
    line = f.readline()
    line = line.strip()
    while line.startswith('#'):
        line = f.readline()
        line = line.strip()
    line = line.split('#')[0]
    line = line.strip()
    return line


def read_params(fvwf):
    """Returns (params, line) where line is the first non-(parameter, blank, or
    comment) line."""
    requiredParams = ('risefall', 'bittime', 'bitlow', 'bithigh')
    params = {'clockdelay':None, 'clockrisefall':None}

    line = read_line(fvwf)
    while '=' in line or line == '':
        name, value = line.split('=')
        name = name.strip()
        value = value.strip()
        params[name] = value

        line = read_line(fvwf)

    # validate
    for p in requiredParams:
        if p not in params:
            raise SyntaxError(f'Required parameter missing: {p}')

    info('Parameters:')
    for p,v in params.items():
        info('  %s = %s' % (p, v))

    if params['clockdelay']:
        info("Adding a clock at 'clock' node.")

    return (params, line)


def read_vector(line, nbits):
    """Return an iterable with bits in the vector.
    Strip comments starting with #."""
    idx = line.find('#')
    if idx >= 0:
        line = line[:idx]
    bits = line.strip()
    if len(bits) != nbits:
        raise SyntaxError(f'Wrong number of bits: {line} -> {bits}')
    return line.strip()


def vwf2pwl(vwf, pwl=None):
    if not vwf.endswith('.vwf'):
        raise SyntaxError(f'Input filename must end with .vwf: {vwf}')

    if pwl is None:
        pwl = vwf.replace('.vwf', '.pwl')

    with fileinput.input(files=(vwf,)) as fvwf, open(pwl, 'w') as fpwl:
        #read in the vwf definition file
        (params, line) = read_params(fvwf)

        #get column labels
        inputs = [c.strip() for c in line.strip().split()]
        ninputs = len(inputs)
        info("Columns: %s" % inputs)

        #read in data
        data = {}
        for i in inputs:
            data[i] = []

        for line in fvwf:
            vector = read_vector(line, nbits=ninputs)

            if len(vector) != len(inputs):
                error(f'{fvwf.lineno()}: Must have same # characters as column labels: {line}')

            for i, bit in enumerate(vector):
                data[inputs[i]].append(bit)

        #get the numbers from parameters
        risefall = unit(params['risefall'])
        bittime = unit(params['bittime'])
        bitlow = unit(params['bitlow'])
        bithigh = unit(params['bithigh'])

        #generate clock definition if specified
        if params['clockdelay']:
            #calculate clock high time
            if params['clockrisefall']:
                clockrisefall = unit(params['clockrisefall'])
            else:
                clockrisefall = risefall

            clockhigh = Decimal('0.5') * (bittime - clockrisefall)
            clockperiod = bittime

            params['clockrisefall'] = str(clockrisefall)
            params['clockhigh'] = str(clockhigh)
            params['clockperiod'] = str(clockperiod)

            clk = 'Vclock clock 0 pulse(%(bitlow)s %(bithigh)s %(clockdelay)s %(clockrisefall)s %(clockrisefall)s %(clockhigh)s %(clockperiod)s)' % params
            fpwl.write(clk + '\n\n')

        for name in inputs:
            d = data[name]
            s = f'V{name} {name} 0 PWL'
            fpwl.write(s + '\n')

            mkpwl(d, bitlow, bithigh, risefall, bittime, fpwl)
            fpwl.write('\n')
    return pwl


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    vwf2pwl(sys.argv[1])

