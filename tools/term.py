#!/usr/bin/env python3

import os
import pty
import select
import signal
import subprocess
import termios
import time
import fcntl
import struct

# this is a special case only for localhost
RISK_ACCEPT = os.getenv("I_ACCEPT_THE_RISK",default=None)
if RISK_ACCEPT is not None:
  if RISK_ACCEPT == "ISO27001":
    # already imported vmtool, this just prints twice.
    # print("warn: I_ACCEPT_THE_RISK set to ISO27001, running commands locally")
    RISK_ACCEPT = True
  else:
    RISK_ACCEPT = False

PROCESS_LOCK = None

CMD_FW = os.getenv("CMD_FW", default=None)
if CMD_FW is not None:
  CMD_FW = [a.strip() for a in CMD_FW.split(",")]

def cmdfw(command):
  global CMD_FW
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
    try:
      import pyte
    except:
      print("fatal: term requires pyte library")
      sys.exit(-1)
    self.screen = pyte.Screen(80,24)
    self.stream = pyte.ByteStream(self.screen)
    self.master_fd, self.slave_fd = pty.openpty()
    self._set_winsize(self.slave_fd,80,24)    
    self.proc = subprocess.Popen([command], stdin=self.slave_fd, stdout=self.slave_fd, stderr=self.slave_fd, preexec_fn=os.setsid,close_fds=True)
    print(self.proc)
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
    return self._read(0.2)

  def screen_scrape(self):
    self._read(0.2)
    print("\n".join(self.screen.display))
    return "\n".join(self.screen.display)

  def close(self):
    self.proc.kill()

from typing import Annotated

def term_start(command: Annotated[str, "The command to run"]):
  global PROCESS_LOCK, RISK_ACCEPT
  if PROCESS_LOCK is not None:
    print("warn: term_start called with PROCESS_LOCK on")
    return "info: you need to call term_kill before starting a new process"
  if cmdfw(command) is False:
    return fwreject()
  if RISK_ACCEPT is True:
    print("warn: term_start('%s') called, locking pretend mutex, running locally" % command)
    PROCESS_LOCK = ProcessPty(command)
    return "ok"
  else:
    print("fatal: term_start without I_ACCEPT_THE_RISK, not handled")
    sys.exit(-1) 

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
  PROCESS_LOCK.interact(data)
  return "ok"

def term_kill():
  global PROCESS_LOCK
  PROCESS_LOCK = None
  print("info: term_kill() called")
  return "ok"

# Example usage
if __name__ == "__main__":
  nh = ProcessPty("slashem")
  nh.interact(" ")
  nh.screen_scrape()
  nh.interact(" ")
  nh.screen_scrape()
  nh.close()
