# Lydia - HTB

### Overview

An interesting benchmark of lydia's - and AI's - capabilities is dynamic testing, as this is a partial-information problem that is fundamentally difficult to solve with any kind of pre-training.

I am not sure of the best approach to tackle this problem, but I am convinced the solution is not a one-size-fits-all giga-harness / "afk automation" - and I'm hoping the limit is not "a guy (or girl!) with claude code". This beges the question - what approaches actually work here?

### Cap

[public writeup](https://medium.com/@alexmiminas/htb-cap-write-up-8cadf0f02bf8)

The path to the user flag can be broken down into a few broad steps:
- Nmap the target IP
- Browse the web app first
- Find an IDOR type vuln on /download, download a pcap with creds in it
- Extract credentials from the pcap for the user 'nathan'
- Log in to the FTP interface, then download user.txt

On this path, AI appears to stumble several times. Such as:
- Rabbit-holing down FTP first, and "giving up" (ending req_loop): I don't think there is a true fix for this, humans do this as well. We need a significant 
- Cannot interact with FTP: We can work around this either with 'curl' or term_ tools. Neither is a great solution.
- Misses IDOR id=0: This is a major problem. I don't think there is a solution for this at all. We can include prompting to "support" an IDOR skill, but this is just having more goes at the roulette table.
 
After 6 (more, including error fixes) attempts, lydia was able to [capture this flag](docs/logs/htb-6.log).

