#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
tuicompiler.py

Copyright (c) 2010 Dexter.Yy
Released under LGPL Licenses.
"""

import io, re, sys, os
import ConfigParser
import subprocess as sub
from optparse import OptionParser
from tuipacker import TUIPacker, printLog, initOptions


def main(argv=None):
    if argv is None:
        argv = sys.argv

    # 从配置里获取可执行命令
    cf = ConfigParser.ConfigParser()
    confpath = os.path.join(os.path.dirname(__file__), "config")
    cf.read(confpath)
    jscompressor = cf.get('tools','jscompressor')
    csscompressor = cf.get('tools', 'csscompressor')
    dos2unix = cf.get('tools', 'dos2unix')

    opt = OptionParser()
    initOptions(opt)
    (opt, args) = opt.parse_args()
    
    if args and args[0]:
        input = args[0]
    else:
        raise Exception('need input file')

    filetype = os.path.splitext(input)[1][1:]

    packer = TUIPacker(input)

    # 边执行边打印日志
    if not opt.quiet:
        TUIPacker.log = printLog(TUIPacker.log)

    # 压缩时使用的编码
    if opt.charset:
        charset = opt.charset.lower()
    else:
        charset = packer.getCharset(input)

    # 没有导入代码的时候，不需要生成中间文件，高级/编译模式下总是生成文件
    if not opt.advanced and len(packer.getRequires(input)) <= 0:
        output = input
    elif opt.outputfilename:
        output = opt.outputfilename
    else:
        output = packer.getOutputName(input)
    
    #output_2 = re.sub(r'([^\.]+?)([_\.][^_]*\.)(\w+)$', 
                 #lambda mo: mo.group(1) 
                            #+ ('' if mo.group(2) else '_min') 
                            #+ '.' + mo.group(3), 
                 #output)

    """压缩文件命名方式:
        _g_src.js
        _g.js

        _g_combo.js
        _g.js

        jquery_pack.js
        jquery_pack_min.js

        _yy_src.pack.js
        _yy.js

        _yy_bak.pack_pack.js
        _yy_bak.pack_pack_min.js
    """
    output_2 = re.sub(r'(.+?)(_src.*|_combo.*)?(\.\w+)$', 
                 lambda mo: mo.group(1)
                    + ('_min' if None == mo.group(2) else '')
                    + mo.group(3), 
                 output)

    dos2unix += ' -q' if opt.quiet else ''


    cmd = []

    if filetype == "js":
        cmd.append(['python',
                    os.path.join(os.path.dirname(__file__), "tuipacker.py")]
                    + argv[1:])

        cmd.append(dos2unix.split(" ") + [output])

        cmd.append(jscompressor.split(" ")
                   + ['--charset', charset, output, '-o', output_2])

    elif filetype == "css":
        cmd.append([dos2unix, input])

        cmd.append(csscompressor.split(" ")
                   + ['--charset', charset, input, '-o', output_2])
    else:
        raise Exception('file type not supported')

    for e in cmd:
        if re.search(r'compressor', " ".join(e)):
            packer.log('Compress', type="task")
            packer.log(output_2, type="action", act="write", dest="compressed file")
        packer.log(" ".join(e), type="command")
        sub.check_call(e)

    packer.log('compress success', type="taskend")



if __name__ == "__main__":
    #try:
        main()
    #except Exception, e:
        #print '\n[error] ' + str(e)
        #sys.exit(1)

