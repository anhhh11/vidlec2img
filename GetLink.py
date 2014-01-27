# -*- coding: utf-8 -*-
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

import json
import requests
class GetLink:
    def __init__(self,url,data='',cookiesJsonContent=''):
        self.url = url
        self.data = data
        self.cookiesJsonContent = cookiesJsonContent
        self.readCookie()
    def readCookie(self):
        if self.cookiesJsonContent != '':
            cookiesJson=json.loads(self.cookiesJsonContent)
            self.cookies = dict(map(lambda cookie: (cookie["name"],cookie["value"]),cookiesJson))
        else:
            self.cookies = {}
    def get(self):
        self.request = requests.head(self.url,\
                        cookies=self.cookies,\
                        allow_redirects=True,
                        stream=True)
        return self.request.url
    def getContent(self):
        self.request = requests.get(self.url,\
                        cookies=self.cookies,\
                        allow_redirects=True,
                        stream=True)
        return self.request.content



if __name__ == '__main__':
    main()
    from GetLink import GetLink
"""
"""