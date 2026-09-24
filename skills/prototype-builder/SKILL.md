---
name: prototype-builder
description: Build stateful local UI references for Roach Loop and register them as provenance-bearing external evidence.
---
# Roach Loop Prototype Builder

Build a self-contained, clickable prototype under `.roach/prototype/` or another project-controlled path. It should cover the same states the implementation will be reviewed against and require no network to render.

Follow `design.md` / `ARCHITECTURE.md`. Make every control functional enough to demonstrate the intended interaction.

Register the finished reference:
```bash
python3 scripts/roach.py external add \
  --id PROTO-001 --kind ui-reference --checkpoint <CP> \
  --path .roach/prototype/<name>.html --source approved-prototype
```

When intent changes, update the prototype first, record a Roach redirect, supersede affected checkpoints, and re-plan. Never silently replace an accepted reference.
