from importlib import import_module

from .. import signals

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

    def debug_message(self, *args, **kwargs):
        return self.bot.debug_message(*args, **kwargs)

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
                        o = cls()
                    self.plugins[plugin] = (o, pluginconf)

    def reload(self):
        for plugin in self.plugins.keys():
            shutdown = getattr(self.plugins[plugin][0], "shutdown", False)
            if callable(shutdown):
                shutdown()
        self.bot.reload_config()
        self.collect_plugins()

    def iter_plugins(self, M, method="proc"):
        sender = M.sender
        for plugin in self.plugins.keys():
            (p, conf) = self.plugins[plugin]
            if getattr(p, "disabled", False):
                continue
            if conf.has_key("whitelist") and sender not in conf["whitelist"]:
                continue
            if conf.has_key("blacklist") and sender in conf["blacklist"]:
                continue
            f = getattr(p, method, None)
            if callable(f):
                try:
                    f(M)
                except signals.ReloadSignal:
                    raise signals.ReloadSignal()
                except:
                    # Dump the last line of traceback somewhere, maybe?
                    import traceback
                    self.debug_message(traceback.format_exc())

    def call_on_plugin(self, plugin, method, M):
        if self.plugins.has_key(plugin):
            (p, conf) = self.plugins[plugin]
            f = getattr(p, method, None)
            if callable(f):
                try:
                    f(M)
                except signals.ReloadSignal:
                    raise signals.ReloadSignal()
                except:
                    # Dump the last line of traceback somewhere, maybe?
                    import traceback
                    self.debug_message(traceback.format_exc())
                return True
        return False
