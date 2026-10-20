# Restore locale when setup raises

## Goal

Keep reset_locale's current public API and normal restoration behavior while restoring after an exception from the managed body. Only i18n_core source/tests; no registry, GUI, catalogs, consumer pins, live locale changes or publication before coordinator review.

## State

- Worker 01a15b4c-c035-7355-a97b-abcada04c033; authenticated ctoth, exact origin git@github.com:accessibleapps/i18n_core.git.
- Current base master e64da21df7ecb2a41c57f14dd3cd418463c3c519 includes merged prerequisite #4. Feature #3 is OPEN/DRAFT at https://github.com/accessibleapps/i18n_core/pull/3; reviewed source/published head cd315b9f3db4da11f372eee4a8c315eba5226e43.
- Historical initial base was 8aad02dacbaae24a9878f3c58e28e4dd9ae038a0 with no open PR; the isolated modernize/task6-i18n_core worktree was created then. Rebase used --no-update-refs; separate remote/local archive refs preserve 51aa8a5e3ba5a92d69743b4582ec6ff1d8ca68a4.
- Canonical root C:/Users/Q/code/i18n_core has dirty gui.py, registry.py and reset_locale.py, plus untracked CLAUDE.md and aider artifacts. Preserve all of it. Canonical reset_locale diff is logger spacing only. Parent explicitly authorized this isolated finally fix after independently reading source/caller.
- Global and discovered repository guidance read. Topology i18n-core owns this reusable locale contract. Manifest is tracked; no tracked lock (uv.lock ignored). Babel>=2.15,<3.0 and platform_utils unchanged; Python 3.8 Pyright target unchanged.

## Decisions and why

- Historical defect at the initial base: gui.set_wx_locale uses reset_locale around wx.Locale setup (gui.py:20), but the contextmanager yielded then restored, so an exception skipped restoration.
- Smallest change: try/finally around existing yield/restoration, approximately eight changed production lines and two focused mocked-locale cases (~35 lines). Retain existing locale tuple normalization, logging and exception propagation. No speculative locale policy changes.
- Historical command authority: parent authorized the mocked regression and one full existing pytest collection when no tracked test command or PR CI existed; only tag publishing was tracked. Current prerequisite #4 adds PR/master test/build CI. Do not infer native wx/catalog/screen-reader proof from mocks.

## Surprises

- Existing full catalog tests depend on external msgfmt and explicitly skip their module if unavailable. Record actual outcome.
- Untracked canonical CLAUDE documents pytest, but did not substitute for prior tracked authority; parent settled the exact new task-specific authority.

## Historical verification before prerequisite #4

- `uv run pytest tests/test_reset_locale.py -v` before source fix: 1 failed, 1 passed. Failure is expected setlocale call count 1, actual 0 after injected RuntimeError; normal-path characterization passes.
- Same command after finally cleanup: 2 passed in 0.53s. Both locale methods are mocked; original body exception identity retained. No actual locale changes or wx initialization.
- Parent-authorized full `uv run pytest`: 4 failed, 7 passed in 1.76s. Four existing tests/test_e2e_msgfmt.py tests fail at build_mo:46 before translation code: installed msgfmt.EXE rejects generated PO header (end-of-line within string, 16 fatal errors). Exact fixture header is unchanged in base. Do not repair/skip/catalog-normalize it in this slice. Parent approved keeping the coherent fix despite this known full-suite failure.
- Windows CPython 3.13.15, pytest 9.1.1. Manifest has no requires-python, so uv warns it defaults its local resolution to >=3.13; no manifest/support target changed. New task-local uv.lock is ignored by existing .gitignore, SHA256 63723D3F8FC99256FC72FA5FEAE83D4A34AED1E9F7C42FC89451194908BABF44. No tracked lock existed or changed; manifest diff stays empty.
- No active commit hooks configured/installed. Final named patch inspection retains source CRLF and all unrelated canonical work.
- Tracked non-publishing `uv build`: exit 0, created dist/i18n_core-2.0.1.tar.gz and dist/i18n_core-2.0.1-py2.py3-none-any.whl. No publish/tag/workflow dispatch. Build proves package creation only.

## Next step

Current verification: hosted pull_request CI https://github.com/accessibleapps/i18n_core/actions/runs/39516546737 at cd315b9f3db4da11f372eee4a8c315eba5226e43 passed all 11 tests without skips, including real gettext and both locale regressions, and built the source distribution and wheel. The historical catalog failures above were repaired in merged prerequisite #4.

Actual Claude source review approved the try/finally and regressions but requested this note correction. Await coordinator review/publication of this note-only commit, then actual Claude final-head followup and hosted CI before the coordinator's exact-head merge decision. No local CI rerun or source/test/manifest/workflow change for this correction; canonical dirty work and bot #5 remain untouched.
