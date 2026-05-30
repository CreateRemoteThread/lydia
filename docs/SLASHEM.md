# Lydia - Slashem

### Problem

Playing roguelike games like "slashem" is an interesting challenge for an LLMs, as this is far too complex for a single LLM prompt interaction to solve. Our approach involves chaining multiple agents and fixed tool calls via the Hatchery system.

![screenshot-1](docs/img/firstroom.png)

### Further reading

- [It's 2026. Can LLM's Play Nethack Yet?](https://kenforthewin.github.io/blog/posts/nethack-agent/)
- [NetPlay agent](https://github.com/CommanderCero/NetPlay)
- [Playing NetHack with Language Models - Dominik Jeurissen (YT)](https://www.youtube.com/watch?v=8ohVsTuCeVo)

### Challenges

Some of the initial challenges are:

```
- Aggressively exiting slashem during testing creates wierd conditions, some of which have no search results (e.g. "Too many hacks running now"). 
  - Check for lockfiles in /opt/homebrew/Cellar/slashem/<version>/slashem
  - Check for orphaned processes ("slashem 4")
  - Watch for perm_lock problems: delete *only* perm_lock. If you delete perm, replace it with an empty file.
- The LLM has no idea how to actually play, sending inputs like "left" and "l" when trying to go left. Write a prompt for what to do.
  - The LLM has no idea what things on the screen mean, or how to move to relative positions (e.g. "move to the { symbol" may go somewhere unexpected).
- The context required by screenshots is relatively large. We need to aggressively prune screen scrapes (MEMORY_DECAY=3?), or foot the bill.
```
