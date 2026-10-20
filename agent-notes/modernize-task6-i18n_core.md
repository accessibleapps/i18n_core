# Restore locale when setup raises

## Goal

Keep reset_locale's current public API and normal restoration behavior while restoring after an exception from the managed body. Only i18n_core source/tests; no registry, GUI, catalogs, consumer pins, live locale changes or publication before coordinator review.

## State

- Worker 01a15b4c-c035-7355-a97b-abcada04c033; authenticated ctoth, exact origin git@github.com:accessibleapps/i18n_core.git.
- Fresh default/base master 8aad02dacbaae24a9878f3c58e28e4dd9ae038a0, verified by API and fetch. No open PR. Requested destination was absent; direct isolated worktree on modernize/task6-i18n_core created there.
- Canonical root C:/Users/Q/code/i18n_core has dirty gui.py, registry.py and reset_locale.py, plus untracked CLAUDE.md and aider artifacts. Preserve all of it. Canonical reset_locale diff is logger spacing only. Parent explicitly authorized this isolated finally fix after independently reading source/caller.
- Global and discovered repository guidance read. Topology i18n-core owns this reusable locale contract. Manifest is tracked; no tracked lock (uv.lock ignored). Babel>=2.15,<3.0 and platform_utils unchanged; Python 3.8 Pyright target unchanged.

## Decisions and why

- Actual caller gui.set_wx_locale uses reset_locale around wx.Locale setup (gui.py:20). Existing contextmanager yields then restores; an exception skips the code after yield.
- Smallest change: try/finally around existing yield/restoration, approximately eight changed production lines and two focused mocked-locale cases (~35 lines). Retain existing locale tuple normalization, logging and exception propagation. No speculative locale policy changes.
- Parent authorized the new mocked regression and one full existing pytest collection as task-specific test authority. No previous tracked test command or PR CI exists; tracked tag release builds/publishes only. Collection comes from existing tests/test_install_module_translation.py and tests/test_e2e_msgfmt.py plus authored tests/test_reset_locale.py. Do not infer native wx/catalog/screen-reader proof from mocks.

## Surprises

- Existing full catalog tests depend on external msgfmt and explicitly skip their module if unavailable. Record actual outcome.
- Untracked canonical CLAUDE documents pytest, but did not substitute for prior tracked authority; parent settled the exact new task-specific authority.

## Verification

- `uv run pytest tests/test_reset_locale.py -v` before source fix: 1 failed, 1 passed. Failure is expected setlocale call count 1, actual 0 after injected RuntimeError; normal-path characterization passes.
- Same command after finally cleanup: 2 passed in 0.53s. Both locale methods are mocked; original body exception identity retained. No actual locale changes or wx initialization.
- Parent-authorized full `uv run pytest`: 4 failed, 7 passed in 1.76s. Four existing tests/test_e2e_msgfmt.py tests fail at build_mo:46 before translation code: installed msgfmt.EXE rejects generated PO header (end-of-line within string, 16 fatal errors). Exact fixture header is unchanged in base. Do not repair/skip/catalog-normalize it in this slice. Parent approved keeping the coherent fix despite this known full-suite failure.
- Windows CPython 3.13.15, pytest 9.1.1. Manifest has no requires-python, so uv warns it defaults its local resolution to >=3.13; no manifest/support target changed. New task-local uv.lock is ignored by existing .gitignore, SHA256 63723D3F8FC99256FC72FA5FEAE83D4A34AED1E9F7C42FC89451194908BABF44. No tracked lock existed or changed; manifest diff stays empty.
- No active commit hooks configured/installed. Final named patch inspection retains source CRLF and all unrelated canonical work.
- Tracked non-publishing `uv build`: exit 0, created dist/i18n_core-2.0.1.tar.gz and dist/i18n_core-2.0.1-py2.py3-none-any.whl. No publish/tag/workflow dispatch. Build proves package creation only.

## Next step

Local slice complete: production 7 insertions/5 deletions plus 31-line regression and this living note. Commit only reset_locale.py, tests/test_reset_locale.py and this note, then return exact commit/checks/PR text to coordinator. No push or PR until concrete review; no merge/release/live GUI setup.
