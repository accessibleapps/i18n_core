# Repair the default-branch gettext baseline

## Goal

Repair the actual failures on fresh master before updating feature PR #3. Keep real GNU gettext compilation, existing translation assertions, and the current API/locale behavior. No publication, rebase, merge, release, GUI work, or translation-policy changes in this local slice.

## State

- Verified owner: accessibleapps/i18n_core, origin git@github.com:accessibleapps/i18n_core.git. Authenticated API master and freshly fetched origin/master both equal 8aad02dacbaae24a9878f3c58e28e4dd9ae038a0.
- Isolated branch repair/task6-i18n-baseline. Existing feature PR #3 remains DRAFT at 51aa8a5e3ba5a92d69743b4582ec6ff1d8ca68a4; its fixture is identical to master.
- Canonical master retains dirty gui.py, registry.py, reset_locale.py and untracked CLAUDE.md/aider files. Existing feature worktree and branch are untouched.
- Read global guidance, canonical CLAUDE.md, original worker report, and repair prompts. Current task explicitly authorizes the narrow baseline repair and focused/full local verification.

## Decisions and why

- Smallest coherent repair: escape eight PO header newlines, expose three existing dynamic translation implementations through the public names documented by README, and perform the missing translation call in the availability test. No new abstraction, dependency, support change, or test skip.
- Broken fixture: generated PO bytes had CRLF inside quoted fields (first field ends with hex 74 65 73 74 0d 0a 22), causing GNU msgfmt 0.22.5 to report end-of-line within string and 16 fatal errors.
- Product defect exposed after compiling valid catalogs: all four tests raised ImportError for the README's documented `from i18n_core import _`. Existing _dynamic_gettext/_dynamic_lazy_gettext/_dynamic_ngettext implement the behavior; aliases preserve those implementations.
- Broken test setup exposed after restoring exports: availability returned only en_US because its comment promised an implicit-registration call but the test only imported foo. Calling foo.get_text() executes the existing inference path; both existing locale assertions remain.
- Coordinator authorized the missing hosted gate: one Ubuntu/Python 3.13 job runs the full existing suite and package build on PRs and master pushes. Install GNU gettext and require `msgfmt --version` before pytest so the module cannot silently skip for an absent compiler. No release workflow changes.
- CI uses uv 0.8.8, matching local verification; no tracked lock exists and the repository ignores uv.lock, so retain the existing `uv run pytest` resolution contract rather than invent a committed lock. Existing pytest/dev tools are already declared; no dependency or support-floor change.
- Official GitHub tag APIs verified actions/checkout v7.0.1 = 3d3c42e5aac5ba805825da76410c181273ba90b1 and astral-sh/setup-uv v9.0.0 = c771a70e6277c0a99b617c7a806ffedaca235ff9. Add github-actions to existing Dependabot configuration to maintain pins. Read-only contents permission, nonpersisted checkout credentials, disabled uv cache, ten-minute timeout, ref-specific supersession cancellation.

## Verification

- Fresh master `uv run pytest -v`: 4 failed, 5 passed in 1.65s. All four failures occur in unchanged build_mo at real msgfmt compilation, before assertions.
- Header-only repair `uv run pytest tests/test_e2e_msgfmt.py -v --tb=short`: 4 failed in 2.52s, now ImportErrors for `_`.
- Header plus aliases, same focused command: 1 failed, 3 passed in 1.30s. Remaining assertion: de_DE absent from ['en_US'].
- Complete repair, same focused command: 4 passed in 1.21s.
- Complete repair `uv run pytest -v --tb=short`: 9 passed in 1.63s; no skips.
- `uv build`: exit 0, built source distribution and wheel for i18n_core 2.0.1. No publishing command executed.
- Windows CPython 3.13.15, pytest 9.1.1, GNU gettext 0.22.5. Full suite exercises its existing locale calls; no separate GUI/native service journey was performed.
- Manifest unchanged. uv.lock was absent and untracked initially, generated locally, remains ignored, SHA256 63723D3F8FC99256FC72FA5FEAE83D4A34AED1E9F7C42FC89451194908BABF44. No tracked lock diff.
- Complete source/test diff inspected, git diff --check passes. No credentials/private data in authored code. Canonical status and feature PR head rechecked unchanged.
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12 -no-color .github/workflows/ci.yml`: exit 0, no diagnostics.
- `uvx zizmor==1.31.1 --offline .github/workflows/ci.yml`: exit 0, no findings. Only the authored workflow audited; old publishing workflow remains unchanged.

## Surprises

The malformed headers hid two independent baseline issues. The documented public import is a production defect; the missing implicit-registration call is test setup, not a reason to weaken the availability assertion.

## Next step

Local repair commit b6d5c46f3cab6fdbcef1c1d53f499211e437bb7b contains the two repaired files and this note. The following CI commit contains the authorized CI/Dependabot additions and this updated living note. Local work is complete and the worktree is clean. Coordinator reviews the complete exact patch before authorizing publication. Actual Claude review and hosted green checks are still pending on the final proposed head. Do not rewrite feature #3 until the coordinator authorizes it after prerequisite landing.
