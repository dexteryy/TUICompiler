#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
LogManager

Copyright (c) 2010 Dexter.Yy
Released under LGPL Licenses.
"""

class LogManager():
    """ 收集运行过程中的日志或提示信息
        可以通过修改rules，增加新的格式和输出方式
    """
    log_notes = []      # 日志记录（[ 文本，元数据 ]）

    style = {           # 各种类型输出信息的格式
        'task':     lambda msg, opt: 
                        "\n{msg}: ".format(msg=msg),
        'taskend':  lambda msg, opt:
                        "    {msg}!\n".format(msg=msg.upper()),
        'action':   lambda msg, opt:
                        "    [{act}]{dest}: {msg}".format(msg=msg, act=opt['act'], dest=opt['dest']),
        'command':  lambda msg, opt:
                        "    [CMD] {msg}".format(msg=msg),
        'stat':     lambda msg, opt:
                        "    {dest}: {msg}".format(msg=msg, dest=opt['dest']),
        'warn':     lambda msg, opt:
                        "    [WARN]{msg}".format(msg=msg),
        'error':    lambda msg, opt:
                        "[ERROR] {msg}!".format(msg=msg.upper())
    }


    def log(self, msg, **opt):
        """ 收集日志
        """
        self.log_notes.append([msg, opt]);


    def formatLog(self, msg, opt):
        """ 设定单行内容的格式
        """
        type = opt["type"]
        if self.style.has_key(type):
            return self.style[type](msg, opt)
        else:
            return msg


    def showLog(self):
        """ 输出日志
        """
        lines = [self.formatLog(item[0], item[1]) for item in self.log_notes]
        return "\n".join(lines)



def main(argv=None):
    if argv is None:
        argv = sys.argv

if __name__ == "__main__":
    main()
