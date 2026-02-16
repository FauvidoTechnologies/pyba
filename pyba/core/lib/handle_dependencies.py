import os
import re
import subprocess
import sys
from pathlib import Path


class PlaywrightDependencies:
    """
    We'll make use of this class if the user wants us to handle the dependencies. Usually, this
    shouldn't be the case because it requires only 2 commands to manage all playwright deps.
    """

    @staticmethod
    def _get_playwright_browsers_path() -> Path:
        """
        Determines the default or configured path where Playwright browsers are
        installed. An OS agnostic check for determining installed playwright browsers.

        Uses the following paths:
            windows: "AppData/Local/ms-playwright"
            macOS: "~/Library/Caches/ms-playwright"
            linux: ".cache/ms-playwright"

        Note: OSes like freebsd haven't been checked
        """
        env_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        if env_path:
            return Path(env_path).expanduser().resolve()

        if os.name == "nt":
            base = (
                Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
                / "ms-playwright"
            )
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Caches" / "ms-playwright"
        else:
            base = Path.home() / ".cache" / "ms-playwright"
        return base

    @staticmethod
    def _get_expected_browser_dirs() -> list[str]:
        """
        Runs 'playwright install --dry-run --json' to determine which browser
        directories should exist, based on the current Playwright version.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "--dry-run"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0 or not result.stdout.strip():
                return []

            data = result.stdout
            matches = re.findall(r"Install location:\s+(.+)", data)
            expected_dirs = [Path(path.strip()).name for path in matches if path.strip()]
            return expected_dirs
        except Exception as e:
            print(f"Error determining expected browser directories: {e}")
            return []

    @staticmethod
    def check_playwright_browsers_installed() -> bool:
        """
        Checks if all expected Playwright browsers are installed in the cache directory.
        """
        try:
            base_path = PlaywrightDependencies._get_playwright_browsers_path()
            expected_dirs = PlaywrightDependencies._get_expected_browser_dirs()

            if not expected_dirs:
                return False

            # Get the names of existing directories inside the Playwright cache path
            existing_dirs = {p.name for p in base_path.glob("*") if p.is_dir()}
            missing_dirs = [name for name in expected_dirs if name not in existing_dirs]

            return len(missing_dirs) == 0

        except Exception as e:
            print(f"An unexpected error occurred during browser check: {e}", file=sys.stderr)
            return False

    @staticmethod
    def install_playwright_browsers():
        """
        Install Playwright browsers automatically.
        """
        print("Installing Playwright browsers...")
        subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)

    @staticmethod
    def check_missing_dependencies():
        """
        Run a test to identify missing dependencies using `playwright install-deps --dry-run`.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install-deps", "--dry-run"],
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stdout.strip() + "\n" + result.stderr.strip()
            # Filter only the lines that mention missing libraries
            missing_lines = [
                line
                for line in output.splitlines()
                if "Missing" in line or line.strip().endswith(".so") or "║" in line
            ]
            if missing_lines:
                print("The following dependencies are missing: ")
                print("\n".join(missing_lines))
                print(
                    "Please install them manually using your package manager or run: playwright install-deps"
                )

            else:
                print("All playwright dependencies present")
        except FileNotFoundError:
            print("Could not run playwright. Is it installed in this environment?")
        except Exception as e:
            print(f"An error occurred during dependency check: {e}")

    @staticmethod
    def handle_dependencies():
        # Step 1: Check if browsers are installed
        if PlaywrightDependencies.check_playwright_browsers_installed():
            print("Playwright browsers are already installed")
        else:
            print("Playwright browsers not found.")
            choice = input("Do you want to install them automatically? (y/n): ").strip().lower()
            if choice == "y":
                try:
                    PlaywrightDependencies.install_playwright_browsers()
                    print("Installation complete.")
                except subprocess.CalledProcessError:
                    print("Browser installation failed. Check the output above for errors.")
            else:
                print("Please install browsers using: playwright install")
        # Step 2: Check missing system dependencies
        PlaywrightDependencies.check_missing_dependencies()


class HandleDependencies:
    playwright = PlaywrightDependencies
