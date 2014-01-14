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
from ConvertVideoLectureToImage import *
import argparse
def menu():
    parser = argparse.ArgumentParser(description='Convert video lecture to image')
    parser.add_argument('-vp','--video-file-path',help="Path to video file",required=True)
    parser.add_argument('-sp','--sub-file-path',help="Path to subtitle file",default='')
    parser.add_argument('-sc',"--subtitle-color",help="Subtitle color R G B, value=0..255\n Default: %s" % str(ConvertVideoLectureToImage.TEXT_COLOR)\
                        ,type=int,nargs=3,required=False,metavar=('R','G','B'),default=ConvertVideoLectureToImage.TEXT_COLOR)
    parser.add_argument('-sm',"--subtitle-margin-percent",\
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
    parser.add_argument("-G","--to-grayscale",\
                        help="Font scale\n Default: {0}".format(ConvertVideoLectureToImage.TO_GRAYSCALE),\
                        default=ConvertVideoLectureToImage.TO_GRAYSCALE,
                        action="store_true")
    parser.add_argument('-U',"--unicode-mode",\
                        help="Support unicode subtitle\n Default: {0}".format(ConvertVideoLectureToImage.UNICODE),\
                        default=ConvertVideoLectureToImage.UNICODE,\
                        action="store_true")

    parser.add_argument('-fp',"--font-path",\
                        help="Font path (required in Unicode mode only) ( require TrueFont type)\n Default: {0}"\
                                        .format(ConvertVideoLectureToImage.FONT_PATH),\
                        default=ConvertVideoLectureToImage.FONT_PATH,\
                        metavar=("FONT PATH"))

    parser.add_argument('-fsz',"--font-size",\
                        help="Font size (in Unicode mode only)\n Default: {0}".format(ConvertVideoLectureToImage.FONT_SIZE),\
                        default=ConvertVideoLectureToImage.FONT_SIZE,\
                        metavar=("FONT SIZE"),
                        type=int)

    parser.add_argument('-bsz',"--border-size",\
                        help="Text border size\n Default: {0}".format(ConvertVideoLectureToImage.BORDER_SIZE),\
                        default=ConvertVideoLectureToImage.BORDER_SIZE,\
                        metavar=("BORDER SIZE"),
                        type=int)

    parser.add_argument('-bcl',"--border-color",\
                        help="Text border color\n Default: {0}".format(ConvertVideoLectureToImage.BORDER_COLOR),\
                        default=ConvertVideoLectureToImage.BORDER_COLOR,\
                        metavar=(("R","G","B")),
                        type=int,nargs=3)

    parser.add_argument("-fs","--font-scale",\
                        help="Font scale\n Default: {0}".format(ConvertVideoLectureToImage.FONTSCALE),\
                        default=ConvertVideoLectureToImage.FONTSCALE,type=float)
    parser.add_argument("-ff","--font-face",\
                        help="""
                            Font face. Default: FONT_HERSHEY_PLAIN
                            Available font-face:
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

    parser.add_argument('-tn',"--thickness",\
                        help="Thickness\n Default: {0}".format(ConvertVideoLectureToImage.THICKNESS),\
                        default=ConvertVideoLectureToImage.THICKNESS,type=int)
    parser.add_argument('-ct',"--collision-shifting-time",\
                        help="Collision shifting time(mil)\n Default: {0}"\
                            .format(ConvertVideoLectureToImage.COLLISION_SHIFTING_MILISECONDS),\
                            default=ConvertVideoLectureToImage.COLLISION_SHIFTING_MILISECONDS)


    parser.add_argument('-t',"--test-2n-image",\
                        help="Generate only 2*n first images. Default: n=%i" % ConvertVideoLectureToImage.TEST_NUM_IMAGE,\
                        default=ConvertVideoLectureToImage.TEST_NUM_IMAGE,type=int)
    parser.add_argument('-o',"--output-path",\
                        help="Output images path. Default: <video_file_name_folder>",\
                        default='')
    #return parser.parse_args()
    return parser
def main():
    parser = menu()
    args = parser.parse_args()
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
    c.COLLISION_SHIFTING_MILISECONDS = args.collision_shifting_time
    c.TEST_NUM_IMAGE = args.test_2n_image
    print c.subPath
    c.genImage()
if __name__ == '__main__':
    main()
