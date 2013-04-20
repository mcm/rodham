import re

class NeatPlugin(object):
    def proc(self, M):
        sender = M.sender
        if re.search(r"!neat", M["body"]):
            M.reply("Wow %s that IS neat!" % sender).send()

    def help(self, M):
        M.reply("!neat wow Tom way to insult billford || blah blah blah !neat").send()
