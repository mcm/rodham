import SocketServer
import threading


class NagzillaServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


def NagzillaProtocolFactory(bot):
    class NagzillaProtocol(SocketServer.StreamRequestHandler):
        bot = None

        def handle(self):
            line = self.rfile.readline().strip()
            while line:
                self.handle_line(line)
                line = self.rfile.readline().strip()

        def handle_line(self, line):
            (style, target, msg) = line.split("^", 2)
            try:
                (msg, color) = msg.split("^", 1)
            except ValueError:
                color = None

            if style.lower() == "room":
                # MUC
                M = self.bot.make_muc_message(mto=target, mbody=msg)
            else:
                # DM
                M = self.bot.make_message(mto=target, mbody=msg)
            if color is not None:
                M["html"]["body"] = """<html xmlns="http://jabber.org/protocol/xhtml-im"><body xmlns="http://www.w3.org/1999/xhtml"><span style="color: %s">%s</span></body></html>""" % (color, msg)
            M.send()
            M["from"], M["to"] = M["to"], M["from"]
            self.bot.message_received(M)

    NagzillaProtocol.bot = bot
    return NagzillaProtocol


class NagzillaPlugin(object):
    def __init__(self, conf, bot, *args, **kwargs):
        self.conf = conf
        addr = self.conf["bind_address"]
        port = int(self.conf.get("bind_port", 49776))
        NagzillaProtocol = NagzillaProtocolFactory(bot)
        self.server = NagzillaServer((addr, port), NagzillaProtocol)

        def worker():
            self.server.serve_forever()
            self.server.socket.close()

        self.thread = threading.Thread(target=worker).start()

    def proc(self, M):
        pass

    def shutdown(self):
        self.server.shutdown()

    def __del__(self):
        self.shutdown()
