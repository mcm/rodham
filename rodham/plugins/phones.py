import asterisk.manager
import copy
import re
import threading
import uuid


class PhonePlugin(object):
    def __init__(self, conf, *args, **kwargs):
        self.ami = asterisk.manager.Manager()
        self.ami.connect(conf["host"])
        self.ami.login(conf["username"], conf["password"])

        if "bot" in kwargs:
            self.bot = kwargs.pop("bot")

        self.help_file = conf.get("help_file", "/opt/virtual_envs/rodham/conf/phone_help.txt")

    def proc(self, M):
        m = re.match("!phones (list|open|close|oncall|fun|call)", M["body"], flags=re.I)
        if not m:
            return

        if M["type"] == "groupchat":
            sender = M.get_from().resource
        else:
            sender = M.get_from().user
        if sender == "mcbastard":
            sender = "mcmaster"

        cmd = m.groups()[0].lower()
        if cmd == "open" or cmd == "close":
            m = re.match("!phones (open|close) (\S+)", M["body"], flags=re.I)
            if not m:
                return

            line = m.groups()[1]
            val = "open" if cmd == "open" else "closed"
            cdict = {"Action": "DBPut", "Family": "hurricanedefense", "Key": line, "Val": val}
            response = self.ami.send_action(cdict)
            if response.get_header("Response") == "Success":
                M.reply("Success").send()
        elif cmd == "oncall":
            m = re.match("!phones oncall(?: (\w+))?(?:$| ([\d:]+))", M["body"], flags=re.I)
            if not m:
                return

            line = m.groups()[0]
            if line is None:
                line = "tech"
            rotation = m.groups()[1]
            if rotation is None:
                # Get rotation
                actionid = str(uuid.uuid4())
                finished = threading.Event()
                def handle_response(event, manager, *args, **kwargs):
                    if event.get_header("ActionID") != actionid:
                        return
                    M.reply(event.get_header("Val")).send()
                    finished.set()
                self.ami.register_event("DBGetResponse", handle_response)
                cdict = {"Action": "DBGet", "Family": "oncall", "Key": line, "ActionID": actionid}
                self.ami.send_action(cdict)

                finished.wait(10)
                self.ami.unregister_event("DBGetResponse", handle_response)
            else:
                # Set rotation
                cdict = {"Action": "DBPut", "Family": "oncall", "Key": line, "Val": rotation}
                response = self.ami.send_action(cdict)
                if response.get_header("Response") == "Success":
                    M.reply("Success").send()
        elif cmd == "list":
            channels = dict()
            actionid = str(uuid.uuid4())
            finished = threading.Event()
            def handle_response(event, manager, *args, **kwargs):
                if event.get_header("ActionID") != actionid:
                    return
                if not re.match("SIP/\d+", event.get_header("Channel")):
                    return
                name = self.bot.get_plugin("ldap").get_user_by_extension(event.get_header("CallerIDnum"))
                if name is None:
                    copy.copy(M).reply(event.get_header("CallerIDnum")).send()
                else:
                    copy.copy(M).reply(name).send()
            def handle_complete(event, manager, *args, **kwargs):
                finished.set()
            self.ami.register_event("CoreShowChannel", handle_response)
            self.ami.register_event("CoreShowChannelsComplete", handle_complete)
            cdict = {"Action": "CoreShowChannels", "ActionID": actionid}
            self.ami.send_action(cdict)
            finished.wait(15)
            self.ami.unregister_event("CoreShowChannelsComplete", handle_complete)
            self.ami.unregister_event("CoreShowChannel", handle_response)
        elif cmd == "call":
            m = re.match("!phones call ([a-zA-Z '-]{3,}?)(?:$| (mobile|office|home)$)", M["body"], flags=re.I)
            if not m:
                return

            ldap_plugin = self.bot.get_plugin("ldap")

            (who, where) = m.groups()
            try:
                (name, number) = ldap_plugin.get_someones_number(who, where)
            except TypeError:
                name = number = None

            if number is None:
                M.reply("That request does not compute - do better").send()
                return

            number = re.sub("[^\d]", "", number)

            ext = ldap_plugin.get_extension_by_user(sender)
            if ext is None:
                M.reply("%s: Sorry I can't find YOU" % sender).send()
                return

            M.reply("Calling %s and connecting to %s (%s)" % (sender, name, where)).send()
            self.ami.originate("LOCAL/%s@devices" % ext, number, context="outgoing-confirm", priority=1, caller_id="%s <%s>" % (name, number))
        elif cmd == "fun":
            with open(self.help_file, "r") as f:
                rules = f.read()

            M.reply(rules.strip()).send()

    def help(self, M):
        pass
