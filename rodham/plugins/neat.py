import re

class NeatPlugin(object):
    def proc(self, M):
        if M["type"] == "groupchat":
            sender = M.get_from().resource
        else:
            sender = M.get_from().user
        if re.search(r"!neat", M["body"]):
            M.reply("Wow %s that IS neat!" % sender).send()

    def help(self, M):
        M.reply("!neat wow Tom way to insult billford || blah blah blah !neat").send()
