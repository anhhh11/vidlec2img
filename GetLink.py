#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      user
#
# Created:     16/01/2014
# Copyright:   (c) user 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    pass

if __name__ == '__main__':
    main()
import json
import requests
class GetLink:
    def __init__(self,url,data='',cookiesJsonPath=''):
        self.url = url
        self.data = data
        self.cookiesJsonPath = cookiesJsonPath
    def get(self):
        if self.cookiesJsonPath != '':
            cookiesJson=json.load(open(self.cookiesJsonPath,'r'))
            cookies = dict(map(lambda cookie: (cookie["name"],cookie["value"]),cookiesJson))
        else:
            cookies = {}
        self.request = requests.head(self.url,\
                        cookies=cookies,\
                        allow_redirects=True,
                        stream=True)
        return self.request.url

##a=""""""
##
##print requests.utils.unquote_header_value("https://d28rh4a8wq0iu5.cloudfront.net/powerofmarkets/recoded_videos/PoM%2001%20-%20Course%20Materials%20and%20General%20Advice.8a2af429cc3a57b2aada027b5791bf8c.mp4?response-content-type=application%2Foctet-stream&a=1&response-content-disposition=attachment%3B%20filename%3D%222%2520-%25201%2520-%2520Course%2520Materials%2520and%2520General%2520Advice%2520%25286%253A55%2529.mp4%22%3B%20filename%2A%3DUTF-8%27%272%2520-%25201%2520-%2520Course%2520Materials%2520and%2520General%2520Advice%2520%25286%253A55%2529.mp4")
##cookiesJson = json.loads(a)
##cookies = dict(map(lambda cookie: (cookie["name"],cookie["value"]),cookiesJson))
##r=requests.head("https://class.coursera.org/powerofmarkets-001/lecture/download.mp4?lecture_id=109",cookies=cookies,allow_redirects=True)
##print r.url
