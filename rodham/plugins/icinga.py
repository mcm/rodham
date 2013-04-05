import re
import socket
import time

def format_icinga_command(command):
    now = int(time.time())
    return "[%lu] %s\n" % (now, command)

class IcingaPlugin(object):
    def __init__(self, conf, *args, **kwargs):
        self.hostname = conf["server"]
        self.port = int(conf.get("port", 5668))
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.hostname, self.port))

    def proc(self, M):
        m = re.match("^!icinga", M["body"], flags=re.I)
        if not m:
            return

        if M["type"] == "groupchat":
            sender = M.get_from().resource
        else:
            sender = M.get_from().user
        if sender == "mcbastard":
            sender = "mcmaster"

        def ack_host(host, comment, silent = False):
            cmd = format_icinga_command("ACKNOWLEDGE_HOST_PROBLEM;%s;2;%s;0;%s;%s" % (host, int(not silent), sender, comment))
            self.client.sendall(cmd)

        def ack_service(host, service, comment, silent = False):
            cmd = format_icinga_command("ACKNOWLEDGE_SVC_PROBLEM;%s;%s;2;%s;0;%s;%s" % (host, service, int(not silent), sender, comment))
            self.client.sendall(cmd)

        def recheck_host(host):
            cmd = format_icinga_command("SCHEDULE_HOST_CHECK;%s;%s" % (host, int(time.time())))
            M.reply(cmd).send()
            self.client.sendall(cmd)

        def recheck_service(host, service):
            cmd = format_icinga_command("SCHEDULE_SVC_CHECK;%s;%s;%s" % (host, service, int(time.time())))
            M.reply(cmd).send()
            self.client.sendall(cmd)

        m = re.match("^!icinga (ack|silentack) ([^\s]+)(?: ([^\s]+))? (HD#\d+)$", M["body"], flags=re.I)
        if m:
            (action, host, service, comment) = m.groups()
            silent = (action == "silentack")
            if service is None:
                ack_host(host, comment, silent)
            else:
                ack_service(host, service, comment, silent)
            return

        m = re.match("^!icinga recheck ([^\s]+)(?: ([^\s]+))?", M["body"], flags=re.I)
        if m:
            (host, service) = m.groups()
            if service is None:
                recheck_host(host)
            else:
                recheck_service(host, service)
            return

        #m = re.match("^!icinga (ack) (?:\[URGENT\] )?Host ([^\s]+) is DOWN", M["body"], flags=re.I)

    def help(self, M):
        M.reply("Loaded").send()
