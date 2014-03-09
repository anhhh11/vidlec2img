#-------------------------------------------------------------------------------
# Name:        main program
# Purpose:
#
# Author:      ppoo
#
# Created:     11/01/2014
# Licence:      MIT
#Reference:
#create menu:
#http://docs.python.org/3/library/argparse.html#dest
#make sure that frame ready to process:
#http://stackoverflow.com/questions/18954889/how-to-process-images-of-a-video-frame-by-frame-in-video-streaming-using-opencv
#save image
#http://stackoverflow.com/questions/18228258/saving-opencv-images
#seek rewind
#http://stackoverflow.com/questions/2974625/opencv-seek-function-rewind
#run on window
#http://stackoverflow.com/questions/11699298/opencv-2-4-videocapture-not-working-on-windows/11703998#11703998
#convert lplimage to numpy array
#http://stackoverflow.com/questions/13104161/fast-conversion-of-iplimage-to-numpy-array
#convert image to grayscale
#http://stackoverflow.com/questions/1807528/python-opencv-converting-images-taken-from-capture
#http://extr3metech.wordpress.com/2012/09/23/convert-photo-to-grayscale-with-python-opencv/
#text progress
#http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
#draw unicode text
#http://stackoverflow.com/questions/7698231/python-pil-draw-multiline-text-on-image
#text show and border
#http://stackoverflow.com/questions/18974194/text-shadow-with-python
#show time idea
#http://www.frisnit.com/2011/07/07/iplayer-for-kindle/
#http://stackoverflow.com/questions/2186525/use-a-glob-to-find-files-recursively-in-python
from _testcapi import raise_exception
from ConvertVideoLectureToImage import *
import argparse
import time
import datetime
import glob
import re
import json
import tempfile
import fnmatch
import multiprocessing
from GetLink import GetLink
def menu():
    parser = argparse.ArgumentParser(description='Convert video lecture to image')
    #mass converter mode
    mass_convert = parser.add_argument_group('Mass mode converter'.upper())
    mass_convert.add_argument('-MM','--mass-mode',help="Enable mass mode",default=False,action="store_true")
    mass_convert.add_argument('-fsp','--folder-subs-path',help="Convert all subtitle in folder. REQUIRE -MM flag",default='',type=str)
    mass_convert.add_argument('-rfp','--recursive-folder-path',help="Convert all subtitle in folder recursively. REQUIRE -MM flag",default='',type=str)
    mass_convert.add_argument('-ve','--video-extensions',help="Video file extension {0}".format(ConvertVideoLectureToImage.VIDEO_EXTENSION),\
                                default=ConvertVideoLectureToImage.VIDEO_EXTENSION,type=str)
    mass_convert.add_argument('-lvjp','--list-video-json-path',help="""List to video json file with structure"
                                                                    [ [<subtitle_link_1>,<video_link_1>,<folder_name_1>],
                                                                     [<subtitle_link_2>,<video_link_2>,<folder_name_2>],
                                                                      ... and so on
                                                                    ]""",type=str)
    mass_convert.add_argument('-nt',"--number-of-thread",help="""Support process multiple links or video files at once. Default: {0}
                                                              """.format(2),default=2,type=int)

    #general
    general = parser.add_argument_group('Input/Output'.upper())
    general.add_argument('-vp','--video-file-path',help="Path to video file",default='')
    general.add_argument('-sp','--sub-file-path',help="Path to subtitle file",default='')
    general.add_argument('-sc',"--subtitle-color",help="Subtitle color R G B, value=0..255\n Default: %s" % str(ConvertVideoLectureToImage.TEXT_COLOR)\
                        ,type=int,nargs=3,required=False,metavar=('R','G','B'),default=ConvertVideoLectureToImage.TEXT_COLOR)

    general.add_argument('-mrn',"--max-retry-number",\
                        help="Max retry number. Default: {0}".format(ConvertVideoLectureToImage.MAX_RETRY_NUMBER),\
                        default=ConvertVideoLectureToImage.MAX_RETRY_NUMBER,type=int)

    general.add_argument("-G","--to-grayscale",\
                        help="Font scale\n Default: {0}".format(ConvertVideoLectureToImage.TO_GRAYSCALE),\
                        default=ConvertVideoLectureToImage.TO_GRAYSCALE,
                        action="store_true")
    general.add_argument("-iot","--image-output-type",\
                        help="Image output type\n Default: {0}".format(ConvertVideoLectureToImage.IMAGE_OUTPUT_TYPE),\
                        default=ConvertVideoLectureToImage.IMAGE_OUTPUT_TYPE,
                        type=str,
                        metavar="[PNG|JPG|BMP]")
    general.add_argument('-o',"--output-path",\
                        help="Output images path. Default: <video_file_name_folder>",\
                        default='')
    general.add_argument('-RSZ',"--enable-resize-output-image",\
                        help="Output images. Default: {0}".format(ConvertVideoLectureToImage.IS_RESIZE),\
                        default=ConvertVideoLectureToImage.IS_RESIZE,
                        action="store_true")
    general.add_argument('-iow',"--image-output-width",\
                        help="Output width of images. Default: {0}".format(ConvertVideoLectureToImage.IMAGE_OUTPUT_WIDTH),\
                        default=ConvertVideoLectureToImage.IMAGE_OUTPUT_WIDTH,type=int)
    general.add_argument('-ioh',"--image-output-height",\
                        help="Output height of images. If set to 0 mean height scaled based on width. Default: {0}".format(ConvertVideoLectureToImage.IMAGE_OUTPUT_HEIGHT),\
                        default=ConvertVideoLectureToImage.IMAGE_OUTPUT_HEIGHT,type=int)
    general.add_argument("-T","--to-tar",\
                        help="Store images to tar file\n Default: {0}".format(ConvertVideoLectureToImage.TO_TAR),\
                        default=ConvertVideoLectureToImage.TO_TAR,
                        action="store_true")
    general.add_argument("-RM","--remove-output-images",\
                        help="Remove output images. Usually used combine with tar -T flag\n Default: {0}".format(ConvertVideoLectureToImage.REMOVE_OUTPUT_IMG),\
                        default=ConvertVideoLectureToImage.REMOVE_OUTPUT_IMG,
                        action="store_true")
    general.add_argument("-tfp","--tar-file-path",\
                        help="Path to tar file\n Default: {0}".format(ConvertVideoLectureToImage.TAR_PATH),\
                        default=ConvertVideoLectureToImage.TAR_PATH)
    general.add_argument("-cjp","--cookie-json-path",\
                        help="Path to cookie's file which exported from Edit This Cookie extension of Google Chrome\n Default: {0}"
                                            .format(ConvertVideoLectureToImage.COOKIE_JSON_PATH),
                                                    default=ConvertVideoLectureToImage.COOKIE_JSON_PATH)
    #unicode mode
    unicode_mode = parser.add_argument_group('Unicode mode'.upper())
    unicode_mode.add_argument('-U',"--unicode-mode",\
                        help="Active unicode mode to support unicode subtitle\n Default: {0}".format(ConvertVideoLectureToImage.UNICODE),\
                        default=ConvertVideoLectureToImage.UNICODE,\
                        action="store_true")
    unicode_mode.add_argument('-fp',"--font-path",\
                        help="Font path (required in Unicode mode only) ( require TrueFont type)\n Default: {0}"\
                                        .format(ConvertVideoLectureToImage.FONT_PATH),\
                        default=ConvertVideoLectureToImage.FONT_PATH,
                        metavar=("FONT PATH"))
    unicode_mode.add_argument('-fsz',"--font-size",\
                        help="Font size (in Unicode mode only)\n Default: {0}".format(ConvertVideoLectureToImage.FONT_SIZE),\
                        default=ConvertVideoLectureToImage.FONT_SIZE,\
                        metavar=("FONT SIZE"),
                        type=int)
    #display settings
    display_settings = parser.add_argument_group('Display setting'.upper())
    display_settings.add_argument("-M","--get-middle-image",\
                        help="Get image at (start+end)/2 time in subtitle line\n Default: {0}".format(ConvertVideoLectureToImage.SHOW_MID),\
                        default=ConvertVideoLectureToImage.SHOW_MID,
                        action="store_true")
    display_settings.add_argument("-E","--get-end-image",\
                        help="Get image at end time in subtitle line\n Default: {0}".format(ConvertVideoLectureToImage.SHOW_END),\
                        default=ConvertVideoLectureToImage.SHOW_END,
                        action="store_true")
    display_settings.add_argument("-ST","--show-time",\
                        help="Show time at top-left corner\n Default: {0}".format(ConvertVideoLectureToImage.SHOW_TIME),\
                        default=ConvertVideoLectureToImage.SHOW_TIME,
                        action="store_true")
    #appearance
    appearance = parser.add_argument_group('Appearance'.upper())
    appearance.add_argument('-sm',"--subtitle-margin-percent",\
                help="""Subtitle margin: left right bottom
                        Default: left:{0} right:{1} bottom:{2}
                """.format(ConvertVideoLectureToImage.SUB_MARGIN_LEFT_PERCENT,\
                            ConvertVideoLectureToImage.SUB_MARGIN_RIGHT_PERCENT,\
                            ConvertVideoLectureToImage.SUB_MARGIN_BOTTOM_PERCENT,\
                            ),type=float,nargs=3,metavar=('LEFT','RIGHT','BOTTOM')\
                                ,default=(ConvertVideoLectureToImage.SUB_MARGIN_LEFT_PERCENT,\
                                        ConvertVideoLectureToImage.SUB_MARGIN_RIGHT_PERCENT,\
                                        ConvertVideoLectureToImage.SUB_MARGIN_BOTTOM_PERCENT,\
                                        )
                            )
    appearance.add_argument('-lbm',"--line-bottom-margin-in-percent",\
                        help="\nLine bottom margin in percent of line height Default: {0}".format(ConvertVideoLectureToImage.SUB_LINE_MARGIN_BOTTOM),\
                        default=ConvertVideoLectureToImage.SUB_LINE_MARGIN_BOTTOM,\
                        metavar=("BOTTOM_MARGIN"),
                        type=float)

    appearance.add_argument('-bsz',"--border-size",\
                        help="Text border size\n Default: {0}".format(ConvertVideoLectureToImage.BORDER_SIZE),\
                        default=ConvertVideoLectureToImage.BORDER_SIZE,\
                        metavar=("BORDER SIZE"),
                        type=int)

    appearance.add_argument('-bcl',"--border-color",\
                        help="Text border color\n Default: {0}".format(ConvertVideoLectureToImage.BORDER_COLOR),\
                        default=ConvertVideoLectureToImage.BORDER_COLOR,\
                        metavar=(("R","G","B")),
                        type=int,nargs=3)

    appearance.add_argument("-fs","--font-scale",\
                        help="Font scale\n (NOT AVAILABLE IN UNICODE MODE in Unicode mode)Default: {0}".format(ConvertVideoLectureToImage.FONTSCALE),\
                        default=ConvertVideoLectureToImage.FONTSCALE,type=float)
    appearance.add_argument("-ff","--font-face",\
                        help="""
                            (NOT AVAILABLE IN UNICODE MODE)
                            Font face. Default: FONT_HERSHEY_PLAIN
                            font-face list:
                                FONT_HERSHEY_SIMPLEX: normal size sans-serif font
                                FONT_HERSHEY_PLAIN: small size sans-serif font
                                FONT_HERSHEY_DUPLEX: normal size sans-serif font
                                FONT_HERSHEY_COMPLEX: normal size serif font
                                FONT_HERSHEY_TRIPLEX: normal size serif font
                                FONT_HERSHEY_COMPLEX_SMALL: smaller version of FONT_HERSHEY_COMPLEX
                                FONT_HERSHEY_SCRIPT_SIMPLEX: hand-writing style font
                                FONT_HERSHEY_SCRIPT_COMPLEX: more complex variant of FONT_HERSHEY_SCRIPT_SIMPLEX
                        """,\
                        default=ConvertVideoLectureToImage.FONT_FACE,type=str)

    appearance.add_argument('-tn',"--thickness",\
                        help="Thickness\n Default: {0}".format(ConvertVideoLectureToImage.THICKNESS),\
                        default=ConvertVideoLectureToImage.THICKNESS,type=int)
    appearance.add_argument('-tml',"--time-margin-right-percent",\
                        help="Time margin right\n Default: {0}".format(ConvertVideoLectureToImage.TIME_MARGIN_RIGHT_PERCENT)\
                        ,type=float,default=ConvertVideoLectureToImage.TIME_MARGIN_RIGHT_PERCENT)

    appearance.add_argument('-tmt',"--time-margin-top-percent",\
                        help="Time margin top\n Default: {0}".format(ConvertVideoLectureToImage.TIME_MARGIN_TOP_PERCENT)\
                        ,type=float,default=ConvertVideoLectureToImage.TIME_MARGIN_TOP_PERCENT)
    appearance.add_argument('-dt',"--difference-threshold",\
                        help="Use threshold to remove duplicate mid,end\n Default: {0}".format(ConvertVideoLectureToImage.DIFF_THRESHOLD)\
                        ,type=int,default=ConvertVideoLectureToImage.DIFF_THRESHOLD)

    #diff_threshold
    others = parser.add_argument_group('Others'.upper())
    others.add_argument('-ct',"--collision-shifting-time",\
                        help="Avoid the instance which the next image have same subtitle with current one\n Default: {0}"\
                            .format(ConvertVideoLectureToImage.COLLISION_SHIFTING_MILISECONDS),\
                            default=ConvertVideoLectureToImage.COLLISION_SHIFTING_MILISECONDS)
    others.add_argument('-cljpg',"--compress-level-jpg",\
                        help="Compress level for JPG | JPEG output images, Value range: [0-100]\n Default: {0}"\
                            .format(ConvertVideoLectureToImage.COMPRESS_LEVEL_JPG),\
                            default=ConvertVideoLectureToImage.COMPRESS_LEVEL_JPG,type=int)
    others.add_argument('-clpng',"--compress-level-png",\
                        help="Compress level for PNG output images, Value range: [0-9]\n Default: {0}"\
                            .format(ConvertVideoLectureToImage.COMPRESS_LEVEL_PNG),\
                            default=ConvertVideoLectureToImage.COMPRESS_LEVEL_PNG,type=int)
    others.add_argument('-t',"--test",\
                        help="""Generate image for testing purpose(only n or 2n or 3n image based on whether or not picking image middle,end)
                                . Default: n=%i""" % ConvertVideoLectureToImage.TEST_NUM_IMAGE,\
                        default=ConvertVideoLectureToImage.TEST_NUM_IMAGE,type=int)
    others.add_argument('-R',"--resume",\
                        help="""To resume currupt process ( required same video,srt,output folder,middle,start,end parameters
                                . Default: n=%i""" % ConvertVideoLectureToImage.RESUME,\
                        default=ConvertVideoLectureToImage.RESUME,action="store_true")

    return parser
