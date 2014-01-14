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
from PIL import Image,ImageDraw,ImageFont
from multiprocessing import Process
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
    FONT_FACE = "FONT_HERSHEY_DUPLEX"
    TEXT_COLOR = (255,255,255) # (B,G,R)
    FONTSCALE = 1.5
    THICKNESS = 1
    #unicode mode
    FONT_PATH = 'C:/arial.ttf'
    FONT_SIZE = 25
    #general
    BORDER_SIZE = 1
    BORDER_COLOR = ()

    def __init__(self,videoPath,subPath='',outputPath=''):
        self.videoPath = videoPath
        if outputPath == '':
            self.outputPath = videoPath.split('.')[0] + '/'
            if not path.isdir(self.outputPath):
                try:
                    os.mkdir(self.outputPath)
                except:
                    os.mkdir(self.outputPath + '_')
        else:
            self.outputPath = outputPath
        if subPath == '':
            def getSubPathFromVideoPath(videoPath):
                return videoPath.split('.')[0] + self.SUBTITLE_EXT
            self.subPath = getSubPathFromVideoPath(videoPath)
            if not path.exists(self.subPath):
                raise Exception("Cannot find subtitle file name " + self.subPath)
        else:
            self.subPath = subPath
        if not self.BORDER_COLOR:
            self.BORDER_COLOR = map(lambda x: 255-x,self.TEXT_COLOR)

    @staticmethod
    def readFrameAtMil(videoCapture,mil):
            while True:
                pos_frame = videoCapture.get(cv.CV_CAP_PROP_POS_FRAMES)
                flag,frame = videoCapture.read()
                if not flag:
                    videoCapture.set(cv2.CV_CAP_PROP_POS_MSEC,mil)
                    print "frame is not ready"
                    cv2.WaitKey(1000)
                else:
                    return frame

    def writeFrameToImg(self,frame,filename):
        if self.TO_GRAYSCALE == True:
            frame = self.toGrayscale(frame)
        if not cv2.imwrite(self.outFilePath(filename),frame):
            raise Exception("Cannot write to output")
        return True

    def outFilePath(self,filename):
        return self.outputPath + '/' +filename

    @staticmethod
    def name_generator(prefix='image'):
        count = 0
        while True:
            yield '{0}-{1:05d}.jpg'.format(prefix,count)
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

    def toGrayscale(self,frame):
        new_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        return new_frame

    def genBorderPos(self,x,y):
        return [(x-i,y-j) for i in range(-self.BORDER_SIZE,self.BORDER_SIZE+1) for j in range(-self.BORDER_SIZE,self.BORDER_SIZE+1)]

    def addTextUnicode(self,filename,textProps,frame):
        self.writeFrameToImg(frame,filename)
        file_path = self.outFilePath(filename)
        image_file = Image.open(file_path)
        img_draw = ImageDraw.Draw(image_file)
        for line_num,text in enumerate(textProps['lineList']):
            for x,y in self.genBorderPos(textProps['x'],textProps['y']):
                img_draw.text((x,
                            y + int(textProps["lineHeight"]*(0.4+1+self.SUB_LINE_MARGIN_BOTTOM))*line_num),
                            text.decode("utf-8"),
                            self.rgb2hex(self.BORDER_COLOR[0],self.BORDER_COLOR[1],self.BORDER_COLOR[2]),
                            self.font)
            img_draw.text((textProps['x'],
                            textProps['y'] + int(textProps["lineHeight"]*(0.4+1+self.SUB_LINE_MARGIN_BOTTOM))*line_num),
                            text.decode("utf-8"),
                            self.rgb2hex(self.TEXT_COLOR[0],self.TEXT_COLOR[1],self.TEXT_COLOR[2]),
                            self.font)
            image_file.save(file_path)

    def addTextAscii(self,filename,textProps,frame):
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
                        (self.TEXT_COLOR[2],self.TEXT_COLOR[1],self.TEXT_COLOR[0]),\
                        self.THICKNESS,\
                        lineType=cv2.CV_AA)
            self.writeFrameToImg(frame,filename)

    def genImage(self):
        self.prepareVidAndSub()
        name_gen = self.name_generator()
        #test mode
        if self.TEST_NUM_IMAGE > 0:
            self.sub = self.sub[0:self.TEST_NUM_IMAGE+1]

        total_subtitle_row = len(self.sub)
        progress_bar = self.progressBar(total_subtitle_row)

        addText = self.addTextUnicode if self.UNICODE else self.addTextAscii
        wrapText = self.wrapTextUnicode if self.UNICODE else self.wrapTextAscii

        for row_num,row in enumerate(self.sub):
            from_time,to_time = row['from'],row['to']
            textProps = wrapText(row['text'])

            #get image at from_time
            img_file_out = name_gen.next()
            frame = self.readFrameAtMil(self.videoCapture,from_time)
            addText(img_file_out,textProps,frame)

            #get image at to_time
            img_file_out = name_gen.next()
            frame = self.readFrameAtMil(self.videoCapture,to_time)
            self.writeFrameToImg(frame,img_file_out)

            progress_bar(row_num+1)

        self.videoCapture.release()
        print '\nDone!'


    def readSubtitle(self):
        sub = {'from':0,'to':0,'text':''}
        sign = {'new':'\n','timeFromTo':'-->'}
        subList = []
        with open(self.subPath,'r') as f:
            f.readline() #skip first empty line
            f.readline()
            while True:
                line = f.readline()
                if not line: break
                if line == sign['new']:
                    f.readline()
                    sub['text'] = sub['text'].replace('\n','')
                    subList.append(sub)
                    sub = {'from':0,'to':0,'text':''}
                    continue
                if line.find(sign['timeFromTo']) != -1:
                    sub['from'],sub['to']= map(ConvertVideoLectureToImage.toMilliseconds, line.replace(' ','').replace('\n','').split(sign['timeFromTo']))
                    continue
                sub['text'] += ' '+line
        if self.COLLISION_SHIFTING_MILISECONDS>0:
            def fixSubTextCollision(self,sub):
                for i in range(1,len(sub)):
                    if sub[i]['from']==sub[i-1]['to']:
                        sub[i]['from'] += self.COLLISION_SHIFTING_MILISECONDS
            self.fixSubTextCollision(subList)
        return subList

    @staticmethod
    def toMilliseconds(timeString):
        hours,minutes,seconds = timeString.split(':')
        seconds,miliseconds = seconds.split(',')
        return int(miliseconds)+3600000*int(hours)+60000*int(minutes)+1000*int(seconds)

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