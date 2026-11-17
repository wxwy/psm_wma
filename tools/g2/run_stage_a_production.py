"""Thin entrypoint for the fixed-code Stage-A one-shot supervisor."""

from g2.offline.full_production import main

if __name__ == "__main__":
    raise SystemExit(main())
