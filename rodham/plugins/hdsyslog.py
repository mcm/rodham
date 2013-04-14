import copy
import re
import xmlrpclib

class HdsyslogPlugin(object):
    def __init__(self, conf, *args, **kwargs):
        port = int(conf.get("port", "9097"))
        self.hdsyslog = xmlrpclib.ServerProxy("http://%s:%d" % (conf["host"], port), allow_none=True)

    def proc(self, M):
        m = re.match("!hdsyslogq? (count|flush|list)(?:$| (.+)$)", M["body"], flags=re.I)
        if not m:
            return

        cmd = m.groups()[0]
        fe = m.groups()[1]
        if fe:
            if fe[0] == "'" or fe[0] == '"':
                fe = fe[1:-1]
        else:
            fe = ""

        if cmd == "count":
            M.reply(str(self.hdsyslog.count(fe))).send()
        elif cmd == "flush":
            if fe == "":
                M.reply("I'm sorry Dave, but I'm afraid I can't do that").send()
            else:
                try:
                    self.hdsyslog.flush(fe)
                except:
                    import traceback
                    M.reply(traceback.format_exc()).send()
                else:
                    M.reply("Success").send()
        elif cmd == "list":
            for msg in self.hdsyslog.list(fe):
                copy.copy(M).reply('%5d: %s' % (msg['queueid'], msg['raw'])).send()
