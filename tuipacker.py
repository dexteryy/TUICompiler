#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
TUIPacker

Copyright (c) 2010 Dexter.Yy
Released under LGPL Licenses.
"""

import io, re, sys, os
import chardet
import ConfigParser
from optparse import OptionParser
from Lib.LogManager import LogManager
import Extensions


class TUIPacker(LogManager):
    filetype = ''                                   # 文件类型，自动影响构建行为
    charset = None                                  # 输出文件的编码
    inputfile = None                                # 构建对象，包含元信息的文件
    outputfile = None                               # 构建之后生成的文件名
    libpath = None                                  # 从这个路径下查找导入的文件
    logfile = None                                  # 日志的输出文件
    importRule = re.compile(r"@import\s+(\S+)")
    problem_files = {}                              # 不安全文件的清单（{ 文件名：版本状态 }）

    path = {                                        # 路径配置
        'work': '',
        'svn': None,
        'js': '',
        'css': ''
    }
    enableModules = {                               # 启用的扩展模块
        'filter': [],
        'batch': [],
        'ftplugin': [],
        'plugin': [],
    }


    def __init__(self, input, output=None, charset=None):

        self.inputfile = input
        self.outputfile = output or self.getOutputName(input)

        # 读取配置
        cf = ConfigParser.ConfigParser()
        confpath = os.path.join(os.path.dirname(__file__), "config")
        cf.read(confpath)

        # 检查已激活的扩展模块
        for n in self.enableModules:
            try:
                self.enableModules[n] = re.split(r',\s*', cf.get('extensions', n))
            except:
                self.enableModules[n] = None

        # 初始化代码库的路径配置
        for n in self.path:
            try:
                self.path[n] = cf.get('file', n)
            except:     
                # svn仓库路径不存在时，从工作目录获取文件，不支持版本检查
                self.path[n] = None

        # 根据输入文件名后缀判断类型
        self.filetype = os.path.splitext(input)[1][1:]
        if not self.path.has_key(self.filetype):
            raise Exception('unsupported filetype')

        # 判断输出编码
        self.charset = charset or self.getCharset(input)

        # 在不提供svn位置的情况下，默认使用工作目录
        self.libpath = (self.path['svn'] or self.path['work']) \
                     + (self.path[self.filetype] if self.filetype != ''
                        else self.path[os.path.splitext(input)[1]])


    def make(self):
        """ 执行构建
        """
        self.combine(self.crawler(self.inputfile))


    def crawler(self, src, files=[]):
        """ 递归读取文件中的标签，生成打包文件列表
        """
        requires = self.getRequires(src)
        for r in requires:
            if not r in files:
                self.crawler(r, files)
        files.append(src)
        return files


    def getRequires(self, src):
        """ 获取依赖文件列表
        """
        requires = []

        src = open(src)
        for line in src:
            result = re.search(self.importRule, line)
            if not result == None:
                result = result.group(1)
                if not self.libpath in result:
                    result = os.path.join(self.libpath, result)
                requires.append(result)
            else:
                #只在顶部第一个ScriptDoc里查找连续的@import标签
                if (len(requires) or '*/' in line):
                    break

        return requires


    def combine(self, filelist):
        """ 拼接文件
            文件内容在拼接之前会通过多层filter的解析和修改
        """
        self.log('build', type="task")

        file_count = len(filelist)
        if file_count <= 1:
            self.log('0', type="stat", dest="total files")
            raise Exception(0) # 用0作为返回状态，与普通错误区别

        self.log(len(filelist), type="stat", dest="total files")

        code = ""
        notes = {
            'licence': ''
        }
        input_charset = self.charset

        for order, f in enumerate(filelist):
            self.log(re.sub(self.libpath, '', f),
                     type="action", act="read", dest="import")

            filelines = self.filter(open(f).readlines(),
                name = f,
                order = order + 1,
                total = file_count,
                notes = notes
            )
            src = ''.join(filelines)

            char = chardet.detect(src) # 侦测编码必须针对文件整体
            file_charset = char['encoding'].lower()
            if 'utf-8' == file_charset or 'ascii' == file_charset:
                file_charset = "utf-8"
            else: # 中文可能被错误识别为latin编码
                file_charset = "gb18030"
            code += src.decode(file_charset)
            if order == file_count:
                input_charset = file_charset

        code = notes['licence'].decode(input_charset) + code

        self.log(self.charset, type="stat", dest="charset")
        self.log(self.outputfile, type="action", act="write", dest="packed file")

        open(self.outputfile, 'wb').write(code.encode(self.charset))

        self.log('build success', type="taskend")


    def filter(self, lines, **meta):
        """ 提供给插件/中间件的钩子
            通过编写这个方法的装饰器，可以实现更多代码生成功能
            meta参数：name, order, total
        """
        return lines


    def getOutputName(self, input):
        """ 打包文件命名方式:
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


    def getCharset(self, input):
        """ 分析输入文件，决定输出文件采用何种编码
        """
        f = open(input)
        src = f.read()
        char = re.search(r'@charset\s+["\']?([\w-]+)', src)
        char = char and char.group(1) or chardet.detect(src)['encoding']
        return char.lower()


def printLog(fn):
    """ log方法的装饰器，在每次记录日志的同时显示内容
    """
    def newfn(self, msg, **args):
        print self.formatLog(msg, args)
        return fn(self, msg, **args)
    newfn.__name__ = fn.__name__
    newfn.__doc__ = fn.__doc__
    newfn.__dict__.update(fn.__dict__) 
    return newfn



def main(argv=None):
    if argv is None:
        argv = sys.argv

    opt = OptionParser()
    opt.add_option("-o", "--output",
                   dest="outputfilename",
                   help="write output to <file>",
                   metavar="FILE")
    opt.add_option("-c", "--charset",
                   dest="charset",
                   help="convert the outfile to <charset>",
                   type="string")
    opt.add_option("-s", "--simple",
                   dest="simple",
                   help="simple mode",
                   action="store_false")
    opt.add_option("-q", "--quiet",
                   dest="quiet",
                   help="quiet mode, suppress all warning and messages",
                   action="store_true")
    (opt, args) = opt.parse_args()
    
    if args and args[0]:
        input = args[0]
    else:
        raise Exception('no input file')

    packer = TUIPacker(input,
        output = opt.outputfilename,
        charset = opt.charset and opt.charset.lower()
    )

    # 边执行边打印日志
    if not opt.quiet:
        TUIPacker.log = printLog(TUIPacker.log)
    
    modules = packer.enableModules

    # 装载过滤器插件
    if 'filter' in modules:
        originFilter = TUIPacker.filter
        hook = TUIPacker.filter
        for plugin in modules['filter']:
            filter = __import__('.'.join(['Extensions', 'filter', plugin]),
                                globals(), locals(), ['filter'], -1).filter
            hook = filter(hook)
            hook.__name__ = originFilter.__name__
            hook.__doc__ = originFilter.__doc__
            hook.__dict__.update(originFilter.__dict__) 
        TUIPacker.filter = hook 


    # 执行构建
    packer.make()
    


if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        if str(e) == '0':
            sys.exit()
        else:
            print '\n[error] ' + str(e)
            sys.exit("1")

