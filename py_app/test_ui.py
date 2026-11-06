"""Manual check: start the trainer in a terminal and pick a game. Run it from py_app/."""

import sys


def main():
    import pexpect

    child = pexpect.spawn(sys.executable, ['trainer.py'], encoding='utf-8')
    child.logfile = sys.stdout

    child.expect('Choose problems or mode:')
    child.sendline('p')

    child.interact()


if __name__ == '__main__':
    main()
