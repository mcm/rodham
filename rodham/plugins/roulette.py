import random

class RoulettePlugin(object):
    def __init__(self, *args, **kwargs):
        self.bot = kwargs["bot"]
        self.debug = False
        self.load()

    def load(self):
        self.barrel = [ 0 for x in range(0, 6) ]
        self.barrel[random.randint(1, 6) - 1] = 1

    def proc(self, M):
        if M["type"] != "groupchat":
            return

        if M["body"][:9].lower() != "!roulette":
            return

        if M["body"].lower() == "!roulette debug":
            self.debug = True
            return

        room = M["mucroom"].split("@")[0]
        nick = M["mucnick"]

        shot = random.randint(1, 6) - 1
        while self.barrel[shot] == -1:
            shot = random.randint(1, 6) - 1

#        if self.debug:
#            self.bot.debug_message(" ".join(map(str, self.barrel)))
#            self.bot.debug_message(str(shot + 1))

        if self.barrel[shot] == 1:
            # Kick the sender
            try:
                self.bot.kick(room, nick, reason="You lose!")
            except:
                M.reply("*BANG*").send()
            self.load()
        else:
            self.barrel[shot] = -1
            M.reply("*click*").send()

    def help(self, M):
        M.reply("How about a nice game of Russian Roulette?").send()
