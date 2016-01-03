#!/usr/bin/python
"""
Check if a file can be read by cclib and if all the required information is available.
"""

import theo_header, cclib_interface, input_options, error_handler
import sys

theo_header.print_header('Check cclib')

print("cc_check.py <logfile>")
print("Check if a logfile can be parsed with cclib")

try:
    logfile = sys.argv[1]
except IndexError:
    raise error_handler.MsgError("Please enter the name of the logfile!")

ioptions = input_options.dens_ana_options(ifile=None, check_init=False)
ioptions['rtype'] = 'cclib'
ioptions['rfile'] = logfile

ccparser = cclib_interface.file_parser_cclib(ioptions)
errcode = ccparser.check()

if errcode <= 1:
    print("\n %s can be parsed by using rtype='cclib' in dens_ana.in."%logfile)
    if errcode == 0:
        print(" Conversion to Molden format also possible")
    else:
        print(" But conversion to Molden format is not possible")
else:
    print("\n %s cannot be parsed by cclib (errcode=%i)!"%(logfile, errcode))