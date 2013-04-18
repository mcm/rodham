from . import plugins
from . import signals

import copy
import re
import sleekxmpp

from sleekxmpp.stanza.message import Message
from sleekxmpp.xmlstream import ElementBase
from sleekxmpp.xmlstream import register_stanza_plugin

class MediatedInvite(ElementBase):
    name = 'x'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = "password"
    is_extension = True
    interfaces = ("password",)
    sub_interfaces = ("password",)

class Rodham(sleekxmpp.ClientXMPP):
    def __init__(self, conf, *args, **kwargs):
        self.conf = conf
        kwargs["jid"] = conf["server"]["jid"]
        kwargs["password"] = conf["server"]["password"]
        super(Rodham, self).__init__(*args, **kwargs)

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message_received)

        self.register_plugin('xep_0045')
        #self.register_plugin('xep_0249')

        register_stanza_plugin(Message, MediatedInvite)

    @property
    def jid_resource(self):
        return self.conf["server"]["jid"].split("/")[-1]

    def run(self):
        if self.conf["server"].has_key("hostname"):
            port = int(conf["server"].get("port", 5222))
            self.connect((conf["server"]["hostname"], port))
        else:
            self.connect()
        self.process(block=True)

    def make_muc_message(self, *args, **kwargs):
        mto = kwargs.pop("mto")
        try:
            server = self.conf["rooms"][mto]["server"]
        except KeyError:
            server = "conference.chat.hurricanedefense.com"
        kwargs["mto"] = "%s@%s" % (mto, server)
        kwargs["mtype"] = "groupchat"
        return self.make_message(*args, **kwargs)

    def debug_message(self, message):
        for (room,roomconf) in self.conf["rooms"].items():
            if roomconf.get("debugging", False):
                self.make_muc_message(mto=room, mbody=message).send()

    def session_start(self, event):
        self.send_presence()
        self.get_roster()
        #print "connected"

        for (room, roomconf) in self.conf["rooms"].items():
            #print "Joining %s" % room
            if not roomconf.has_key("password"):
                roomconf["password"] = ""
            self.join_room(room, roomconf["server"], roomconf["password"])

        self.add_event_handler("groupchat_invite", self.groupchat_invite)

        self._plugin_manager = plugins.PluginManager(self.conf["plugins"], bot=self)

    def groupchat_invite(self, inv):
        (room, server) = str(inv["from"]).split("@")
        self.join_room(room, server, inv["password"])

    def join_room(self, room, server, password):
        if not room in self.conf["rooms"]:
            roomconf = {
                "password": password,
                "server": server,
                "nick": self.jid_resource
            }
            self.conf["rooms"][room] = roomconf
        else:
            roomconf = self.conf["rooms"][room]
        jid = "%s@%s" % (room, server)
        self.plugin["xep_0045"].joinMUC(jid, roomconf["nick"], password=password)
        self.add_event_handler("muc::%s::got_online" % jid, self.muc_online)
        self.add_event_handler("muc::%s::got_offline" % jid, self.muc_offline)

    def leave_room(self, room, server):
        jid = "%s@%s" % (room, server)
        self.add_event_handler("muc::%s::got_offline" % jid, self.muc_offline)
        self.add_event_handler("muc::%s::got_online" % jid, self.muc_online)
        try:
            self.plugin["xep_0045"].leaveMUC(jid, self.conf["rooms"][room]["nick"])
        except ValueError:
            pass

    def message_received(self, M):
        if M["type"] == "groupchat":
            room = M.get_from().user
            sender = M.get_from().resource
        else:
            sender = M.get_from().user
        if self.conf["server"].has_key("whitelist") and sender not in self.conf["server"]["whitelist"]:
            return
        if self.conf["server"].has_key("blacklist") and sender in self.conf["server"]["blacklist"]:
            return

        # hardcoded for security?
        if M["body"] == "!reload" and sender in ("mcmaster", "mcbastard", "billford", "dru"):
            self._plugin_manager.reload()
            M.reply("Reload complete").send()
            return

        if M["type"] == "groupchat" and self.conf["rooms"][room].get("monitor_only", False):
            return

        method = "proc"
        m = re.match("^!help ([^\s]+)", M["body"])
        if m:
            # Help mode
            plugin = m.groups()[0]
            if self._plugin_manager.call_on_plugin(plugin, "help", M):
                return
        try:
            self._plugin_manager.iter_plugins(M, method)
        except signals.ReloadSignal:
            self._plugin_manager.reload()
            M.reply("Reload complete").send()

    def muc_online(self, presence):
        room = presence.get_from().user
        roomconf = self.conf["rooms"][room]
        user = presence["muc"]["jid"].user
        if user == "":
            # Fall back to their muc nick
            user = presence["muc"]["nick"]
        if presence["muc"]["nick"] == roomconf["nick"]:
            return

        monitor_report = roomconf.get("monitor_report", None)
        if monitor_report is None:
            return
        (mtype, mto) = monitor_report.split("/", 1)
        if mtype == "room":
            self.make_muc_message(mto=mto, mbody="Notice: %s joined %s" % (user, room)).send()
        else:
            self.make_message(mto=mto, mbody="Notice: %s joined %s" % (user, room)).send()

    def muc_offline(self, presence):
        room = presence.get_from().user
        roomconf = self.conf["rooms"][room]
        user = presence["muc"]["jid"].user
        if user == "":
            # Fall back to their muc nick
            user = presence["muc"]["nick"]
        if presence["muc"]["nick"] == roomconf["nick"]:
            # Kicked
            self.leave_room(room, roomconf["server"])
            self.join_room(room, roomconf["server"], roomconf["password"])
            return

        monitor_report = roomconf.get("monitor_report", None)
        if monitor_report is None:
            return
        (mtype, mto) = monitor_report.split("/", 1)
        if mtype == "room":
            self.make_muc_message(mto=mto, mbody="Notice: %s left %s" % (user, room)).send()
        else:
            self.make_message(mto=mto, mbody="Notice: %s left %s" % (user, room)).send()

    def get_plugin(self, plugin_name):
        return self._plugin_manager.plugins[plugin_name][0]
