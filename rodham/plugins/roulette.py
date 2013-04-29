import random

class RoulettePlugin(object):
    def __init__(self, *args, **kwargs):
        self.bot = kwargs["bot"]
        self.barrel = random.randint(1, 6)

    def proc(self, M):
        if M["type"] != "groupchat":
            return

        if M["body"] != "!roulette":
            return

        room = M["mucroom"].split("@")[0]
        nick = M["mucnick"]

        shot = random.randint(1, 6)

        if shot == self.barrel:
            # Kick the sender
            self.bot.kick(room, nick, reason="You lose!")
            self.barrel = random.randint(1, 6)
        else:
            M.reply("*click*").send()

    def help(self, M):
        M.reply("How about a nice game of Russian Roulette?").send()
