from __future__ import absolute_import

from . import bot
from . import config

import daemon
import optparse


def main():
    import logging

    op = optparse.OptionParser()
    op.add_option("-c", "--conffile", dest="conffile")
    op.add_option("-d", "--daemon", action="store_true", dest="daemon", default=False)
    op.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False)
    (options, args) = op.parse_args()
    options = vars(options)

    conf = config.get_config(**options)

    if conf["verbose"]:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

    if conf["daemon"]:
        daemon.DaemonContext().open()
    rodham = bot.Rodham(conf)
    try:
        rodham.run()
    except KeyboardInterrupt:
        import sys
        sys.exit()

if __name__ == "__main__":
    main()
