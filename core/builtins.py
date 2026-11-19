#!/usr/bin/env python3

import sys
import glob
import sys
import os
import core.config
import core.sandbox
from os.path import expanduser, normpath
import subprocess
from pathlib import Path
import random
import requests
from typing import Annotated
import pty
import select
import signal
import termios
import time
import fcntl
import struct
import queue, threading
import re

SSL_VERIFY = core.config.getenv("SSL_VERIFY","True") == "True"
MAX_DATA = 1024 * 1024 * 2
RISK_ACCEPT = None
VM_SSHARGS = None

def risk_accept():
  global RISK_ACCEPT
  if RISK_ACCEPT is None:
    RISK_ACCEPT = core.config.getenv("I_ACCEPT_THE_RISK",default=None)
    if RISK_ACCEPT == "ISO27001":
      RISK_ACCEPT = True
    else:
      RISK_ACCEPT = False
  return RISK_ACCEPT

def vm_sshargs():
  global VM_SSHARGS
  if VM_SSHARGS is None:
    VM_SSHARGS = core.config.getenv("VM_SSHARGS",default="")
  else:
    return VM_SSHARGS

PROCESS_LOCK = None

CMD_FW = None

def cmdfw(command):
  global CMD_FW
  if CMD_FW is None:
    CMD_FW = core.config.getenv("CMD_FW", default=None)
    if CMD_FW is not None:
      CMD_FW = [a.strip() for a in CMD_FW.split(",")]
  print("fw: firewalling '%s'" % command)

  if CMD_FW is None:
    manual_allow = input("fw: CMD_FW whitelist unset. allow this once? [y/N] > ").rstrip()
    if manual_allow == "y":
      print("fw: command manually permitted")
      return True
    print("fw: command not permitted")
    return False
  else:
    cmd0 = command.split()[0]
    if cmd0 in CMD_FW:
      print("fw: command whitelisted, allowing")
      return True
    else:
      print("fw: command not in whitelist, denying")
      return False

def fwreject():
  global CMD_FW
  if CMD_FW is None:
    return "error: permission denied by user"
  else:
    return "error: permission denied by firewall. allowed commands: %s" % " ".join(CMD_FW)

