from .. import signals

import re


class AdminPlugin(object):
    def __init__(self, conf, bot, *args, **kwargs):
        self.bot = bot
        self.admins = conf.get("admin_users", [])

    def proc(self, M):
        m = re.match("^!admin (reload|hostname|version|leave|kick|showplugins|enable|disable|join)", M["body"], flags=re.I)
        if not m:
            return

        if M["type"] == "groupchat":
            sender = M.get_from().resource
        else:
            sender = M.get_from().user

        if sender not in self.admins:
            return

        cmd = m.groups()[0].lower()

        if cmd == "reload":
            raise signals.ReloadSignal
        elif cmd == "hostname":
            import socket
            M.reply(socket.gethostname()).send()
        elif cmd == "version":
            M.reply("Not implemented").send()
        elif cmd == "leave" or cmd == "join":
            m = re.match("!admin (?:(join) (\S+) (\S+)(?:$| (\S+))|(leave) (\S+))", M["body"], flags=re.I)
            if not m:
                return
            if m.groups()[0] is not None:
                (room, server, password, _, _) = m.groups()[1:]
                self.bot.join_room(room, server, password)
            else:
                room = m.groups()[-1]
                try:
                    server = self.bot.conf["rooms"][room]["server"]
                except KeyError:
                    M.reply("Unable to leave %s" % room).send()
                    return
                self.bot.leave_room(room, server)
        elif cmd == "kick":
            M.reply("Not implemented").send()
        elif cmd == "showplugins":
            import copy
            for plugin in self.bot._plugin_manager.plugins.keys():
                disabled = getattr(self.bot._plugin_manager.plugins[plugin][0], "disabled", False)
                status = "disabled" if disabled else "enabled"
                copy.copy(M).reply("%s (%s)" % (plugin, status)).send()
        elif cmd == "enable":
            m = re.match("!admin enable (\S+)$", M["body"], flags=re.I)
            if not m:
                return

            plugin = m.groups()[0]
            try:
                disabled = getattr(self.bot._plugin_manager.plugins[plugin][0], "disabled", False)
            except KeyError:
                M.reply("Unable to locate '%s' plugin" % plugin).send()
                return
            if disabled:
                self.bot._plugin_manager.plugins[plugin][0].disabled = False
                M.reply("Enabled '%s' plugin" % plugin).send()
            else:
                M.reply("'%s' plugin already enabled" % plugin).send()
        elif cmd == "disable":
            m = re.match("!admin disable (\S+)$", M["body"], flags=re.I)
            if not m:
                return

            plugin = m.groups()[0]
            try:
                disabled = getattr(self.bot._plugin_manager.plugins[plugin][0], "disabled", False)
            except KeyError:
                M.reply("Unable to locate '%s' plugin" % plugin).send()
                return
            if not disabled:
                self.bot._plugin_manager.plugins[plugin][0].disabled = True
                M.reply("Disabled '%s' plugin" % plugin).send()
            else:
                M.reply("'%s' plugin already disabled" % plugin).send()
