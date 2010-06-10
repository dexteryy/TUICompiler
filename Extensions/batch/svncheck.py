#!/usr/bin/python
# -*- encoding: utf-8 -*-
"""
svncheck
plugin for TUIPacker

Copyright (c) 2010 Dexter.Yy
Released under LGPL Licenses.
"""

import io, re, sys, os
import pysvn

print __file__

def checkSVN(self):
    """ 核对svn status
    """
    try:
        svn = pysvn.Client()
        svn.update(path['svn'])
        changes = svn.status(path['svn'])
        wc = pysvn.wc_status_kind
        problem = [wc.modified, wc.added, wc.conflicted, wc.deleted, wc.unversioned]
        problem_notes.update(dict([(f.path, str(f.text_status)) for f in changes if f.text_status in problem]))
    except:
        log("svn repo does not exit", type="warn")


#warn =  problem_notes[f] if f in problem_notes else ''
#if warn:
    #raise Exception('svn ' + warn + ':' + f)
