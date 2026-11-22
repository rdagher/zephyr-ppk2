# For coding agents

- `README.md` is the overview and the setup of the module. The interface
  (`marking.md`, `commands.md`), the limitations, the bench and the
  samples are described in `docs/`.
- `.claude/skills/ppk2-profile/SKILL.md` is the procedure for finding
  which code draws the current.
- `uvx ruff check scripts` and `uvx ruff format --check scripts` must
  pass. `just build-all` builds every sample; it needs the nRF Connect
  SDK toolchain.
- The captures behind the figures are on the branch `captures`, not on
  the module's branch. `just captures` puts them in `evidence/`, where
  git ignores them.
- Flashing and capturing use the hardware on the bench. Do not do
  either unless asked.
