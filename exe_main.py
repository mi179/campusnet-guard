"""Compatibility wrapper for the packaged interactive menu entry point."""

import sys

from cyber_lobster.menu import (
    main,
    run_setup_wizard,
    run_watch_loop,
    show_menu,
)

def entry_point() -> int:
    if len(sys.argv) > 1:
        from cyber_lobster.cli import main as cli_main
        return cli_main()

    return main()


if __name__ == "__main__":
    sys.exit(entry_point())
