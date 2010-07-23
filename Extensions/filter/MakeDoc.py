#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
MakeDoc
filter for TUIPacker

Copyright (c) 2010 Dexter.Yy
Released under LGPL Licenses.
"""

import re
import chardet


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
    linecode = []
    scriptDoc = False

    src = ''.join(lines)
    char = chardet.detect(src)
    file_charset = char['encoding'].lower()

    blockTag = { "class": 1, "public": 1, "private": 1 }

    data = [] 

    while (len(lines) > 0):
        line = lines.pop(0).decode(file_charset)
        match = re.search(r'\*\s+@(\w+)\s+(.+)', line)
        if match:
            tag = match.group(1)
            v = match.group(2).encode('utf-8')
            #print tag, blockTag.has_key(tag)

            if blockTag.has_key(tag):
                info = re.search(r'(.+?)([\s\(]+)([^\)\s]*)', v)
                info = info.groups() if info else []
                block = {
                    'name': info[0],
                    'addition': info[2],
                    'type': tag == 'class' and "Class"
                                or not re.search(r'^\(', info[1] or '') == None and "Method"
                                or "Attribute"
                }
            else:
                block = data.pop()
                if not block.has_key(tag):
                    block[tag] = v
                else:
                    block[tag] += '\n' + v

            data.append(block)

        linecode.append(line.encode('utf-8'))

    #print data.pop(0)

    return linecode
