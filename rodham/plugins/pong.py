class PongPlugin(object):
    wang = 0

    def proc(self, M):
        if M["body"] == "ping":
            M.reply("pong").send()
        elif M["body"] == "wang":
            self.wang += 1
            if self.wang > 3:
                self.wang = 1
                M.reply("http://goo.gl/MXrQ").send()
            else:
                M.reply("chung").send()
