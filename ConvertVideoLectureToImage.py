#-------------------------------------------------------------------------------
# Name:        convert video lecture to image
# Purpose:
#
# Author:      ppoo
#
# Created:     11/01/2014
# Licence:      MIT
#-------------------------------------------------------------------------------

import cv2
import cv2.cv as cv
import numpy
import math
from os import path
import os.path
import sys
import textwrap
import pysrt
import tarfile
import unicodedata
import shutil
from PIL import Image,ImageDraw,ImageFont
from multiprocessing import Process
from datetime import timedelta
import GetLink
class ConvertVideoLectureToImage:
    SUBTITLE_EXT = '.srt'
    SUB_MARGIN_LEFT_PERCENT  = 0.1
    SUB_MARGIN_RIGHT_PERCENT  = 0.1
    SUB_MARGIN_BOTTOM_PERCENT = 0.1
    SUB_LINE_MARGIN_BOTTOM = 0.1
    COLLISION_SHIFTING_MILISECONDS = 0
    TO_GRAYSCALE = False
    TEST_NUM_IMAGE = 0
    UNICODE = False
    #ascii mode
    FONT_FACE = "FONT_HERSHEY_SIMPLEX"
    TEXT_COLOR = [255,255,255] # (R, G, B)
    FONTSCALE = 0.7
    THICKNESS = 1
    #unicode mode
    FONT_PATH = ''
    FONT_SIZE = 25
    #general
    BORDER_SIZE = 1
    BORDER_COLOR = list()

    SHOW_MID = False
    SHOW_END = False
    SHOW_TIME = False

    COUNT_INCREMENT = 1

    TIME_MARGIN_RIGHT_PERCENT = 0.2
    TIME_MARGIN_TOP_PERCENT = 0.05

    IMAGE_OUTPUT_TYPE = 'jpg'

    VIDEO_EXTENSION = '.mp4'

    TO_TAR  = False
    TAR_PATH = ''

    SCENE_DETECTION = False
    SCENE_THREADHOLD = 10

    COOKIE_JSON_PATH = ''

    RESUME = False

    COMPRESS_LEVEL_JPG = 50
    COMPRESS_LEVEL_PNG = 100

    IMAGE_OUTPUT_WIDTH = 800
    IMAGE_OUTPUT_HEIGHT = 0
    IS_RESIZE = False

    REMOVE_OUTPUT_IMG = False

    def __init__(self,videoPath,subPath,outputPath=''):
        self.videoPath = videoPath
        self.subPath = subPath
        self.compressParams = []
        self.tarPath = None
        if outputPath == '':
            self.outputPath = subPath.split('.')[0]
        else:
            self.outputPath = self.outputPath + '/' + path.basename(self.subPath).split('.')[0]
        if not path.isdir(self.outputPath):
            try:
                os.mkdir(self.outputPath)
            except:
                os.mkdir(self.outputPath + '_')

        def getSubFileNameWithoutExt(subPath):
                return subPath.split('.')[0]

        if videoPath == '':
            subFilenameWithoutExt = getSubFileNameWithoutExt(subPath)
            self.videoPath = subFilenameWithoutExt + self.VIDEO_EXTENSION


        if not path.exists(self.subPath):
            raise Exception("Cannot find subtitle file name " + self.subPath)


    def readFrameAtMil(self,videoCapture,mil):
            while True:
                pos_frame = videoCapture.get(cv.CV_CAP_PROP_POS_FRAMES)
                flag,frame = videoCapture.read()
                if not flag:
                    videoCapture.set(cv2.CV_CAP_PROP_POS_MSEC,mil)
                    print "frame is not ready"
                    cv2.WaitKey(1000)
                else:
                    return self.preprocessFrame(frame)

    def writeFrameToImg(self,frame,filepath):
        if not cv2.imwrite(filepath,frame,self.compressParams):
            raise Exception("Cannot write to output")
        if self.TO_TAR==True:
            self.tarFile.add(filepath,arcname=path.basename(filepath))
        return True

    def outFilePath(self,filename):
        return self.outputPath + '/' +filename

    def imgPathGenerator(self,prefix='image'):
        count = 0
        while True:
            filename = '{0}-{1:05d}.{2}'.format(prefix,count,self.IMAGE_OUTPUT_TYPE)
            yield self.outFilePath(filename)
            count+=1

    def wrapTextUnicode(self,text):
        text_width,text_height = self.font.getsize(text)
        content_width = self.width*(1 - self.SUB_MARGIN_LEFT_PERCENT - self.SUB_MARGIN_RIGHT_PERCENT)
        if text_width > content_width:
            char_avg_width = int(float(text_width)/len(text))
            len_line_limit = int(float(content_width)/char_avg_width)
            line_list = textwrap.wrap(text,width=len_line_limit)
        else:
            line_list = [text]
        pos_x = int(self.SUB_MARGIN_LEFT_PERCENT*self.width)
        pos_y = int(self.height - \
                    text_height*(len(line_list)-1) - \
                    self.SUB_LINE_MARGIN_BOTTOM*text_height*(len(line_list)-1) - \
                    self.SUB_MARGIN_BOTTOM_PERCENT*self.height)
        return {'lineList':line_list,'x':pos_x,'y':pos_y,'lineHeight':text_height}

    def wrapTextAscii(self,text):
        text = text.encode("ascii","ignore")
        text_width,text_height = cv2.getTextSize(text,self.FONT_FACE,self.FONTSCALE,self.THICKNESS)[0] # width,height
        content_width = self.width*(1 - self.SUB_MARGIN_LEFT_PERCENT - self.SUB_MARGIN_RIGHT_PERCENT)
        if text_width > content_width:
            char_avg_width = int(float(text_width)/len(text))
            len_line_limit = int(float(content_width)/char_avg_width)
            line_list = textwrap.wrap(text,width=len_line_limit)
        else:
            line_list = [text]
        pos_x = int(self.SUB_MARGIN_LEFT_PERCENT*content_width)
        pos_y = int(self.height - \
                    text_height*(len(line_list)-1) - \
                    self.SUB_LINE_MARGIN_BOTTOM*text_height*(len(line_list)-1) - \
                    self.SUB_MARGIN_BOTTOM_PERCENT*self.height)
        return {'lineList':line_list,'x':pos_x,'y':pos_y,'lineHeight':text_height}

    def prepareVidAndSub(self):
        if self.SHOW_MID: self.COUNT_INCREMENT+=1

        if self.SHOW_END: self.COUNT_INCREMENT+=1

        if len(self.BORDER_COLOR)==0:
            self.BORDER_COLOR = map(lambda x: 255-x,self.TEXT_COLOR)

        if  self.IMAGE_OUTPUT_TYPE in ('jpg','jpeg'):
            self.compressParams = [cv2.cv.CV_IMWRITE_JPEG_QUALITY,self.COMPRESS_LEVEL_JPG,0]
        elif self.IMAGE_OUTPUT_TYPE == 'png':
            self.compressParams = [cv2.cv.CV_IMWRITE_PNG_COMPRESSION,self.COMPRESS_LEVEL_PNG,0]

        if self.videoPath.startswith('http'):
            self.videoPath = GetLink.GetLink(url=self.videoPath,cookiesJsonPath=self.COOKIE_JSON_PATH).get()
            self.videoPath = self.videoPath.replace('https','http')
            ##print self.videoPath

        if self.TO_TAR == True:
            if self.TAR_PATH=='':
                self.tarPath = self.outputPath + '.tar'
            else:
                self.tarPath = self.TAR_PATH + path.basename(self.subPath).split('.')[0] + '.tar'
            mode = 'w'
            #'a' if path.exists(self.tarPath) else
            self.tarFile = tarfile.open(self.tarPath,mode)

        self.sub = self.readSubtitle()
        #font prepare
        self.FONT_FACE = eval("cv2."+self.FONT_FACE)
        if self.UNICODE == True:
            if not self.FONT_PATH == '':
                self.font = ImageFont.truetype(self.FONT_PATH,self.FONT_SIZE)
            else:
                raise Exception("Need FONT_PATH argument for Unicode mode")
        self.videoCapture = cv2.VideoCapture()
        if not self.videoCapture.open(self.videoPath):
            raise Exception("Cannot open video file")
        self.width = int(self.videoCapture.get(cv.CV_CAP_PROP_FRAME_WIDTH))
        self.height = int(self.videoCapture.get(cv.CV_CAP_PROP_FRAME_HEIGHT))
        if self.IS_RESIZE:
            self.orginal_width = self.width
            self.orginal_height = self.height
            newHeightDependOnWidth = int(self.IMAGE_OUTPUT_WIDTH*self.orginal_height/float(self.orginal_width))
            if newHeightDependOnWidth < self.IMAGE_OUTPUT_HEIGHT:
                self.height = self.IMAGE_OUTPUT_HEIGHT
            else:
                self.height = newHeightDependOnWidth
            self.width = self.IMAGE_OUTPUT_WIDTH

    def toGrayscale(self,frame):
        new_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        return new_frame

    def genBorderPos(self,x,y):
        return [(x-i,y-j) for i in range(-self.BORDER_SIZE,self.BORDER_SIZE+1) for j in range(-self.BORDER_SIZE,self.BORDER_SIZE+1)]

    def preprocessFrame(self,frame):
        if self.IS_RESIZE:
            frame = cv2.resize(frame,(self.width,self.height))
        if self.TO_GRAYSCALE == True:
            frame = self.toGrayscale(frame)
        return frame

    def addTextUnicode(self,file_path,textProps,frame,miltime):
        image_file = Image.fromarray(frame) #open(file_path)
        img_draw = ImageDraw.Draw(image_file)
        for line_num,text in enumerate(textProps['lineList']):
            for x,y in self.genBorderPos(textProps['x'],textProps['y']):
                img_draw.text((x,
                            y + int(textProps["lineHeight"]*(0.4+1+self.SUB_LINE_MARGIN_BOTTOM))*line_num),
                            text,
                            self.rgb2hex(self.BORDER_COLOR[0],self.BORDER_COLOR[1],self.BORDER_COLOR[2]),
                            self.font)
            img_draw.text((textProps['x'],
                            textProps['y'] + int(textProps["lineHeight"]*(0.4+1+self.SUB_LINE_MARGIN_BOTTOM))*line_num),
                            text,
                            self.rgb2hex(self.TEXT_COLOR[0],self.TEXT_COLOR[1],self.TEXT_COLOR[2]),
                            self.font)
        if self.SHOW_TIME:
            timePos = self.getTimePos()
            time = self.milToHumanreadableStr(miltime)
            for x,y in self.genBorderPos(timePos[0],timePos[1]):
                img_draw.text(timePos,
                            time,
                            self.rgb2hex(self.BORDER_COLOR[0],self.BORDER_COLOR[1],self.BORDER_COLOR[2]),
                            self.font)
            img_draw.text(timePos,
                            time,
                            self.rgb2hex(self.TEXT_COLOR[0],self.TEXT_COLOR[1],self.TEXT_COLOR[2]),
                            self.font)
        # Convert RGB to BGR
        open_cv_image = numpy.array(image_file)
        #open_cv_image = open_cv_image[:, :, ::-1].copy()
        #image_file.save(file_path)
        self.writeFrameToImg(open_cv_image,file_path)

    def addTextAscii(self,file_path,textProps,frame,miltime):
        for line_num,line in enumerate(textProps['lineList']):
            for x,y in self.genBorderPos(textProps['x'],textProps['y']):
                cv2.putText(frame,\
                        line,\
                        (x,\
                        y + int(textProps["lineHeight"]*(0.4+1+self.SUB_LINE_MARGIN_BOTTOM))*line_num),\
                        self.FONT_FACE,\
                        self.FONTSCALE,\
                        [self.BORDER_COLOR[2],self.BORDER_COLOR[1],self.BORDER_COLOR[0]],\
                        self.THICKNESS,\
                        lineType=cv2.CV_AA)
            cv2.putText(frame,\
                        line,\
                        (textProps['x'],\
                        textProps['y'] + int(textProps["lineHeight"]*(0.4+1+self.SUB_LINE_MARGIN_BOTTOM))*line_num),\
                        self.FONT_FACE,\
                        self.FONTSCALE,\
                        [self.TEXT_COLOR[2],self.TEXT_COLOR[1],self.TEXT_COLOR[0]],\
                        self.THICKNESS,\
                        lineType=cv2.CV_AA)

        if self.SHOW_TIME:
            timePos = self.getTimePos()
            time = self.milToHumanreadableStr(miltime)
            for x,y in self.genBorderPos(timePos[0],timePos[1]):
                cv2.putText(frame,\
                        time,\
                        (x,y),
                        self.FONT_FACE,\
                        self.FONTSCALE,\
                        [self.BORDER_COLOR[2],self.BORDER_COLOR[1],self.BORDER_COLOR[0]],\
                        self.THICKNESS,\
                        lineType=cv2.CV_AA)
            cv2.putText(frame,\
                        time,\
                        timePos,
                        self.FONT_FACE,\
                        self.FONTSCALE,\
                        (self.TEXT_COLOR[2],self.TEXT_COLOR[1],self.TEXT_COLOR[0]),\
                        self.THICKNESS,\
                        lineType=cv2.CV_AA)
        self.writeFrameToImg(frame,file_path)

    def getTimePos(self):
        return tuple((int((1-self.TIME_MARGIN_RIGHT_PERCENT)*self.width),\
                        int(self.TIME_MARGIN_TOP_PERCENT*self.height)))

    def genImage(self):
        self.prepareVidAndSub()
        img_path_gen = self.imgPathGenerator()
        #test mode
        if self.TEST_NUM_IMAGE > 0:
            self.sub = self.sub[0:self.TEST_NUM_IMAGE]
        skip = 0

        total_subtitle_row = len(self.sub)

        progress_bar = self.progressBar(total_subtitle_row*self.COUNT_INCREMENT)

        addText = self.addTextUnicode if self.UNICODE else self.addTextAscii
        wrapText = self.wrapTextUnicode if self.UNICODE else self.wrapTextAscii


        for row_num,row in enumerate(self.sub):

            progress_bar((row_num+1)*self.COUNT_INCREMENT)

            from_time,to_time = row['from'],row['to']
            textProps = wrapText(row['text'])

            #get image at from_time
            img_file_out = img_path_gen.next()

            if self.RESUME == True:
                if path.isfile(img_file_out):
                    skip+=1
                    continue

            frame = self.readFrameAtMil(self.videoCapture,from_time)
            addText(img_file_out,textProps,frame,from_time)
            if self.SCENE_DETECTION == True:
                pass
            textProps['lineList'] = []
            #get image at mid_time
            if self.SHOW_MID == True:
                img_file_out = img_path_gen.next()
                if self.RESUME == True:
                    if path.isfile(img_file_out):
                        skip+=1
                        continue
                mid_time = (from_time+to_time)/2
                frame = self.readFrameAtMil(self.videoCapture,mid_time)
                addText(img_file_out,textProps,frame,mid_time)
                #self.writeFrameToImg(frame,img_file_out)

            #get image at to_time
            if self.SHOW_END == True:
                img_file_out = img_path_gen.next()
                if self.RESUME == True:
                    if path.isfile(img_file_out):
                        skip+=1
                        continue
                frame = self.readFrameAtMil(self.videoCapture,to_time)
                addText(img_file_out,textProps,frame,to_time)
                #self.writeFrameToImg(textProps,img_file_out)

        sys.stdout.write("\nSkip %d/%d image" % (skip,total_subtitle_row))
        self.videoCapture.release()

        if self.TO_TAR:
            self.tarFile.close()

        if self.REMOVE_OUTPUT_IMG:
            shutil.rmtree(self.outputPath)

        print '\nDone!'


    def readSubtitle(self):
        sub = {'from':0,'to':0,'text':''}
        sign = {'new':'\n','timeFromTo':'-->'}
        subList = []
        ###encoding ="utf-8" if self.UNICODE else "ascii"
        srt = pysrt.open(self.subPath,encoding="utf-8")
        subList = [{'from':self.toMilliseconds(line.start),
                    'to':self.toMilliseconds(line.end),
                    'text':u'' + line.text} for line in srt]
        if self.COLLISION_SHIFTING_MILISECONDS>0:
            def fixSubTextCollision(self,sub):
                for i in range(0,len(sub)):
                    if sub[i]['from']==sub[i-1]['to']:
                        sub[i]['from'] += self.COLLISION_SHIFTING_MILISECONDS
            self.fixSubTextCollision(subList)
        return subList

    @staticmethod
    def toMilliseconds(timeObj):
        return int(timeObj.milliseconds)+3600000*int(timeObj.hours)+60000*int(timeObj.minutes)+1000*int(timeObj.seconds)

    @staticmethod
    def milToHumanreadableStr(milliseconds):
        return str(timedelta(milliseconds=milliseconds))

    @staticmethod
    def progressBar(complete,bar_width=30):
        def run(count):
            count = float(count)
            percent = 100*count/complete
            sys.stdout.write('\r[{0}] - {1}% - {2}/{3} Total'.format('#'*int(math.ceil(bar_width*count/complete))\
                                                              , round(percent,2)
                                                              , int(count)\
                                                              , complete))

        return run

    @staticmethod
    def rgb2hex(r, g, b):
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)