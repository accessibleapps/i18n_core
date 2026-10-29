Goal: Resolve implicit translation callers in sourceless frozen applications.
State: Actual bundled audio_player.gui calls install_module_translation implicitly; instrumented inspect.getmodule returned None while frame.f_globals named audio_player.gui. This prevents that module's translation registration.
Decisions and why: Resolve the module directly from the caller frame's __name__ and sys.modules instead of matching source filenames through inspect.getmodule. This is about two source lines and updating the existing caller-resolution test.
Next step: Publish, observe existing CI, rebuild QCast with the exact shared owner branch, verify registration and absence of the unresolved-caller warning.
