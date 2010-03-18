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
                file = open(f)
                linecode = ''
                line = '\n'
                pathinfo = ' * ' + f.replace(root, '').replace('\\', '') + '\n'
                scriptDoc = False
                while line:
                    if re.search(r'\s*\/\*', line):
                        scriptDoc = True # 存在scriptDoc
                        line += pathinfo
                    elif not scriptDoc and re.search(r'\s*[^\/\s]', line):
                        # 在ScriptDoc之前出现代码，停止逐行检查，在顶部插入新scriptDoc
                        linecode = '/**\n' + pathinfo + ' */\n' + line
                        break
                    # 删除SVN关键字的语法标记，保留内容
                    line = re.sub(r'\$\w+\:?(.*?)\$', r'\1', line)
                    linecode += line
                    # SVN关键字只应该出现在顶部第一个scriptDoc里，@import之上
                    if '@import' in line or '*/' in line:
                        break
                    line = file.readline()

                # 读取剩余的内容，与之前逐行取到的内容合并
                try:
                    src = file.read()
                    if not src:
                        raise Exception()
                except:
                    src = linecode
                else:
                    src = linecode + src

                char = chardet.detect(src) # 侦测编码必须针对文件整体
                file_charset = char['encoding']
                if "ISO" in file_charset:
                    # 中文可能被错误识别为latin编码
                    log('    [WARN] %s will decode with gb18030' % file_charset)
                    file_charset = "gb18030"
                code += src.decode(file_charset)
            except Exception, e:
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
    """打包文件命名方式:
        _g_src.js
        _g_combo.js

        jquery.js
        jquery_pack.js

        _yy_src.pack.js
        _yy_combo.js

        _yy_bak.pack.js
        _yy_bak.pack_pack.js
    """
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

