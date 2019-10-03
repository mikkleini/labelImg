#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import os
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs
from libs.constants import DEFAULT_ENCODING

TXT_EXT = '.txt'
ENCODE_METHOD = DEFAULT_ENCODING

class YOLOWriter:

    def __init__(self, foldername, filename, imgSize, databaseSrc='Unknown', localImgPath=None):
        self.foldername = foldername
        self.filename = filename
        self.databaseSrc = databaseSrc
        self.imgSize = imgSize
        self.boxlist = []
        self.localImgPath = localImgPath
        self.verified = False

    def addBndBox(self, xmin, ymin, xmax, ymax, name, difficult):
        bndbox = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
        bndbox['name'] = name
        bndbox['difficult'] = difficult
        self.boxlist.append(bndbox)

    def BndBox2YoloLine(self, box, classList=[]):
        w = self.imgSize[1]
        h = self.imgSize[0]

        # Make sure this class gets to class list
        if box['name'] not in classList:
            classList.append(box['name'])

        return box['name'], box['xmin'] / w, box['xmax'] / w, box['ymin'] / h, box['ymax'] /h

    def save(self, classList=[], targetFile=None):

        out_file = None #Update yolo .txt
        out_class_file = None   #Update class list .txt

        if targetFile is None:
            out_file = open(
            self.filename + TXT_EXT, 'w', encoding=ENCODE_METHOD)
            classesFile = os.path.join(os.path.dirname(os.path.abspath(self.filename)), "classes.txt")
            out_class_file = open(classesFile, 'w')

        else:
            out_file = codecs.open(targetFile, 'w', encoding=ENCODE_METHOD)
            classesFile = os.path.join(os.path.dirname(os.path.abspath(targetFile)), "classes.txt")
            out_class_file = open(classesFile, 'w')


        for box in self.boxlist:
            classname, xmin, xmax, ymin, ymax = self.BndBox2YoloLine(box, classList)
            # print (classIndex, xcen, ycen, w, h)
            out_file.write("%s %.6f %.6f %.6f %.6f\n" % (classname, xmin, xmax, ymin, ymax))

        # print (classList)
        # print (out_class_file)
        for c in classList:
            out_class_file.write(c+'\n')

        out_class_file.close()
        out_file.close()



class YoloReader:

    def __init__(self, filepath, image, classListPath=None):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self.shapes = []
        self.filepath = filepath

        if classListPath is None:
            dir_path = os.path.dirname(os.path.realpath(self.filepath))
            self.classListPath = os.path.join(dir_path, "classes.txt")
        else:
            self.classListPath = classListPath

        # print (filepath, self.classListPath)

        classesFile = open(self.classListPath, 'r')
        self.classes = classesFile.read().strip('\n').split('\n')

        # print (self.classes)

        imgSize = [image.height(), image.width(),
                      1 if image.isGrayscale() else 3]

        self.imgSize = imgSize

        self.verified = False
        # try:
        self.parseYoloFormat()
        # except:
            # pass

    def getShapes(self):
        return self.shapes

    def addShape(self, label, xmin, ymin, xmax, ymax, difficult):

        points = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        self.shapes.append((label, points, None, None, difficult))

    def yoloLine2Shape(self, line):        
        
        w = self.imgSize[1]
        h = self.imgSize[0]

        parts = line.split(' ')

        # Class name could contain multiple words
        classname = ' '.join(parts[0:len(parts) - 4])

        # Make sure this class gets to class list
        if classname not in self.classes:
            self.classes.append(classname)

        # Calculate absolute positions
        xmin = int(float(parts[len(parts) - 4]) * w)
        xmax = int(float(parts[len(parts) - 3]) * w)
        ymin = int(float(parts[len(parts) - 2]) * h)
        ymax = int(float(parts[len(parts) - 1]) * h)

        return classname, xmin, ymin, xmax, ymax

    def parseYoloFormat(self):
        bndBoxFile = open(self.filepath, 'r')
        for bndBox in bndBoxFile:
            
            label, xmin, ymin, xmax, ymax = self.yoloLine2Shape(bndBox)

            # Caveat: difficult flag is discarded when saved as yolo format.
            self.addShape(label, xmin, ymin, xmax, ymax, False)
