#!/usr/bin/env python3

import requests
import json
import sys
from typing import Annotated

def devtools(method: Annotated[str,"The HTTP method"],path: Annotated[str, "The request path, starting with '/'"], body: Annotated[str, "The request body in JSON"]):
  print("info: called chrome_debug(%s,%s,%s)" % (method,path,body))
  if len(body) == 0:
    resp = requests.request(method=method,url="http://localhost:9222%s" % path,verify=False)
  else:
    resp = requests.request(method=method,url="http://localhost:9222%s" % path,json=body,verify=False)
  print(resp.status_code)
  # sys.exit(0)
  # print(resp.text)
  return resp.text
