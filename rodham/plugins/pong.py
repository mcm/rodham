class PongPlugin(object):
    def proc(self, M):
        if M["body"] == "ping":
            M.reply("pong").send()
