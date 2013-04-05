from importlib import import_module

import copy
import inspect


class PluginStop(Exception): pass


def import_plugin(plugin, path=None):
    if path is None:
        path = "rodham.plugins.{}".format(plugin)
    try:
        m = import_module(path)
    except ImportError:
        return None
    reload(m)
    return m


class PluginManager(object):
    def __init__(self, conf, bot=None):
        self.bot = bot
        self.conf = conf
        self.collect_plugins()

    def collect_plugins(self):
        self.plugins = dict()
        for (plugin, pluginconf) in self.conf.items():
            module = import_plugin(plugin, pluginconf.get("import_path", None))
            if module == None:
                continue
            for (cls_name,cls) in inspect.getmembers(module, inspect.isclass):
                if hasattr(cls, "proc"):
                    try:
                        o = cls(conf=pluginconf, bot=self.bot)
                    except TypeError:
                        #import traceback
                        #f = self.bot.make_muc_message(mto="roddydev", mbody=traceback.format_exc())
                        #f.send()
                        o = cls()
                    #self.bot.send_message(mto="roddydev@conference.chat.hurricanedefense.com", mbody="%s loaded" % plugin, mtype="groupchat")
                    self.plugins[plugin] = (o, pluginconf)

    def reload(self):
        for plugin in self.plugins.keys():
            shutdown = getattr(self.plugins[plugin][0], "shutdown", False)
            if callable(shutdown):
                shutdown()
        self.collect_plugins()

    def iter_plugins(self, M, method="proc"):
        if M["type"] == "groupchat":
            sender = M.get_from().resource
        else:
            sender = M.get_from().user
        for plugin in self.plugins.keys():
            (p, conf) = self.plugins[plugin]
            if conf.has_key("whitelist") and sender not in conf["whitelist"]:
                continue
            if conf.has_key("blacklist") and sender in conf["blacklist"]:
                continue
            f = getattr(p, method, None)
            if callable(f):
                try:
                    f(copy.copy(M))
                except:
                    # Dump the last line of traceback somewhere, maybe?
                    import traceback
                    f = self.bot.make_muc_message(mto="roddydev", mbody=traceback.format_exc())
                    f.send()

    def call_on_plugin(self, plugin, method, M):
        if self.plugins.has_key(plugin):
            (p, conf) = self.plugins[plugin]
            f = getattr(p, method, None)
            if callable(f):
                try:
                    f(copy.copy(M))
                except:
                    # Dump the last line of traceback somewhere, maybe?
                    import traceback
                    f = self.bot.make_muc_message(mto="roddydev", mbody=traceback.format_exc())
                    f.send()
                return True
        return False
