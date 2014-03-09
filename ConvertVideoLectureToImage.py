#-------------------------------------------------------------------------------
# Name:        convert video lecture to image
# Purpose:
#
# Author:      ppoo
#
# Created:     11/01/2014
# Licence:      MIT
#-------------------------------------------------------------------------------
from doctest import _OutputRedirectingPdb

import numpy
import math
from os import path
import os.path
import sys
import textwrap
import tarfile
import shutil
from PIL import Image, ImageDraw, ImageFont
from datetime import timedelta

import cv2
import cv2.cv as cv
import pysrt
from selenium.webdriver.support.expected_conditions import element_selection_state_to_be

import GetLink
import logging

class ConvertVideoLectureToImage:
    SUBTITLE_EXT = '.srt'
    SUB_MARGIN_LEFT_PERCENT = 0.1
    SUB_MARGIN_RIGHT_PERCENT = 0.1
    SUB_MARGIN_BOTTOM_PERCENT = 0.1
    SUB_LINE_MARGIN_BOTTOM = 0.5
    COLLISION_SHIFTING_MILISECONDS = 0
    TO_GRAYSCALE = False
    TEST_NUM_IMAGE = 0
    UNICODE = False
    #ascii mode
    FONT_FACE = "FONT_HERSHEY_SIMPLEX"
    TEXT_COLOR = [255, 255, 255] # (R, G, B)
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

    TIME_MARGIN_RIGHT_PERCENT = 0.9
    TIME_MARGIN_TOP_PERCENT = 0.05

    IMAGE_OUTPUT_TYPE = 'jpg'

    VIDEO_EXTENSION = '.mp4'

    TO_TAR = False
    TAR_PATH = ''


    COOKIE_JSON_PATH = ''

    RESUME = False

    COMPRESS_LEVEL_JPG = 50
    COMPRESS_LEVEL_PNG = 100

    IMAGE_OUTPUT_WIDTH = 800
    IMAGE_OUTPUT_HEIGHT = 0
    IS_RESIZE = False

    REMOVE_OUTPUT_IMG = False

    DIFF_THRESHOLD = 8000
    AVOID_DUPLICATE_MID_END_IMAGE = True

    MAX_RETRY_NUMBER = 2

    MASS_MODE = False
    def __init__(self, videoPath, subPath, outputPath=''):
        """

        @param videoPath: path to video file
        @param subPath: path to subtitle file
        @param outputPath: path to output folder
        @return: @raise Exception: Cannot find subtitle filename
        """
        self.videoPath = videoPath
        self.subPath = subPath
        self.orgSubPath = subPath
        self.compressParams = []
        self.tarPath = None
        self.outputPath = ''
        logging.basicConfig(filename='error.log',level=logging.ERROR,filemode='w')

    def read_frame_at_mil(self, videoCapture, mil):
        """

        @rtype : cv2 frame
        """
        retryCounter = 0
        while True:
            videoCapture.set(cv2.cv.CV_CAP_PROP_POS_MSEC, mil)
            flag, frame = videoCapture.read()
            if not flag:
                print "frame is not ready"
                retryCounter+=1
                cv2.waitKey(1000)
                if retryCounter > self.MAX_RETRY_NUMBER: exit("Exceed max retries, checking whether or not your video or subtitle have problem!!!")
            else:
                return self.preprocess_frame(frame)

    def write_frame_to_img(self, frame, filepath):
        """
        @param frame: opencv frame
        @param filepath: path to file
        @return: @raise Exception: Cannot write to file
        """
        if not cv2.imwrite(filepath, frame, self.compressParams):
            raise Exception("Cannot write to output")
        if self.TO_TAR == True:
            self.tarFile.add(filepath, arcname=path.basename(filepath))
        return True

    def out_file_path(self, filename):
        return self.outputPath + '/' + filename

    def img_path_generator(self, prefix='image',increaseBy=1):
        count = 0
        while True:
            filename = '{0}-{1:05d}.{2}'.format(prefix, count, self.IMAGE_OUTPUT_TYPE)
            nextFileName = '{0}-{1:05d}.{2}'.format(prefix, count+1, self.IMAGE_OUTPUT_TYPE)
            yield [filename,nextFileName]
            count += increaseBy

    def img_name_by_number(self,prefix,number):
        return '{0}-{1:05d}.{2}'.format(prefix, number, self.IMAGE_OUTPUT_TYPE)

    def wrap_text_unicode(self, text):
        """

        @param text: subtitle line
        @return:
        """
        text_width, text_height = self.font.getsize(text)
        content_width = self.width * (1 - self.SUB_MARGIN_LEFT_PERCENT - self.SUB_MARGIN_RIGHT_PERCENT)
        if text_width > content_width:
            char_avg_width = int(float(text_width) / len(text))
            len_line_limit = int(float(content_width) / char_avg_width)
            line_list = textwrap.wrap(text, width=len_line_limit)
        else:
            line_list = [text]
        pos_x = int(self.SUB_MARGIN_LEFT_PERCENT * self.width)
        pos_y = int(self.height - \
                    text_height * (len(line_list)) - \
                    self.SUB_LINE_MARGIN_BOTTOM * text_height * (len(line_list) - 1) - \
                    self.SUB_MARGIN_BOTTOM_PERCENT * self.height)
        return {'lineList': line_list, 'x': pos_x, 'y': pos_y, 'lineHeight': text_height}

    def wrap_text_ascii(self, text):
        """

        @param text: subtitle line
        @return:
        """
        text = text.encode("ascii", "ignore")
        text_width, text_height = cv2.getTextSize(text, self.FONT_FACE, self.FONTSCALE, self.THICKNESS)[
            0] # width,height
        content_width = self.width * (1 - self.SUB_MARGIN_LEFT_PERCENT - self.SUB_MARGIN_RIGHT_PERCENT)
        if text_width > content_width:
            char_avg_width = int(float(text_width) / len(text))
            len_line_limit = int(float(content_width) / char_avg_width)
            line_list = textwrap.wrap(text, width=len_line_limit)
        else:
            line_list = [text]
        pos_x = int(self.SUB_MARGIN_LEFT_PERCENT * content_width)
        pos_y = int(self.height - \
                    text_height * (len(line_list)) - \
                    self.SUB_LINE_MARGIN_BOTTOM * text_height * (len(line_list) - 1) - \
                    self.SUB_MARGIN_BOTTOM_PERCENT * self.height)
        return {'lineList': line_list, 'x': pos_x, 'y': pos_y, 'lineHeight': text_height}

    def prepare_vid_and_sub(self):
        if self.outputPath == '':
            self.outputPath = self.subPath.split('.')[0]
        elif not self.MASS_MODE:
            self.outputPath = self.outputPath + '/' + path.basename(self.subPath).split('.')[0]
        if not path.isdir(self.outputPath):
            try:
                os.mkdir(self.outputPath)
            except:
                os.mkdir(self.outputPath + '_')

        if self.SHOW_MID: self.COUNT_INCREMENT += 1

        if self.SHOW_END: self.COUNT_INCREMENT += 1

        if len(self.BORDER_COLOR) == 0:
            self.BORDER_COLOR = map(lambda x: 255 - x, self.TEXT_COLOR)

        if self.IMAGE_OUTPUT_TYPE in ('jpg', 'jpeg'):
            self.compressParams = [cv2.cv.CV_IMWRITE_JPEG_QUALITY, self.COMPRESS_LEVEL_JPG, 0]
        elif self.IMAGE_OUTPUT_TYPE == 'png':
            self.compressParams = [cv2.cv.CV_IMWRITE_PNG_COMPRESSION, self.COMPRESS_LEVEL_PNG, 0]

        if self.videoPath.startswith('http'):
            cookiesJsonContent='' if self.COOKIE_JSON_PATH=='' else open(self.COOKIE_JSON_PATH,'r').read()
            self.videoPath = GetLink.GetLink(url=self.videoPath, cookiesJsonContent=cookiesJsonContent).get()
            self.videoPath = self.videoPath.replace('https', 'http')
            ##print self.videoPath

        if self.TO_TAR == True:
            if self.TAR_PATH == '':
                self.tarPath = self.outputPath + '.tar'
            else:
                self.tarPath = self.TAR_PATH + path.basename(self.subPath).split('.')[0] + '.tar'
            mode = 'w|bz2'
            #'a' if path.exists(self.tarPath) else
            self.tarFile = tarfile.open(self.tarPath, mode)

        def getSubFileNameWithoutExt(subPath):
            return '.'.join(subPath.split('.')[0:-1])

        if self.videoPath == '':
            subFilenameWithoutExt = getSubFileNameWithoutExt(self.subPath)
            self.videoPath = subFilenameWithoutExt + self.VIDEO_EXTENSION

        if not path.exists(self.subPath):
            raise Exception("Cannot find subtitle file name " + self.subPath)

        self.sub = self.read_subtitle()
        #font prepare
        self.FONT_FACE = eval("cv2." + self.FONT_FACE)
        if self.UNICODE == True:
            if not self.FONT_PATH == '':
                self.font = ImageFont.truetype(self.FONT_PATH, self.FONT_SIZE)
            else:
                raise Exception("Need FONT_PATH argument for Unicode mode")
        self.video_capture = cv2.VideoCapture()
        if not self.video_capture.open(self.videoPath):
            logging.error("Cannot open video file: %s",self.videoPath)
            raise Exception("Cannot open video file: %s" % self.videoPath)
        self.width = int(self.video_capture.get(cv.CV_CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video_capture.get(cv.CV_CAP_PROP_FRAME_HEIGHT))
        if self.IS_RESIZE:
            self.orginal_width = self.width
            self.orginal_height = self.height
            newHeightDependOnWidth = int(self.IMAGE_OUTPUT_WIDTH * self.orginal_height / float(self.orginal_width))
            if newHeightDependOnWidth <= self.IMAGE_OUTPUT_HEIGHT:
                self.height = self.IMAGE_OUTPUT_HEIGHT
            else:
                self.height = newHeightDependOnWidth
            self.width = self.IMAGE_OUTPUT_WIDTH

    @staticmethod
    def to_grayscale(frame):
        """

        @param frame: opencv frame
        @return:
        """
        new_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return new_frame

    def gen_border_pos(self, x, y):
        """
            Generate border positions for text
        @param x: x-axis position of text which will put on image
        @param y: y-axis
        @return: position for drawing border
        """
        return [(x - i, y - j) for i in range(-self.BORDER_SIZE, self.BORDER_SIZE + 1) for j in
                range(-self.BORDER_SIZE, self.BORDER_SIZE + 1)]

    def preprocess_frame(self, frame):
        """
            Preprocess frame
        @param frame:
        @return: processed frame
        """
        if self.IS_RESIZE:
            frame = cv2.resize(frame, (self.width, self.height))
        if self.TO_GRAYSCALE == True:
            frame = self.to_grayscale(frame)
        return frame

    def add_text_unicode(self, file_path, textProps, frame, miltime):
        image_file = Image.fromarray(frame) #open(file_path)
        img_draw = ImageDraw.Draw(image_file)
        border_color = self.rgb2hex(self.BORDER_COLOR[0], self.BORDER_COLOR[1], self.BORDER_COLOR[2])
        text_color = self.rgb2hex(self.TEXT_COLOR[0], self.TEXT_COLOR[1], self.TEXT_COLOR[2])
        for line_num, text in enumerate(textProps['lineList']):
            for x, y in self.gen_border_pos(textProps['x'], textProps['y']):
                img_draw.text((x,
                               y + int(textProps["lineHeight"] * (1 + self.SUB_LINE_MARGIN_BOTTOM)) * line_num),
                              text,
                              border_color,
                              self.font)
            img_draw.text((textProps['x'],
                           textProps['y'] + int(
                               textProps["lineHeight"] * (1 + self.SUB_LINE_MARGIN_BOTTOM)) * line_num),
                          text,
                          text_color,
                          self.font)
        if self.SHOW_TIME:
            #text_width, text_height = self.font.getsize(text)
            timePos = self.get_time_pos()
            time = self.mil_to_humanreadable_str(miltime)
            for x, y in self.gen_border_pos(timePos[0], timePos[1]):
                img_draw.text((x,y),
                              time,
                              border_color,
                              self.font)
            img_draw.text(timePos,
                          time,
                          text_color,
                          self.font)
            # Convert RGB to BGR
        open_cv_image = numpy.array(image_file)
        #open_cv_image = open_cv_image[:, :, ::-1].copy()
        #image_file.save(file_path)
        self.write_frame_to_img(open_cv_image, file_path)

    def add_text_ascii(self, file_path, textProps, frame, miltime):
        for line_num, line in enumerate(textProps['lineList']):
            for x, y in self.gen_border_pos(textProps['x'], textProps['y']):
                cv2.putText(frame,
                            line,
                            (x,
                             y + int(textProps["lineHeight"] * (1 + self.SUB_LINE_MARGIN_BOTTOM)) * line_num),
                            #y + int(textProps["lineHeight"] * (self.SUB_LINE_MARGIN_BOTTOM)) * line_num),
                            self.FONT_FACE,
                            self.FONTSCALE,
                            [self.BORDER_COLOR[2], self.BORDER_COLOR[1], self.BORDER_COLOR[0]],
                            self.THICKNESS,
                            lineType=cv2.CV_AA)
            cv2.putText(frame,
                        line,
                        (textProps['x'],
                         textProps['y'] + int(
                         textProps["lineHeight"] * (1 + self.SUB_LINE_MARGIN_BOTTOM)) * line_num),
                        #textProps["lineHeight"] * (self.SUB_LINE_MARGIN_BOTTOM)) * line_num),
                        self.FONT_FACE,
                        self.FONTSCALE,
                        [self.TEXT_COLOR[2], self.TEXT_COLOR[1], self.TEXT_COLOR[0]],
                        self.THICKNESS,
                        lineType=cv2.CV_AA)

        if self.SHOW_TIME:
            timePos = self.get_time_pos()
            time = self.mil_to_humanreadable_str(miltime)
            for x, y in self.gen_border_pos(timePos[0], timePos[1]):
                cv2.putText(frame,
                            time,
                            (x, y),
                            self.FONT_FACE,
                            self.FONTSCALE,
                            [self.BORDER_COLOR[2], self.BORDER_COLOR[1], self.BORDER_COLOR[0]],
                            self.THICKNESS,
                            lineType=cv2.CV_AA)
            cv2.putText(frame,
                        time,
                        timePos,
                        self.FONT_FACE,
                        self.FONTSCALE,
                        [self.TEXT_COLOR[2], self.TEXT_COLOR[1], self.TEXT_COLOR[0]],
                        self.THICKNESS,
                        lineType=cv2.CV_AA)
        self.write_frame_to_img(frame, file_path)

    def get_time_pos(self):
        return tuple((int((1 - self.TIME_MARGIN_RIGHT_PERCENT) * self.width), \
                      int(self.TIME_MARGIN_TOP_PERCENT * self.height)))

    def gen_image(self):
        self.prepare_vid_and_sub()
        img_path_gen = self.img_path_generator()
        #test mode
        if self.TEST_NUM_IMAGE > 0:
            self.sub = self.sub[0:self.TEST_NUM_IMAGE]
        skip = 0

        total_subtitle_row = len(self.sub)
        estimated_row = total_subtitle_row * self.COUNT_INCREMENT

        add_text = self.add_text_unicode if self.UNICODE else self.add_text_ascii
        wrap_text = self.wrap_text_unicode if self.UNICODE else self.wrap_text_ascii

        count = 0
        print('{0}'.format(path.basename(self.outputPath)))
        for row_num, row in enumerate(self.sub):
            from_time, to_time = row['from'], row['to']
            text_props = wrap_text(row['text'])

            #get image at from_time
            img_file_out = map(self.out_file_path,img_path_gen.next())
            #start image with subtitle
            if True == self.RESUME and path.isfile(img_file_out[0]):
                skip += 1
                continue
            else:
                frame = self.read_frame_at_mil(self.video_capture, from_time)
                count+=1

            org_frame = numpy.empty_like(frame)
            if self.SHOW_MID or self.SHOW_END:
                numpy.copyto(org_frame,frame)
            add_text(img_file_out[0], text_props, frame, from_time)
            text_props['lineList'] = []
            #get image at mid_time
            mid_frame = None
            if self.SHOW_MID:
                if self.RESUME and path.isfile(img_file_out[1]):
                    skip += 1
                else:
                    mid_time = (from_time + to_time) / 2
                    mid_frame = self.read_frame_at_mil(self.video_capture, mid_time)
                    if self.AVOID_DUPLICATE_MID_END_IMAGE and self.is_difference(org_frame,mid_frame):
                        count+=1
                        ##print "Diff {0}".format(cv2.norm(org_frame,mid_frame))
                        img_file_out = map(self.out_file_path,img_path_gen.next())
                        add_text(img_file_out[0], text_props, mid_frame, mid_time)
                    else:
                        estimated_row -= 1
                #self.writeFrameToImg(frame,img_file_out)

            #get image at to_time
            if self.SHOW_END:
                if self.RESUME and path.isfile(img_file_out[1]):
                    skip += 1
                else:
                    end_frame = self.read_frame_at_mil(self.video_capture, to_time)
                    if (mid_frame is not None and self.is_difference(mid_frame,end_frame)) or \
                            (mid_frame is None and self.is_difference(org_frame,end_frame)):
                        count += 1
                        img_file_out = map(self.out_file_path,img_path_gen.next())
                        add_text(img_file_out[0], text_props, end_frame, to_time)
                    else:
                        estimated_row -= 1
                    #self.writeFrameToImg(text_props,img_file_out)
            self.progress_bar(estimated_row)(count)
        if not self.RESUME:
            print("\nSkip %d/%d subtitle row" % (skip, estimated_row))
        else:
            print("\nSkip %d subtitle row" % (skip))
        self.video_capture.release()

        if self.TO_TAR:
            self.tarFile.close()

        if self.REMOVE_OUTPUT_IMG:
            shutil.rmtree(self.outputPath)

        print 'Done!\n'


    def read_subtitle(self):
        sub = {'from': 0, 'to': 0, 'text': ''}
        sign = {'new': '\n', 'timeFromTo': '-->'}
        subList = []
        ###encoding ="utf-8" if self.UNICODE else "ascii"
        srt = pysrt.open(self.subPath, encoding="utf-8")
        subList = [{'from': self.to_milliseconds(line.start),
                    'to': self.to_milliseconds(line.end),
                    'text': u'' + line.text} for line in srt]
        if self.COLLISION_SHIFTING_MILISECONDS > 0:
            def fixSubTextCollision(self, sub):
                for i in range(0, len(sub)):
                    if sub[i]['from'] == sub[i - 1]['to']:
                        sub[i]['from'] += self.COLLISION_SHIFTING_MILISECONDS
            self.fixSubTextCollision(subList)
        return subList

    @staticmethod
    def to_milliseconds(timeObj):
        return int(timeObj.milliseconds) + 3600000 * int(timeObj.hours) + 60000 * int(timeObj.minutes) + 1000 * int(
            timeObj.seconds)

    @staticmethod
    def mil_to_humanreadable_str(milliseconds):
        return str(timedelta(milliseconds=milliseconds))

    @staticmethod
    def progress_bar(complete, bar_width=30):
        def run(count):
            count = float(count)
            percent = 100 * count / complete
            sys.stdout.write("\r[{0}] - {1}% - {2}/{3} Total".format('#' * int(math.ceil(bar_width * count / complete))
                ,round(percent, 2)
                , int(count)
                , complete))
        return run

    @staticmethod
    def rgb2hex(r, g, b):
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)

    def is_difference(self,frame1,frame2):
        return True if cv2.norm(frame1,frame2)>=self.DIFF_THRESHOLD else False
