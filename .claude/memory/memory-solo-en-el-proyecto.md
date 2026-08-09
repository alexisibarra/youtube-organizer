---
name: memory-solo-en-el-proyecto
description: Toda la memoria persistente de este proyecto vive en .claude/memory/ dentro del repo; nunca en ~/.claude.
metadata:
  type: feedback
---

Regla dada por Alexis el 2026-08-09: toda la memoria persistente de este proyecto
(decisiones, contexto de arquitectura, convenciones, notas) debe vivir **exclusivamente**
dentro del directorio del proyecto — en `.claude/memory/` o en `CLAUDE.md` / `Docs/` /
`_bmad-output/`. Nunca en `~/.claude/CLAUDE.md` ni en el directorio de memoria por-proyecto
del harness (`~/.claude/projects/-Users-alexis-Proyectos-Yo-youtube-organizer/memory/`),
que queda fuera del repo.

**Why:** el contexto del proyecto debe viajar con el repo y ser visible/auditable por el
equipo y por otros agentes; la memoria global del harness es invisible en git y no se
comparte al clonar.

**How to apply:** escribe memorias nuevas en `.claude/memory/<slug>.md` con el frontmatter
habitual y añade la línea de índice en `.claude/memory/MEMORY.md`. Antes de escribir
cualquier archivo de memoria, comprueba que la ruta esté bajo
`/Users/alexis/Proyectos/Yo/youtube-organizer`; si no lo está, detente y avisa
explícitamente al usuario en lugar de escribir.
