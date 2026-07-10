"""CLI: python -m docustudio validate <clean.txt> <help.txt> <visual.txt>"""
import sys
from .validate import validate

USAGE = __doc__


def main():
    args = sys.argv[1:]
    if len(args) == 4 and args[0] == "validate":
        _, errors, _ = validate(args[1], args[2], args[3])
        sys.exit(1 if errors else 0)
    print(USAGE)
    sys.exit(2)


if __name__ == "__main__":
    main()
