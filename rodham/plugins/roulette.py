import random

class RoulettePlugin(object):
    def __init__(self, *args, **kwargs):
        self.bot = kwargs["bot"]

    def proc(self, M):
        if M["type"] != "groupchat":
            return

        if M["body"] != "!roulette":
            return

        room = M["mucroom"].split("@")[0]
        nick = M["mucnick"]

        # Load the revolver
        barrel = random.randint(1, 6)

        # Fire!
        shot = random.randint(1, 6)

        if shot == barrel:
            # Kick the sender
            self.bot.kick(room, nick, reason="You lose!")
