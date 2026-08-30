#!/usr/bin/env python3

import requests
import random
import time
import hashlib
import string
import re
import core.config
from urllib.parse import urlparse,parse_qs

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

CALLBACK_PORT = 8091
CALLBACK_CODE = None

class OauthRequestCatcher(BaseHTTPRequestHandler):
  def do_GET(self):
    parsed = urlparse(self.path)
    if parsed.path == "/callback":
      global CALLBACK_CODE
      params = parse_qs(parsed.query)
      CALLBACK_CODE = params.get("code", [None])[0]
    self.send_response(200)
    self.send_header("Content-Type", "text/plain")
    self.end_headers()
    self.wfile.write(b"hello from lydia/core/oauth")

  def log_message(self, format, *args):
    pass
  
class OauthCatcher:
  global CALLBACK_PORT
  def __init__(self, host="127.0.0.1", port=CALLBACK_PORT,handler_class=OauthRequestCatcher):
    self.server = HTTPServer((host, port), handler_class)
    self.thread = None

  def start(self):
    if self.thread and self.thread.is_alive():
      return
    self.thread = threading.Thread(
      target=self.server.serve_forever,
      daemon=True
    )
    self.thread.start()

  def stop(self):
    self.server.shutdown()
    self.server.server_close()
    if self.thread:
      self.thread.join()

  def serve_forever(self):
    try:
      self.server.serve_forever()
    finally:
      self.server.server_close()

SSL_VERIFY = core.config.getenv("SSL_VERIFY","True") == "True"

class OauthImpl:
  def dynamic_register_client(self,reg_url):
    global CALLBACK_PORT
    print("oauth: attempting dynamic client registration as 'lydia'")
    pp = requests.post(reg_url,json = {"client_name":"lydia","redirect_uris":["http://localhost:%d/callback" % CALLBACK_PORT]})
    resp = pp.json()
    if "client_id" in resp.keys():
      print("oauth: dynamic register successful, client_id '%s'" % resp["client_id"])
      return resp["client_id"]
    else:
      return input("oauth: dynamic client register failed, enter client_id > ").rstrip()

  def user_3lo_auth(self,rsrc_metadata,auth_metadata):
    global CALLBACK_PORT, CALLBACK_CODE
    print(rsrc_metadata)
    print(auth_metadata)
    cv_raw = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    code_challenge = hashlib.sha256(cv_raw.encode("utf-8")).hexdigest()
    auth_endp = auth_metadata["authorization_endpoint"]
    token_endp = auth_metadata["token_endpoint"]
    mcp_scope="+".join(rsrc_metadata["scopes_supported"])
    print("")
    print(cv_raw)
    print(code_challenge)
    print("oauth: authenticate to:")
    print("%s?response_type=code&client_id=%s&redirect_uri=http://localhost:%d/callback&scope=%s&code_challenge=%s&code_challenge_method=S256" % (auth_endp,self.client_id,CALLBACK_PORT,mcp_scope,code_challenge))
    print("")
    server = OauthCatcher(host="localhost",port=CALLBACK_PORT)
    server.start()
    input("oauth: press enter when catcher done")
    server.stop()
    if CALLBACK_CODE is None:
      print("oauth: fatal, did not get callback code")
      sys.exit(0)
    print("oauth: got oauth code len(%d)" % len(CALLBACK_CODE))
    print("oauth: exchanging oauth code for access token...")
    def hexdigest(in_bytes):
      return "".join(["%02x" % b for b in in_bytes])
    payload = {
      "grant_type":"authorization_code",
      "client_id":self.client_id,
      "code":CALLBACK_CODE,
      "code_verifier":cv_raw,
      "redirect_uri":"http://localhost:%d/callback" % CALLBACK_PORT
    }
    print(payload)
    # "redirect_uri":"http://localhost:%d/callback" % CALLBACK_PORT,
    pp = requests.post(token_endp,json=payload,verify=SSL_VERIFY)
    while pp.status_code == 202:
      print("Polling...")
      time.sleep(1.0)
      pp = requests.post(token_endp,json=payload,verify=SSL_VERIFY)
    print(pp.json())

  def __init__(self,auth_hdr,base_url):
    global SSL_VERIFY
    print("oauth: got auth header")
    self.base_url = base_url
    match = re.search(r'\bresource_metadata\s*=\s*"([^"]*)"', auth_hdr)
    if not match:
      print("oauth: could not find resource_metadata in auth header")
      print(auth_hdr)
      sys.exit(0)
    rm_url = match.group(1)
    pp = requests.get(rm_url,verify=SSL_VERIFY)
    resource_metadata = pp.json()
    # print(resource_metadata)
    auth_url = random.choice(resource_metadata["authorization_servers"])
    print("oauth: selected '%s' auth server" % auth_url)
    pp = requests.get("/".join([auth_url,".well-known/oauth-authorization-server"]),verify=SSL_VERIFY)
    if pp.status_code != 200:
      auth_discov = core.config.getsubvar("MCP_AUTH_METADATA",base_url,None)
      if auth_discov is None:
        print("oauth: could not find authorization server metadata for mcp '%s'" % base_url)
        sys.exit(0)
      pp = requests.get(auth_discov,verify=SSL_VERIFY)
    auth_metadata = pp.json()
    if "registration_endpoint" in auth_metadata.keys():
      self.client_id = self.dynamic_register_client(auth_metadata["registration_endpoint"])
    else:
      self.client_id = input("oauth: enter client id > ").rstrip()
    self.user_3lo_auth(resource_metadata,auth_metadata)
    # sys.exit(0)
