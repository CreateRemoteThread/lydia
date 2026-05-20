# Lydia - Slashem

### Problem

While typical command-line utilities can be interacted with using line buffered input, this does not work for more important applications such as Slash'EM. To work around this, we use the 'pyte' library to emulate a terminal, and provide 4 interfaces to the LLM:

```
- term_start
- term_interact
- term_screen_scrape
- term_kill
```

Some of the initial challenges are:

```
- Aggressively exiting slashem during testing creates wierd conditions, some of which have no search results (e.g. "Too many hacks running now"). 
  - Check for lockfiles in /opt/homebrew/Cellar/slashem/<version>/slashem
  - Check for orphaned processes ("slashem 4")
  - Watch for perm_lock problems: delete *only* perm_lock. If you delete perm, replace it with an empty file.
- The LLM has no idea how to actually play, sending inputs like "left" and "l" when trying to go left. Write a prompt for what to do.
- The context required by screenshots is relatively large. We need to aggressively prune screen scrapes (MEMORY_DECAY=3?), or foot the bill.
```