def get_converter(args):
    c = ConvertVideoLectureToImage(args.video_file_path,\
                                    args.sub_file_path,\
                                    args.output_path)
    c.FONTSCALE = args.font_scale
    c.FONT_FACE = args.font_face
    c.THICKNESS = args.thickness
    c.TEXT_COLOR = args.subtitle_color
    c.TO_GRAYSCALE = args.to_grayscale
    c.UNICODE = args.unicode_mode
    c.FONT_SIZE = args.font_size
    c.FONT_PATH = args.font_path
    c.BORDER_COLOR = args.border_color
    c.BORDER_SIZE = args.border_size

    c.SUB_MARGIN_LEFT_PERCENT,c.SUB_MARGIN_RIGHT_PERCENT,c.SUB_MARGIN_BOTTOM_PERCENT=\
        args.subtitle_margin_percent
    c.SUB_LINE_MARGIN_BOTTOM = args.line_bottom_margin_in_percent
    c.COLLISION_SHIFTING_MILISECONDS = args.collision_shifting_time

    c.TEST_NUM_IMAGE = args.test

    c.TO_TAR = args.to_tar

    c.SHOW_END = args.get_end_image
    c.SHOW_MID = args.get_middle_image
    c.SHOW_TIME = args.show_time

    c.TIME_MARGIN_RIGHT_PERCENT = args.time_margin_right_percent
    c.TIME_MARGIN_TOP_PERCENT = args.time_margin_top_percent


    c.COOKIE_JSON_PATH = args.cookie_json_path

    c.IMAGE_OUTPUT_TYPE = args.image_output_type

    c.RESUME = args.resume

    c.COMPRESS_LEVEL_JPG = args.compress_level_jpg
    c.COMPRESS_LEVEL_PNG = args.compress_level_png

    c.REMOVE_OUTPUT_IMG = args.remove_output_images

    c.IMAGE_OUTPUT_WIDTH = args.image_output_width
    c.IMAGE_OUTPUT_HEIGHT = args.image_output_height
    c.IS_RESIZE = args.enable_resize_output_image

    c.MASS_MODE = args.mass_mode

    c.DIFF_THRESHOLD = args.difference_threshold
    c.VIDEO_EXTENSION = args.video_extensions


    c.MAX_RETRY_NUMBER = args.max_retry_number

    c.outputPath = args.output_path
    return c


