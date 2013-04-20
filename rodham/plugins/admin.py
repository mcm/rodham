from .. import signals

import re


class AdminPlugin(object):
    def __init__(self, conf, bot, *args, **kwargs):
        self.bot = bot
        self.admins = conf.get("admin_users", [])

    def proc(self, M):
        m = re.match("^!admin (blacklist add|blacklist remove|reload|hostname|version|leave|kick|showplugins|enable|disable|join)", M["body"], flags=re.I)
        if not m:
            return

        sender = M.sender
        print sender

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
            m = re.match(r"!admin kick (?:(\S+) )?{(.+?)}(?:$| (.+)$)", M["body"], flags=re.I)
            if not m:
                return

            if m.groups()[0] is None:
                room = M.get_from().user
            else:
                room = m.groups()[0]

            if m.groups()[2] is None:
                reason = "admin requested"
            else:
                reason = m.groups()[2]

            self.bot.kick(room, m.groups()[1], reason=reason)
        elif cmd == "showplugins":
            for plugin in self.bot._plugin_manager.plugins.keys():
                disabled = getattr(self.bot._plugin_manager.plugins[plugin][0], "disabled", False)
                status = "disabled" if disabled else "enabled"
                M.reply("%s (%s)" % (plugin, status)).send()
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
        elif cmd == "blacklist add":
            m = re.match("^!admin blacklist add (\S+)", M["body"], flags=re.I)
            if m is None:
                return

            badmonkey = m.groups()[0]
            if badmonkey not in self.bot.conf["server"]["blacklist"]:
                self.bot.conf["server"]["blacklist"].append(badmonkey)
                M.reply("%s blacklisted" % badmonkey).send()
            else:
                M.reply("%s already blacklisted" % badmonkey).send()
        elif cmd == "blacklist remove":
            m = re.match("^!admin blacklist remove (\S+)", M["body"], flags=re.I)
            if m is None:
                return

            goodmonkey = m.groups()[0]
            if goodmonkey in self.bot.conf["server"]["blacklist"]:
                self.bot.conf["server"]["blacklist"].remove(goodmonkey)
                M.reply("%s removed from blacklist" % goodmonkey).send()
            else:
                M.reply("%s not blacklisted" % goodmonkey).send()