class ProcessPty:
  def __init__(self,command):
    global pyte
    try:
      import pyte
    except:
      print("fatal: term requires pyte library")
      sys.exit(-1)
    self.screen = pyte.Screen(80,24)
    self.stream = pyte.ByteStream(self.screen)
    self.master_fd, self.slave_fd = pty.openpty()
    self._set_winsize(self.slave_fd,80,24)
    cmd_tokens = command.split()
    self.proc = subprocess.Popen(cmd_tokens, stdin=self.slave_fd, stdout=self.slave_fd, stderr=self.slave_fd, preexec_fn=os.setsid,close_fds=True)
    # print(self.proc)
    os.close(self.slave_fd)

  def _set_winsize(self,fd,rows,cols):
    winsize = struct.pack("HHHH", cols, rows, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

  def _read(self,timeout=0.2,max_bytes=65535):
    output = b""
    end_time = time.time()+ timeout
    while time.time() < end_time:
      r,_,_ = select.select([self.master_fd],[],[],0.05)
      if self.master_fd in r:
        try:
          chunk = os.read(self.master_fd,1024)
          if not chunk:
            break
          output += chunk
          self.stream.feed(chunk)
          if len(output) >= max_bytes:
            break
        except OSError:
          break
    return output.decode(errors="replace")

  def interact(self,data):
    os.write(self.master_fd,data.encode())
    return self.screen_scrape()

  def screen_scrape(self):
    self._read(0.2)
    # print("\n".join(self.screen.display))
    return "\n".join(self.screen.display)

  def close(self):
    self.proc.kill()

def term_start(command: Annotated[str, "The command to run"]):
  global PROCESS_LOCK
  if PROCESS_LOCK is not None:
    print("warn: term_start called with PROCESS_LOCK on")
    return "info: you need to call term_kill before starting a new process"
  if cmdfw(command) is False:
    return fwreject()
  if risk_accept() is True:
    print("warn: term_start('%s') called, locking pretend mutex, running locally" % command)
    PROCESS_LOCK = ProcessPty(command)
    time.sleep(0.5)
    return "ok. screen scraped:\n" + PROCESS_LOCK.screen_scrape()
  else:
    print("fatal: term_start without I_ACCEPT_THE_RISK, not handled")
    sys.exit(-1) 

def term_locatechr(chrcode: Annotated[int, "The ASCII code of the character to locate"]):
  global PROCESS_LOCK
  print("info: term_locatechr(%d) called" % chrcode)
  # if len(char) != 1:
  #   return "error: term_locatechr takes exactly a single byte"
  disp = PROCESS_LOCK.screen.display
  y_max = len(disp)
  x_max = len(disp[0]) 
  locations = []
  for y in range(0,y_max):
    for x in range(0,x_max):
      if ord(disp[y][x]) == chrcode:
        locations.append( (x,y) )
  if len(locations) == 0:
    return "not found"
  else:
    return "found at: " + ", ".join(["(x:%d,y:%d)" % (x,y) for (x,y) in locations])

def term_screen_scrape():
  global PROCESS_LOCK
  print("info: term_screen_scrape() called")
  if PROCESS_LOCK is None:
    return "error: use term_start to start the process first"
  else:
    return PROCESS_LOCK.screen_scrape()

def term_interact(data: Annotated[str, "The data to send"]):
  global PROCESS_LOCK
  print("info: term_interact('%s') called" % data)
  data = PROCESS_LOCK.interact(data)
  return "ok"

def web_request(method: Annotated[str, "request method"], url: Annotated[str, "request url, including protocol"], data: Annotated[str, "request data. leave blank by default."]):
  global SSL_VERIFY
  print("info: web_request(method='%s',url='%s',data='%s') called" % (method,url,data))
  if len(data) == 0:
    response = requests.request(method=method,url=url,verify=SSL_VERIFY)
  else:
    response = requests.request(method=method,url=url,data=data,verify=SSL_VERIFY)
  status_line = f"HTTP/1.1 {response.status_code} {response.reason}" 
  headers = "\n".join(f"{key}: {value}" for key, value in response.headers.items())
  data = response.text
  raw_http_response = f"{status_line}\n{headers}\n\n{data}"
  print("info: web request returning, status '%s'" % status_line)
  return raw_http_response

def web_download_file(method: Annotated[str, "request method"], url: Annotated[str, "request url, including protocol"], data: Annotated[str, "request data. leave blank by default."], filename: Annotated[str, "location to save the file"]):
  print("info: web_download_file(method='%s',url='%s',data='%s',filename='%s') called" % (method,url,data,filename))
  global SSL_VERIFY
  if len(data) == 0:
    response = requests.request(method=method,url=url,verify=SSL_VERIFY)
  else:
    response = requests.request(method=method,url=url,data=data,verify=SSL_VERIFY)
  status_line = f"HTTP/1.1 {response.status_code} {response.reason}"
  filename = core.sandbox.is_path_safe(filename)
  if filename is False:
    return "error: filename path forbidden by sandbox"
  while os.path.isfile(filename) is True:
    print("warn: web_download_file attempting to overwrite")
    filename = filename + ".%d" % random.randint(0,100)
  with open(filename,"wb") as f:
    f.write(response.content)
  # raw_http_response = f"{status_line}\n{headers}\n\n{data}"
  print("info: web request returning, status '%s'" % status_line)
  if response.status_code == 200:
    return "ok, saved as '%s'" % filename
  else:
    return status_line

def file_rg(pattern: Annotated[str, "pattern to pass to search for with ripgrep."], location: Annotated[str, "location to search. use '.' for current directory"]):
  print("info: file_rg('%s','%s') called" % (pattern,location))
  location = core.sandbox.is_path_safe(location)
  if location is False:
    return "error: location blocked by sandbox"
  result = subprocess.run(
    ["rg","--color=never" ,"-e",pattern,"--",location],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    check=False
  )
  if result.returncode == 0:
    return "ok, results:\n" + result.stdout
  elif result.returncode == 1:
    return "ok: no matches found"
  else:
    return f"error: ripgrep failed: {result.stderr.strip()}"

def file_mkdir(dirname: Annotated[str, "Name of directory to create"]):
  realpath = expanduser(normpath(dirname))
  realpath = core.sandbox.is_path_safe(realpath)
  if realpath is False:
    return "error: dirname blocked by sandbox"
  if os.path.isdir(realpath):
    return "error: directory already exists"
  elif os.path.isfile(realpath):
    return "error: file already exists"
  os.mkdir(realpath)
  return "ok"

def file_read(filename: Annotated[str, "Name of the file to read"], start: Annotated[int, "Location to start reading from"], bytes: Annotated[int, "Number of bytes to read. Use -1 to read the whole file."]):
  global MAX_DATA
  print("info: file_read(%s,%d,%d) called" % (filename,start,bytes))
  filename = core.sandbox.is_path_safe(filename)
  if filename is False:
    return "error: filename blocked by sandbox"
  else:
    if os.path.isfile(filename) is False:
      print("warn: os.path.isfile('%s') is False" % filename)
      return "cannot open file (this is not a file, maybe a directory?)"
    with open(filename,"r",encoding="utf-8",errors="replace") as f:
      f.seek(0,2)
      total_bytes = f.tell()
      f.seek(start)
      if bytes == -1:
        print("info: file_read asked to get -1 bytes, reading all")
        data = f.read()
      else:
        data = f.read(bytes)
    if len(data) >= MAX_DATA:
      return "error: trying to return %d bytes, can only read %d at once" % (len(data),MAX_DATA)
    else:
      status_str = "ok, read %d out of %d bytes, %d remaining\n" % (len(data),total_bytes - start,total_bytes - start - len(data))
      return status_str + data

def file_write(filename: Annotated[str, "Name of the file to write to"], data: Annotated[str, "Data to write"], append: Annotated[bool, "True to append to end of file, False to write over existing data"]):
  global FILE_WRITE_PERMISSION
  print("info: file_write(%s,len(data)=%d) called" % (filename, len(data)))
  realpath = expanduser(normpath(filename))
  realpath = core.sandbox.is_path_safe(realpath)
  if realpath is False:
    return "error: filename blocked by sandbox"
  mode = "w"
  if append is True:
    mode = "a"
  with open(realpath,mode) as f:
    f.write(data)
  return "ok"

def file_glob(pattern: Annotated[str, "Pattern to glob"]):
  print("info: file_glob(%s) called" % pattern)
  pattern = core.sandbox.is_path_safe(pattern)
  if pattern is False:
    return "error: pattern blocked by sandbox"
  data = glob.glob(pattern)
  if len(data) == 0:
    return "0 files found"
  else:
    return ",".join(glob.glob(pattern))

ANSI_ESCAPE_RE = re.compile(r"\x1B\x5B[0-9;]+m")
def strip_terminal_colors(text: str) -> str:
  return ANSI_ESCAPE_RE.sub('', text)

PROCESS_LOCK = None
PROCESS_RD_QUEUE = None
PROCESS_RD_THREAD = None
PROCESS_RD_STOP = False

# courtesy of gpt-4o
# neat trick!
def async_reader(pipe, q):
  global PROCESS_RD_QUEUE, PROCESS_RD_STOP
  for line in iter(pipe.readline, ''):
    if PROCESS_RD_STOP is True:
      return
    PROCESS_RD_QUEUE.put(line)

def shell_exec(command: Annotated[str, "The command to run"]):
  if vm_sshargs() is None and risk_accept() is False:
    print("fatal: you must specify vm_sshargs() to use shell_exec, or I_ACCEPT_THE_RISK to run locally")
    sys.exit(-1)
  if cmdfw(command) is False:
    return fwreject()
  if risk_accept() is True:
    print("warn: I_ACCEPT_THE_RISK detected, running shell_exec('%s') locally" % command)
    try:
      result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    except subprocess.CalledProcessError as e:
      return "process returned a non-zero status"
    return strip_terminal_colors(result.stdout)
  else:
    if vm_sshargs().startswith("ssh ") is False:
      print("fatal: don't run local commands from ai you fucking retard")
      sys.exit(-1)
    command = command.replace("'", "\\'")
    command = command.replace("*", "\\*")
    new_c = vm_sshargs() + " '" + command + "'"
    print("info: shell_exec('%s') called" % new_c)
    try:
      result = subprocess.run(new_c, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,errors="replace")
    except subprocess.CalledProcessError as e:
      return "process returned a non-zero status"
    return strip_terminal_colors(result.stdout)

def shell_interactive_start(command: Annotated[str, "The command to run"]):
  global PROCESS_LOCK, PROCESS_RD_QUEUE, PROCESS_RD_THREAD
  if PROCESS_LOCK is not None:
    print("warn: shell_interactive_start called with PROCESS_LOCK on")
    return "error: you can only have one interactive process at a time"
  if cmdfw(command) is False:
    return fwreject()
  if risk_accept() is True:
    print("warn: shell_interactive_start('%s') called, locking pretend mutex, running locally" % command)
    PROCESS_LOCK = subprocess.Popen(
      command.split(),
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      text=True,
      errors="replace"
    )
  else:
    if vm_sshargs().startswith("ssh ") is False:
      print("fatal: don't run local commands from ai you fucking retard")
      sys.exit(-1)
    print("info: shell_interactive_start('%s') called, locking pretend mutex" % command)
    PROCESS_LOCK = subprocess.Popen(
      vm_sshargs().split() + [command],
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      text=True,
      errors="replace"
    )
    
  print("info: starting async read queue")
  PROCESS_RD_QUEUE = queue.Queue()
  PROCESS_RD_THREAD = threading.Thread(
    target=async_reader,
    args=(PROCESS_LOCK.stdout, PROCESS_RD_QUEUE),
    daemon=True
  )
  PROCESS_RD_THREAD.start()
  return "ok"

def shell_interactive_read():
  global PROCESS_LOCK, PROCESS_RD_QUEUE,PROCESS_RD_THREAD
  if PROCESS_LOCK is None:
    print("warn: shell_interactive_read called without PROCESS_LOCK")
    return "error: you have not started an interactive process"
  out = ""
  time.sleep(2.0)
  while True:
    try:
      line = PROCESS_RD_QUEUE.get(timeout=2)
      out += line
    except queue.Empty:
      break
  if len(out) == 0:
    print("info: shell_interactive_read returns nothing")
    return "got no output"
  else:
    new_out = strip_terminal_colors(out)
    print("info: shell_interactive_read returned %d bytes (%d stripped)" % (len(out),len(new_out)))
    return "got output:\n %s" % new_out

def shell_interactive_write(data: Annotated[str, "The data to write"]):
  global PROCESS_LOCK, PROCESS_RD_QUEUE,PROCESS_RD_THREAD
  if PROCESS_LOCK is None:
    print("warn: shell_interactive_write called without PROCESS_LOCK")
    return "error: you have not started an interactive process"
  print("info: shell_interactive_write('%s') called" % data.rstrip())
  try:
    PROCESS_LOCK.stdin.write(data.rstrip() + "\n")
    PROCESS_LOCK.stdin.flush()
  except BrokenPipeError as e:
    print("warn: process died, returning")
    return "failed, process died, unable to read"
  return "ok"

def shell_interactive_kill():
  global PROCESS_LOCK, PROCESS_RD_QUEUE, PROCESS_RD_THREAD, PROCESS_RD_STOP
  print("info: shell_interactive_kill() invoked")
  PROCESS_LOCK.terminate()
  PROCESS_LOCK = None
  print("info: pseudo-lock cleared")
  PROCESS_RD_QUEUE = None
  PROCESS_RD_STOP = True
  # PROCESS_RD_THREAD.stop()
  PROCESS_RD_THREAD.join()
  PROCESS_RD_STOP = False
  print("info: reader thread terminated and joined")
  return "ok, process killed"

if __name__ == "__main__":
  print("This file shouldn't be called directly")
  sys.exit(0)
