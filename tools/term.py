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
    print("warn: I_ACCEPT_THE_RISK set to ISO27001, running commands locally")
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

# thanks chatgpt!
class ProcessPty:
  def __init__(self, cmd="slashem", cols=80, rows=24):
    try:
      import pyte
    except:
      print("fatal: term_ functions require pyte library")
      sys.exit(-1)

    self.cols = cols
    self.rows = rows

    # pyte virtual terminal
    self.screen = pyte.Screen(cols, rows)
    self.stream = pyte.Stream(self.screen)

    # Create PTY pair
    self.master_fd, self.slave_fd = pty.openpty()

    # Set terminal window size
    self._set_winsize(self.slave_fd, rows, cols)

    # Launch NetHack attached to slave PTY
    self.proc = subprocess.Popen(
      [cmd],
      stdin=self.slave_fd,
      stdout=self.slave_fd,
      stderr=self.slave_fd,
      preexec_fn=os.setsid,  # make subprocess session leader
      close_fds=True,
    )

    # Parent only needs master
    os.close(self.slave_fd)

  def _set_winsize(self, fd, rows, cols):
    """Set terminal window size."""
    winsize = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

  def read(self, timeout=0.2, max_bytes=65536):
    """
    Read available output from NetHack, feed it into pyte,
    and return raw decoded output.
    """
    output = b""
    end_time = time.time() + timeout

    while time.time() < end_time:
      r, _, _ = select.select([self.master_fd], [], [], 0.05)
      if self.master_fd in r:
        try:
          chunk = os.read(self.master_fd, 1024)
          if not chunk:
            break

          output += chunk

          # Update pyte terminal state
          self.stream.feed(chunk.decode(errors="replace"))

          if len(output) >= max_bytes:
            break

        except OSError:
          break

    return output.decode(errors="replace")

  def send(self, command):
    """Send keystrokes to NetHack."""
    if isinstance(command, str):
      command = command.encode()
    os.write(self.master_fd, command)

  def interact(self, command, timeout=0.2):
    """Send command and update screen state."""
    self.send(command)
    return self.read(timeout)

  def screen_scrape(self, structured=False):
    """
    Return the visible screen.

    structured=False -> multiline string
    structured=True -> list of rows
    """
    rows = [self.screen.display[y].rstrip() for y in range(self.rows)]

    if structured:
      return rows
    return "\n".join(rows)

  def scrape_regions(self):
    """
    NetHack-specific scrape helper.
    Returns top message line, map area, bottom status line.
    """
    rows = self.screen_scrape(structured=True)

    return {
      "message": rows[0] if rows else "",
      "map": rows[1:-2] if len(rows) > 3 else [],
      "status": rows[-1] if rows else "",
    }

  def cursor_position(self):
    """Return current cursor (row, col)."""
    return self.screen.cursor.y, self.screen.cursor.x

  def is_alive(self):
    """Check if NetHack is still running."""
    return self.proc.poll() is None

  def close(self):
    """Terminate NetHack process."""
    if self.is_alive():
      try:
        os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        self.proc.wait(timeout=2)
      except Exception:
        self.proc.kill()

    try:
      os.close(self.master_fd)
    except OSError:
      pass

def fwreject():
  global CMD_FW
  if CMD_FW is None:
    return "error: permission denied by user"
  else:
    return "error: permission denied by firewall. allowed commands: %s" % " ".join(CMD_FW)


from typing import Annotated

def term_interactive_start(command: Annotated[str, "The command to run"]):
  global PROCESS_LOCK, RISK_ACCEPT
  if PROCESS_LOCK is not None:
    print("warn: term_interactive_start called with PROCESS_LOCK on")
    return "info: you need to call term_interactive_kill before starting a new process"
  if cmdfw(command) is False:
    return fwreject()
  if RISK_ACCEPT is True:
    print("warn: term_interactive_start('%s') called, locking pretend mutex, running locally" % command)
    PROCESS_LOCK = ProcessPty(command)
    return "ok"
  else:
    print("fatal: term_interactive_start without I_ACCEPT_THE_RISK, not handled")
    sys.exit(-1) 

def term_interactive_read():
  global PROCESS_LOCK
  print("info: term_interactive_read() called")
  if PROCESS_LOCK is None:
    return "error: use term_interactive_start to start the process first"
  else:
    PROCESS_LOCK.read(1.0)
    return PROCESS_LOCK.screen_scrape()

def term_interactive_write(data: Annotated[str, "The data to send"]):
  global PROCESS_LOCK
  print("info: term_interactive_write('%s') called" % data)
  PROCESS_LOCK.interact(data)
  return "ok"
  # PROCESS_LOCK.read(1.0)
  # return PROCESS_LOCK.screen_scrape()

def term_interactive_kill():
  PROCESS_LOCK.close()
  PROCESS_LOCK = None
  return "ok"

# Example usage
if __name__ == "__main__":
  nh = ProcessPty()
  nh.read(1.0)

  print("=== Screen ===")
  print(nh.screen_scrape())

  # Dismiss intro
  nh.interact(" ")

  print("\n=== After Space ===")
  print(nh.screen_scrape())

  # NetHack-specific scrape
  info = nh.scrape_regions()
  print("\nMessage:", info["message"])
  print("Status:", info["status"])

  nh.close()
