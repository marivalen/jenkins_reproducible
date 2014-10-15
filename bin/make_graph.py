#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Holger Levsen (holger@layer-acht.org)
#
# based on similar code taken from piuparts-reports.py written by me

import os
import sys
import string
from rpy2 import robjects
from rpy2.robjects.packages import importr

def main():
    if len(sys.argv) != 6:
        print "we need exactly five params: csvfilein, pngoutfile, color, mainlabel, ylabl"
        return
    filein = sys.argv[1]
    fileout = sys.argv[2]
    colors = sys.argv[3]
    columns = str(int(colors)+1)
    mainlabel = sys.argv[4]
    ylabel = sys.argv[5]
    countsfile = os.path.join(filein)
    pngfile = os.path.join(fileout)
    grdevices = importr('grDevices')
    grdevices.png(file=pngfile, width=1600, height=800, pointsize=10, res=100, antialias="none")
    r = robjects.r
    r('t <- (read.table("'+countsfile+'",sep=",",header=1,row.names=1))')
    r('cname <- c("date",rep(colnames(t)))')
    # thanks to http://tango.freedesktop.org/Generic_Icon_Theme_Guidelines for those nice colors
    r('palette(c("#4e9a06", "#f57900", "#cc0000", "#2e3436", "#888a85"))')
    r('v <- t[0:nrow(t),0:'+colors+']')
    # make graph since day 1
    r('barplot(t(v),col = 1:'+columns+', main="'+mainlabel+'", xlab="", ylab="'+ylabel+'", space=0, border=NA)')
    r('legend(x="bottom",legend=colnames(t), ncol=2,fill=1:'+columns+',xjust=0.5,yjust=0,bty="n")')
    grdevices.dev_off()

if __name__ == "__main__":
    main()

# vi:set et ts=4 sw=4 :