def gen_image_from_link(args, cookies, orgOutputPath, row):
    subTempFile = tempfile.NamedTemporaryFile('w', delete=False)
    subTitleContent = GetLink(row[0], cookies).getContent()
    subTempFile.write(subTitleContent)
    subTempName = subTempFile.name
    subTempFile.close()
    args.video_file_path = GetLink(url=row[1], cookiesJsonContent=cookies).get()
    outputFolderName = row[-1]
    args.sub_file_path = subTempName
    args.output_path = orgOutputPath + '/' + outputFolderName
    get_converter(args).gen_image()
    os.unlink(subTempName)


def main():
    parser = menu()
    args = parser.parse_args()
    start = time.clock()
    if args.mass_mode:
        orgOutputPath = args.output_path
        if args.folder_subs_path:
            for sub_file in filter(lambda f: re.search(r"\{0}".format(ConvertVideoLectureToImage.SUBTITLE_EXT), f),\
                                os.listdir(args.folder_subs_path)):
                try:
                    args.video_file_path = ''
                    args.sub_file_path = os.path.join(args.folder_subs_path,sub_file)
                    args.output_path = '' if orgOutputPath=='' else  orgOutputPath + '/' + path.basename(args.sub_file_path)
                    get_converter(args).gen_image()
                except Exception:
                    continue
        elif args.recursive_folder_path:
            matches = []
            for root, dirnames, filenames in os.walk(args.recursive_folder_path):
              for filename in fnmatch.filter(filenames, '*{0}'.format(ConvertVideoLectureToImage.SUBTITLE_EXT)):
                    matches.append(os.path.join(root, filename))
            for sub_path in matches:
                args.video_file_path = ''
                args.sub_file_path = sub_path
                args.output_path = '' if orgOutputPath=='' else  orgOutputPath + '/' + path.basename(args.sub_file_path)
                get_converter(args).gen_image()
        elif args.list_video_json_path:
            if args.output_path == '':
                raise Exception("Require setting output path")
            rowList =json.loads(open(args.list_video_json_path,'r').read())
            cookies = ''
            if args.cookie_json_path:
                cookies = open(args.cookie_json_path,'r').read()
            for row in filter(lambda x: x[0],rowList):
                gen_image_from_link(args, cookies, orgOutputPath, row)
    else:
        get_converter(args).gen_image()
    elapsed = time.clock() - start
    sys.stdout.write("\nElapsed time: %s\n" % datetime.timedelta(seconds=elapsed))


if __name__ == '__main__':
    main()
