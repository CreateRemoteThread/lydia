#!/usr/bin/env python3

import requests
import random
import hashlib
import string
import re
import core.config

SSL_VERIFY = core.config.getenv("SSL_VERIFY","True") == "True"

class OauthImpl:
  def dynamic_register_client(self,reg_url):
    print("oauth: attempting dynamic client registration as 'lydia'")
    pp = requests.post(reg_url,json = {"client_name":"lydia","redirect_uris":["http://localhost:8089/callback"]})
    resp = pp.json()
    if "client_id" in resp.keys():
      print("oauth: dynamic register successful, client_id '%s'" % resp["client_id"])
      return resp["client_id"]
    else:
      return input("oauth: dynamic client register failed, enter client_id > ").rstrip()

  def user_3lo_auth(self,rsrc_metadata,auth_metadata):
    code_verifier = ''.join(random.choices(string.ascii_letters + string.digits, k=16)).encode("utf-8")
    code_challenge = hashlib.sha256(code_verifier).hexdigest()
    auth_endp = auth_metadata["authorization_endpoint"]
    mcp_scope="+".join(rsrc_metadata["scopes_supported"])
    print("")
    print("oauth: authenticate to:")
    print("%s?response_type=code&client_id=%s&redirect_uri=http://localhost:8089/callback&scope=%s&code_challenge=%s&code_challenge_method=S256" % (auth_endp,self.client_id,mcp_scope,code_challenge))
    print("")

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
    print(resource_metadata)
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
