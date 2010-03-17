#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
tuicompiler.py

"""

import io, re, sys, os, ConfigParser
from optparse import OptionParser
import tuipack


def main(argv=None):
    if argv is None:
        argv = sys.argv

    global log

    cf = ConfigParser.ConfigParser()
    confpath = os.path.join(os.path.dirname(__file__), "config")
    cf.read(confpath)
    jscompressor = cf.get('tools','jscompressor')
    csscompressor = cf.get('tools', 'csscompressor')
    jspack = cf.get('tools', 'jspack')
    dos2unix = cf.get('tools', 'dos2unix')

    parser = OptionParser()
    parser.add_option("-o", "--output", 
                        dest="outputfilename",
                        help="write output to <file>", 
                        metavar="FILE")
    parser.add_option("-c", "--charset", 
                        dest="charset",
                        help="Convert the outfile to <charset>", 
                        type="string")
    parser.add_option("-n", "--nocheck", 
                        dest="nocheck",
                        help="NOT check svn status", 
                        action="store_true")
    parser.add_option("-q", "--quiet", 
                        dest="quiet",
                        help="Quiet mode. Suppress all warning and messages", 
                        action="store_true")
    (options, args) = parser.parse_args()
    
    if args and args[0]:
        input = args[0]
    else:
        raise Exception('need input file')

    filetype = os.path.splitext(input)[1]

    if options.quiet:
        def log(m):pass
    else:
        def log(message): print(message)
    
    if options.charset:
        charset = options.charset.lower()
    else:
        charset = tuipack.getCharset(input)

    if len(tuipack.getRequires(input)) <= 0:
        output = input
    elif options.outputfilename:
        output = options.outputfilename
    else:
        output = tuipack.getOutputName(input)
    
    #output_2 = re.sub(r'([^\.]+?)([_\.][^_]*\.)(\w+)$', 
                 #lambda mo: mo.group(1) 
                            #+ ('' if mo.group(2) else '_min') 
                            #+ '.' + mo.group(3), 
                 #output)
    output_2 = re.sub(r'(.+?)(_src.*|_combo.*)?(\.\w+)$', 
                 lambda mo: mo.group(1)
                    + ('_min' if None == mo.group(2) else '')
                    + mo.group(3), 
                 output)

    dos2unix += ' -q' if options.quiet else ''

    if filetype == ".js":
        cmd = '{0} {1}{7}{8}; {2} {5}; {3} --charset {4} {5} -o {6}'.format(
            jspack, input, dos2unix, jscompressor, charset, output, output_2,
            options.nocheck and ' -n' or '',
            options.quiet and ' -q' or '')
    elif filetype == ".css":
        cmd = '{3} {1}; {0} {1} -o {2}'.format(
            jscompressor, input, output_2, dos2unix)
    else:
        raise Exception('file type not supported')

    result = 0
    for e in cmd.split(';'):
        if result == 0:
            log('[CMD] ' + e + '')
            result = os.system(e)
    if result == 0:
        log('    compressed file: ' + output_2)
        log('    COMPRESS SUCCESS!')


if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        print '\n[error] ' + str(e)
        sys.exit(1)

