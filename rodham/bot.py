from . import plugins
from . import signals

import copy
import re
import sleekxmpp

from sleekxmpp.jid import JID
from sleekxmpp.stanza.message import Message as BaseMessage
from sleekxmpp.xmlstream import ElementBase
from sleekxmpp.xmlstream import ET
from sleekxmpp.xmlstream import register_stanza_plugin

class MediatedInvite(ElementBase):
    name = 'x'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = "password"
    is_extension = True
    interfaces = ("password",)
    sub_interfaces = ("password",)

class Message(BaseMessage):
    sender = None

    def reply(self, *args, **kwargs):
        M = copy.copy(self)
        return BaseMessage.reply(M, *args, **kwargs)

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

        register_stanza_plugin(BaseMessage, MediatedInvite)

    @property
    def jid(self):
        return JID(self.conf["server"]["jid"])

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
                "nick": self.jid.resource
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
        M.__class__ = Message
        if M["type"] == "groupchat":
            room = M.get_from().bare
            nick = M.get_from().resource
            senderjid = self.plugin["xep_0045"].rooms[room][nick]["jid"]
            if senderjid.domain != self.jid.domain:
                sender = senderjid.bare
            else:
                sender = senderjid.user
        else:
            if senderjid.domain != self.jid.domain:
                sender = M.get_from().bare
            else:
                sender = M.get_from().user
        M.sender = sender
        if self.conf["server"].has_key("whitelist") and sender not in self.conf["server"]["whitelist"]:
            return
        if self.conf["server"].has_key("blacklist") and sender in self.conf["server"]["blacklist"]:
            return

        if M["type"] == "groupchat" and self.conf["rooms"][M.get_from().user].get("monitor_only", False):
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

    def get_nick(self, name, room):
        if room is None:
            return name
        jid = "%s@%s" % (name, self.jid.domain)
        muc = self.plugin["xep_0045"]
        for nick in muc.getRoster(room):
            if muc.rooms[room][nick]["jid"].bare == jid:
                return nick
        return name

    def get_jid(self, nick, room):
        try:
            return self.plugin["xep_0045"].rooms[room][nick]["jid"]
        except KeyError:
            return None

    def kick(self, room, nick, reason=None):
        print room
        if not room in self.conf["rooms"]:
            return
        roomconf = self.conf["rooms"][room]
        iq = self.makeIqSet()
        iq["to"] = "%s@%s" % (room, roomconf["server"])
        iq["from"] = str(self.jid)

        query = ET.Element("{http://jabber.org/protocol/muc#admin}query")
        item = ET.Element("{http://jabber.org/protocol/muc#admin}item")
        item.set("nick", nick)
        item.set("role", "none")
        if reason:
            xreason = ET.Element("{http://jabber.org/protocol/muc#admin}reason")
            xreason.text = reason
            item.append(xreason)
        query.append(item)
        iq.append(query)
        iq.send()
