#!/usr/bin/env python3

import requests
from typing import Annotated

def web_request(method: Annotated[str, "request method"], url: Annotated[str, "request url, including protocol"], data: Annotated[str, "request data. leave blank by default."]):
  print("info: web_request(method='%s',url='%s',data='%s') called" % (method,url,data))
  if len(data) == 0:
    response = requests.request(method=method,url=url,verify=False)
  else:
    response = requests.request(method=method,url=url,data=data,verify=False)
  status_line = f"HTTP/1.1 {response.status_code} {response.reason}" 
  headers = "\n".join(f"{key}: {value}" for key, value in response.headers.items())
  data = response.text
  raw_http_response = f"{status_line}\n{headers}\n\n{data}"
  print("info: web request returning, status '%s'" % status_line)
  return raw_http_response

def web_download_file(method: Annotated[str, "request method"], url: Annotated[str, "request url, including protocol"], data: Annotated[str, "request data. leave blank by default."], filename: Annotated[str, "location to save the file"]):
  print("info: web_download_file(method='%s',url='%s',data='%s',filename='%s') called" % (method,url,data,filename))
  if len(data) == 0:
    response = requests.request(method=method,url=url,verify=False)
  else:
    response = requests.request(method=method,url=url,data=data,verify=False)
  status_line = f"HTTP/1.1 {response.status_code} {response.reason}"
  with open(filename,"wb") as f:
    f.write(response.content)
  # raw_http_response = f"{status_line}\n{headers}\n\n{data}"
  print("info: web request returning, status '%s'" % status_line)
  if response.status_code == 200:
    return "ok"
  else:
    return status_line
