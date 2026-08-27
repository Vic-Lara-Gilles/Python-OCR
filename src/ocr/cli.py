"""Console entry point that launches the Streamlit application."""

from __future__ import annotations

import sys
from pathlib import Path

APP_PATH = Path(__file__).with_name("app.py")


def main() -> int:
    """Run the Streamlit app, forwarding any extra command line arguments.

    Returns:
        The exit code produced by the Streamlit CLI.
    """
    from streamlit.web import cli as streamlit_cli

    sys.argv = ["streamlit", "run", str(APP_PATH), *sys.argv[1:]]
    return streamlit_cli.main()


if __name__ == "__main__":
    raise SystemExit(main())
