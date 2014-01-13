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
class ConvertVideoLectureToImage:
    SUBTITLE_EXT = '.srt'
    SUB_MARGIN_LEFT_PERCENT  = 0.1
    SUB_MARGIN_RIGHT_PERCENT  = 0.1
    SUB_MARGIN_BOTTOM_PERCENT = 0.1
    SUB_LINE_MARGIN_BOTTOM = 0.1
    FONT_FACE = "FONT_HERSHEY_DUPLEX"
    TEXT_COLOR = (255,255,255) # (B,G,R)
    FONTSCALE = 1.5
    THICKNESS = 1
    COLLISION_SHIFTING_MILISECONDS = 2
    TO_GRAYSCALE = False
    TEST = False
    TEST_NUM_IMAGE = 0
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
            self.subPath = self.getSubPathFromVideoPath(videoPath)
            if not path.exists(self.subPath):
                raise Exception("Cannot find subtitle file name " + self.subPath)
        else:
            self.subPath = subPath
    @classmethod
    def getSubPathFromVideoPath(cls,videoPath):
        return videoPath.split('.')[0] + cls.SUBTITLE_EXT
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

    def wrapText(self,text,fontFace,fontScale,thickness):
        text_width,text_height = cv2.getTextSize(text,fontFace,fontScale,thickness)[0] # width,height
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
        return {'lineList':line_list,'x':pos_x,'y':pos_y,'fontFace':fontFace\
                ,'fontScale':fontScale,'thickness':thickness,'lineHeight':text_height}

    def prepareVidAndSub(self):
        self.sub = self.readSubtitle()
        self.videoCapture = cv2.VideoCapture()
        #self.videoCapture.set(CV_CAP_PROP_FOURCC,CV_FOURCC('D','I','V','4'))
        if not self.videoCapture.open(self.videoPath):
            raise Exception("Cannot open video file")

    def toGrayscale(self,frame):
        new_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        return new_frame
    def genImage(self):
        self.prepareVidAndSub()
        self.width = int(self.videoCapture.get(cv.CV_CAP_PROP_FRAME_WIDTH))
        self.height = int(self.videoCapture.get(cv.CV_CAP_PROP_FRAME_HEIGHT))
        name_gen = self.name_generator()
        #test mode
        if self.TEST_NUM_IMAGE > 0:
            self.sub = self.sub[0:self.TEST_NUM_IMAGE+1]

        total_subtitle_row = len(self.sub)
        progress_bar = self.progressBar(total_subtitle_row)
        for row_num,row in enumerate(self.sub):
            #get image at from_time
            img_file_out = name_gen.next()
            #if path.exists(self.outFilePath(img_file_out)):
            #    continue

            from_time = row['from']
            to_time = row['to']
            textProps = self.wrapText(row['text'],\
                                fontFace=eval("cv2."+self.FONT_FACE),\
                                fontScale=self.FONTSCALE,\
                                thickness=self.THICKNESS
                                )

            frame = self.readFrameAtMil(self.videoCapture,from_time)
            text_color = self.TEXT_COLOR # (B,G,R)
            for line_num,line in enumerate(textProps['lineList']):
                cv2.putText(frame,\
                            line,\
                            (textProps['x'],\
                            textProps['y'] + int(textProps["lineHeight"]*(0.4+1+self.SUB_LINE_MARGIN_BOTTOM))*line_num),\
                            textProps['fontFace'],\
                            textProps['fontScale'],\
                            text_color,\
                            textProps['thickness'],\
                            lineType=cv2.CV_AA)
            #cv2.imshow("img",frame)
            self.writeFrameToImg(frame,img_file_out)

            #get image at to_time
            img_file_out = name_gen.next()
            #if path.exists(self.outFilePath(img_file_out)):
            #    continue
            frame = self.readFrameAtMil(self.videoCapture,to_time)
            self.writeFrameToImg(frame,img_file_out)

            progress_bar(row_num+1)
        self.videoCapture.release()
        print '\nDone!'

    def fixSubTextCollision(self,sub):
        for i in range(1,len(sub)):
            if sub[i]['from']==sub[i-1]['to']:
                sub[i]['from'] += self.COLLISION_SHIFTING_MILISECONDS

    def readSubtitle(self,fix=True):
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
        if fix:
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
                                                              , round(percent,3)
                                                              , int(count)\
                                                              , complete))

        return run