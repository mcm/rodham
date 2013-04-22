import configobj


def get_config(**options):
    conffile = "/etc/rodham/rodham.conf"
    if options.get("conffile", False):
        conffile = options.get("conffile")
    cdict = configobj.ConfigObj(conffile)
    cdict.update(options)
    return cdict
