#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
BeautifyCredit
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
    pathinfo = ' * ' + meta['name'].replace(path, '').replace('\\', '') + '\n'
    scriptDoc = False

    while (len(lines) > 0):
        line = [lines.pop(0)]

        if re.search(r'\s*\/\*', line[0]):
            scriptDoc = True # 存在scriptDoc
            line.append(pathinfo)
        elif not scriptDoc and re.search(r'\s*[^\/\s]', line[0]):
            # 在ScriptDoc之前出现代码，停止逐行检查，在顶部插入新scriptDoc
            linecode.append('\n/**\n' + pathinfo + ' */\n')
            linecode += line
            break
        elif re.search(r'@(import|!)', line[0]):
            # 移除原子文件的@import，避免重复导入
            # 移除@!形式的标签
            continue
        # 删除SVN关键字的语法标记，保留内容
        if meta['order'] != meta['total']:
            line[0] = re.sub(r'\$\w+\:?(.*?)\$', r'\1', line[0])
        # SVN关键字只应该出现在顶部第一个scriptDoc里
        linecode += line
        if '*/' in line[0]:
            break

    # 最后一个文件是Input文件，原有scriptDoc移到顶部, 增加包文件名
    if meta['order'] == meta['total']: 
        meta['notes']['licence'] = ''.join(linecode[1:])
        linecode = ['\n/**\n', pathinfo, ' */\n']

    # 把修改过的内容跟剩余的内容重新拼接
    linecode += lines
    return linecode
