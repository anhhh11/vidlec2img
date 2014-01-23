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