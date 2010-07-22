#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
MakeDoc
filter for TUIPacker

Copyright (c) 2010 Dexter.Yy
Released under LGPL Licenses.
"""

import re


def filter(inner):
    """ 扩展接口
        TUIPacker.filter方法的装饰器，参数和返回值必须保持一致
    """
    def wrapper(self, lines, **meta):
        rootpath = self.path['svn'] or self.path['work']
        lines = _parseDocs(lines, rootpath, meta)
        return inner(self, lines, **meta)
    return wrapper


def _parseDocs(lines, path, meta):
    """ 解析JS文件顶部的ScriptDoc/doc comments
    """
    linecode = ['\n']
    scriptDoc = False

    while (len(lines) > 0):
        line = [lines.pop(0)]
        if re.search(r'/*\s+@\w+\s+', line[0]):
            print line

        linecode += lines

    return linecode
