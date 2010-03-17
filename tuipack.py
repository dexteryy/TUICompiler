#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
tuipack.py

"""

import io, re, sys, os, pysvn, ConfigParser, chardet
from optparse import OptionParser


def parseJS(src, files=[]):
    '''递归解析文件，生成打包文件列表'''
    requires = getRequires(src)
    for r in requires:
        if not r in files:
            parseJS(r, files)
    files.append(src)
    return files


importRule = re.compile(r"@import\s+(\S+)")

def getRequires(file):
    '''获取依赖文件列表'''
    requires = []
    try:
        src = open(file)
        for line in src:
            result = re.search(importRule, line)
            if not result == None:
                result = result.group(1)
                if not root in result:
                    result = os.path.join(root, result)
                requires.append(result)
            else:
                #只在顶部第一个ScriptDoc里查找连续的@import标签
                if (len(requires) or '*/' in line):
                    break
    except:
        pass
    else:
        src.close()
    return requires


def writeFile(filelist):
    client = pysvn.Client()
    code = ''
    log('Build: ')

    if len(filelist) > 1:
        for f in filelist:
            log('    import ' + f)

            if problem_file:
                warn =  problem_file[f] if f in problem_file else ''
                if warn:
                    raise Exception('svn ' + warn + ':' + f)

            try:
                rev = str(client.info2(f)[0][1].rev.number)
            except:
                rev = ''
            code += '\n/* ' + f.replace(root, '').replace('\\', '') + ' ' + rev + ' */\n'

            try:
                file = open(f)
                src = file.read()
                char = chardet.detect(src)
                file_charset = char['encoding']
                print file_charset
                if "ISO" in file_charset:
                    log('    [WARN] %s will decode with gb18030' % file_charset)
                    file_charset = "gb18030"
                src = src.decode(file_charset)
                #encode = char['encoding'].lower()
                #if not (encode == charset if charset == 'utf-8' else 'gb' in encode):
                    #log('\n[warning] ' + encode + ' NOT equal with output '
                          #+ 'charset(' + charset + ')\n')
                code += src
            except:
                raise Exception('file not exist: ' + f)
            finally:
                file.close()
        log('    Import files: %d' % len(filelist))
    else:
        log('    Import files: 0')
        raise Exception(0) # 用0作为返回状态，与普通错误区别
    
    log('    charset: ' + charset)
    log('    packed file: ' + output)
    open(output, 'wb').write(code.encode(charset))
    log('    BUILD SUCCESS!')


def getOutputName(input):
    return re.sub(r'(.+?)(_src.*)?(\.\w+)$',
            lambda mo: mo.group(1)
                + ('_pack' if None == mo.group(2) else '_combo')
                + mo.group(3),
            input)


def getCharset(input):
    try:
        inputfile = open(input)
        src = inputfile.read()
        char = re.search(r'@charset\s+["\']?([\w-]+)', src)
        char = char and char.group(1) or chardet.detect(src)['encoding']
    except:
        raise Exception('input file can\'t open')
    else:
        inputfile.close()
    return char.lower()


def initConfig():
    global root
    cf = ConfigParser.ConfigParser()
    confpath = os.path.join(os.path.dirname(__file__), "config")
    cf.read(confpath)
    root = cf.get('tuipack','root')


def main(argv=None):
    if argv is None:
        argv = sys.argv

    global log, output, charset, problem_file 


    parser = OptionParser()
    parser.add_option("-o", "--output", 
                        dest="outputfilename",
                        help="write output to <file>", 
                        metavar="FILE")
    parser.add_option("-c", "--charset", 
                        dest="charset",
                        help="Convert the outfile to <charset>", 
                        type="string")
    #parser.add_option("-d", "--default", 
                        #dest="defaultoutput",
                        #help="use default setting", 
                        #action="store_false")
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
        raise Exception('input .js file')
    
    if os.path.splitext(input)[1] != '.js':
        raise Exception('only .js file excepted')

    if options.quiet:
        def log(m):pass
    else:
        def log(message): print(message)

    # 检查svn status
    if options.nocheck:
        problem_file = {}
    else:
        svn = pysvn.Client()
        svn.update(root)
        changes = svn.status(root)
        wc = pysvn.wc_status_kind
        problem = [wc.modified, wc.added, wc.conflicted, wc.deleted, wc.unversioned]
        problem_file = dict([(f.path, str(f.text_status)) for f in changes if f.text_status in problem])
    
    # 判断输出编码
    if options.charset:
        charset = options.charset.lower()
    else:
        charset = getCharset(input)
    
    # 打包后的文件名
    if options.outputfilename:
        output = options.outputfilename
    else:
        output = getOutputName(input)

    writeFile(parseJS(input))


initConfig()

if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        if str(e) == '0':
            sys.exit()
        else:
            print '\n[error] ' + str(e)
            sys.exit("1")

