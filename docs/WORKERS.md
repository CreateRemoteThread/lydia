# Lydia - Workers

"Workers" are my attempt to implement a form of subagents, which are common to other AI client tools. This is implemented in two function calls:

- create_worker allows us to specify a prompt, and create a worker. there is no limit on how many, each worker inhereits (via copy.copy) the permissions and access of it's parent
- wait_worker waits for all workers and returns what they returned

A fundamental problem is that you cannot guarantee the "host thread" will gather all the workers, particularly if the host thread can simply do the task itself. An example of this problem is as follows:

```
lydia --workers -p "create two workers, to write sentences about guavas. wait for the result and display it"
tools: attempting to grab tool 'shell_exec'
tools: attempting to grab tool 'file_write'
tools: attempting to grab tool 'file_read'
tools: attempting to grab tool 'file_glob'
worker: prepping agent class
info: calling regular function 'create_worker'
worker: 'Write a sentence about the nutritional benefits of guavas.'
info: calling regular function 'create_worker'
worker: 'Write a sentence about where guavas are commonly grown.'
Guavas are commonly grown in tropical and subtropical regions around the world, including countries like India, Brazil, and Mexico.
```

Note that wait_worker was simply not called. Given the base nature of LLM interaction, we cannot solve this without "out-of-loop trickery" (i.e. prompting like a fucking clown, forcing the LLM to accept an extra turn), or simply leaving it.

A more robust way to use subagents is to use hatchery's node-as-tool mechanism - this deterministically executs all subagents, and can simply wait for the outcome.
