# Setup configs to monkey patch a lower memory mode in pyba.
# This is based on the conversations at
# https://stackoverflow.com/questions/79094715/disable-hardware-influence-on-playwright-tests-using-chromium-driver
#
# Benchmarked on Amazon.com (headless, 1280x720):
#   No flags:         760 MB
#   These flags:      552 MB  (~27% reduction)

LAUNCH_ARGS = [
    # --- Background services ---
    "--disable-gpu",  # Disable GPU compositing (not needed for headless)
    "--disable-dev-shm-usage",  # Use /tmp instead of /dev/shm (avoids OOM in containers)
    "--disable-background-networking",  # Stop background network requests (updates, safe browsing)
    "--disable-background-timer-throttling",  # Don't throttle timers in background tabs
    "--disable-backgrounding-occluded-windows",  # Don't deprioritize hidden windows
    "--disable-renderer-backgrounding",  # Keep renderer active even when not focused
    "--disable-extensions",  # No browser extensions
    "--disable-sync",  # Disable Chrome profile sync
    "--disable-default-apps",  # Don't install default apps (Gmail, Drive, etc.)
    "--no-default-browser-check",  # Skip "set as default browser" prompt
    "--no-first-run",  # Skip first-run welcome page
    "--mute-audio",  # Mute all audio output
    "--metrics-recording-only",  # Disable metrics reporting, keep recording for internal use
    "--disable-lcd-text",  # Disable subpixel text rendering (saves rendering memory)
    "--disable-component-update",  # Don't download component updates at runtime
    # --- Process and rendering overhead ---
    "--single-process",  # Merge all Chromium processes into one (~100-150MB saved)
    "--js-flags=--max-old-space-size=256",  # Cap V8 JS heap at 256MB (default ~1.5GB)
    "--disable-site-isolation-trials",  # Disable per-origin renderer process isolation
    "--disable-features=IsolateOrigins,site-per-process,Translate,BackForwardCache",
    #   IsolateOrigins: Don't create separate processes per origin
    #   site-per-process: Same as above, different enforcement path
    #   Translate: Disable page translation feature
    #   BackForwardCache: Don't cache previous pages in RAM for back/forward navigation
    "--disable-accelerated-2d-canvas",  # Use software rendering for canvas (less memory)
    "--disable-shared-workers",  # Disable SharedWorker API (not needed for automation)
]

CONTEXT_KWARGS = {
    "device_scale_factor": 1,
}
