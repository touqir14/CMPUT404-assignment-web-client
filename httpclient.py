#!/usr/bin/env python
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib
import urlparse

def help():
    print "httpclient.py [GET/POST] [URL]\n"

class HTTPResponse(object):
    def __init__(self, code=200, body="", header=""):
        self.code = code
        self.body = body
        self.header = header

    def std_out(self):
        print "status code: %s\nHeaders: \n\n%s\nBody: \n\n%s" % (self.code, self.header, self.body)


class HTTPClient(object):

    def connect(self, host, port):
        # use sockets!
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((host, port))
        return clientSocket

    def get_code(self, data):
        status_code=int(data.split(" ")[1])
        return status_code

    # def get_headers(self,data):
    #     return None

    # def get_body(self, data):
    #     return None

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return str(buffer)

    def GET(self, url, args=None):
        parsed=self.parseURL(url)
        if type(args) is dict:
            #TODO: Process args dictionary
            clientSocket=self.connect(parsed["host"], parsed["port"])
        elif args is None:
            clientSocket=self.connect(parsed["host"], parsed["port"])
            GET_request=self.gen_GET_text(parsed["host"], parsed["path"])

        clientSocket.sendall(GET_request)
        response_text=self.recvall(clientSocket)
        response_obj=self.parseResponse(response_text)
        
        return response_obj

    def POST(self, url, args=None):
        parsed=self.parseURL(url)
        if type(args) is dict:
            clientSocket=self.connect(parsed["host"], parsed["port"])
            POST_request=self.gen_POST_text(parsed["host"], parsed["path"], args)
        elif args is None:
            clientSocket=self.connect(parsed["host"], parsed["port"])
            POST_request=self.gen_POST_text(parsed["host"], parsed["path"], args)

        clientSocket.sendall(POST_request)
        response_text=self.recvall(clientSocket)
        response_obj=self.parseResponse(response_text)
        
        return response_obj

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )

    def gen_POST_text(self, host, path, content_dict=None):

        if path=="":
            path="/"

        if content_dict is not None:
            content=urllib.urlencode(content_dict)
            content_length=len(content)
        else:
            content="" 
            content_length=0

        text="POST %s HTTP/1.1\r\n" % (path)
        text+="Host: %s\r\n" % (host)
        # text+="Connection: close\r\n"
        text+="User-Agent: httpclient/1.0\r\n"
        text+="Accept-Encoding: gzip\r\n"
        text+="Accept-Charset: ISO-8859-1,UTF-8;q=0.7,*;q=0.7\r\n"
        text+="Cache-Control: no-cache\r\n"
        text+="Accept-Language: de,en;q=0.7,en-us;q=0.3\r\n"
        
        text+="Content-Type: application/x-www-form-urlencoded\r\n"
        text+="Content-Length: %d\r\n\r\n" % (content_length)
        text+="%s\r\n" % (content)
        text+="\r\n"

        return text

    def gen_GET_text(self, host, path, content_dict=None):

        if path=="":
            path="/"

        if content_dict is not None:
            content=urllib.urlencode(content_dict)
            content_length=len(content)
        else:
            content="" 
            content_length=0

        text="GET %s HTTP/1.1\r\n" % (path)
        text+="Host: %s\r\n" % (host)
        text+="Connection: close\r\n"
        text+="User-Agent: httpclient/1.0\r\n"
        # text+="Accept-Encoding: gzip\r\n"
        text+="Accept-Encoding: identity\r\n"
        text+="Accept-Charset: ISO-8859-1,UTF-8;q=0.7,*;q=0.7\r\n"
        text+="Cache-Control: no-cache\r\n"
        text+="Accept-Language: de,en;q=0.7,en-us;q=0.3\r\n"
        text+="\r\n"

        return text

    def parseResponse(self, response):

        status_code=self.get_code(response)
        index=response.find('\r\n\r\n')
        # print response
        if index != -1:
            body=response[index+4:]
            header=response[:index+2]
            header, body=self.processBody(header, body)
        else:
            body=""
            header=""

        return HTTPResponse(status_code, body, header)    

    def parseURL(self, URL):
        
        parsed={}
        if "http" not in URL:
            splitted=URL.split("/")
            if ":" not in splitted[0]:
                parsed["host"]=splitted[0]
                parsed["port"]=80
            else:
                parsed["host"]=splitted[0].split(":")[0]
                parsed["port"]=int(splitted[0].split(":")[1])
            parsed["path"]="/"+"/".join(splitted[1:])

        else:

            if "https" in URL:
                splitted=URL.split("/")
                del splitted[1]
                if ":" not in splitted[1]:
                    parsed["host"]=splitted[1]
                    parsed["port"]=443
                else:
                    parsed["host"]=splitted[1].split(":")[0]
                    parsed["port"]=int(splitted[1].split(":")[1])

            else: #in case http is there
                splitted=URL.split("/")
                del splitted[1]
                if ":" not in splitted[1]:
                    parsed["host"]=splitted[1]
                    parsed["port"]=80
                else:
                    parsed["host"]=splitted[1].split(":")[0]
                    parsed["port"]=int(splitted[1].split(":")[1])
            parsed["path"]="/"+"/".join(splitted[2:])

        # if URL[-1]!="/":
        #     parsed["path"]=parsed["path"][:-1]

        print parsed

        return parsed

    def processBody(self, header, body):

        # print header

        for line in header.split("\r\n"):
            if "charset=" in line and "text/html" in line:
                encoding=line.split("charset=")[1]
                body=unicode(body, encoding)
                break
        
        return [header, body]


if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        client.command( sys.argv[2], sys.argv[1] ).std_out()
    else:
        client.command( sys.argv[1] ).std_out()   
