# Setup configs to monkey patch a lower memory mode in pyba.
# This is based on the conversations at
# https://stackoverflow.com/questions/79094715/disable-hardware-influence-on-playwright-tests-using-chromium-driver
#
# Benchmarked on Amazon.com (headless, 1280x720):
#   No flags:         760 MB
#   These flags:      552 MB  (~27% reduction)

LAUNCH_ARGS = [
    # Disable background services
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-extensions",
    "--disable-sync",
    "--disable-default-apps",
    "--no-default-browser-check",
    "--no-first-run",
    "--mute-audio",
    "--metrics-recording-only",
    "--disable-lcd-text",
    "--disable-component-update",
    # Reduce process and rendering overhead
    "--single-process",  # NOTE: This is a big one, but don't try this with concurrent sessions!
    "--js-flags=--max-old-space-size=256",
    "--disable-site-isolation-trials",
    "--disable-features=IsolateOrigins,site-per-process,Translate,BackForwardCache",
    "--disable-accelerated-2d-canvas",
    "--disable-shared-workers",
]

CONTEXT_KWARGS = {
    "device_scale_factor": 1,
}
