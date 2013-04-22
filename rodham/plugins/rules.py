import os
import re

class RulesPlugin(object):
    def __init__(self, *args, **kwargs):
        self.conf = kwargs["conf"]

    def proc(self, M):
        m = re.match("^!rules(?: (\S+))?", M["body"], flags=re.I)
        if not m:
            return

        which = m.groups()[0]
        if which is None:
            which = self.conf.get("default", "roddy")

        fn = self.conf.get(which, False)
        if not fn or not os.path.exists(fn):
            return

        with open(fn, "r") as f:
            rules = f.read()

        M.reply(rules.strip()).send()
