# Setup configs to monkey patch a lower memory mode in pyba.
# https://stackoverflow.com/questions/79094715/disable-hardware-influence-on-playwright-tests-using-chromium-driver

LAUNCH_ARGS = [
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
    "--disable-features=Translate,BackForwardCache",
    "--disable-lcd-text",
]

CONTEXT_KWARGS = {
    "device_scale_factor": 1,
}
