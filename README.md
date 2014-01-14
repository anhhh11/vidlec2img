==========
vidlec2img
==========
Convert video lecture + subtitle to images

Python tool to convert video to image ( especially video lectures)
Usage:
python vidlec2img.py --video-file-path ~/home/test.mp4
By default subtitle should be in same folder as video file with extension .srt.
For more detail running with --help flag
Requirement:
Python 2.7.6
Numpy MKL-1.8.0
OpenCV 2.4.7 or 2.4.8
Pillow 2.3.0
Can download numpy and opencv and pillow from here: http://www.lfd.uci.edu/~gohlke/pythonlibs/

I've added text border's option ( or text shadow) with --border-size and --border-color parameters

To write unicode subtitle turn on -U flag and set path to TrueFont type using -fp (for example: -fp C:/fonts/Arial.ttf ) ; and this tool allow to set Font size.
