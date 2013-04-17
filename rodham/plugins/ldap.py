from __future__ import absolute_import

import ldap
import re

class LdapPlugin(object):
    regexes = [
        re.compile("^!ldap (name) (\d\d\d-\d\d\d-\d\d\d\d)$", flags=re.I),
        re.compile("^!ldap (mobile) ([a-zA-Z '-]{3,})$", flags=re.I),
        re.compile("^!ldap (email) ([a-zA-Z '-]{3,})$", flags=re.I),
        re.compile("^!ldap (home) ([a-zA-Z '-]{3,})$", flags=re.I),
        re.compile("^!ldap (office) ([a-zA-Z '-]{3,})$", flags=re.I),
        re.compile("(\d\d\d-\d\d\d-\d\d\d\d)", flags=re.I),
    ]

    def __init__(self, conf, *args, **kwargs):
        self._ldap = ldap.open(conf["server"])
        self._ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, int(conf.get("timeout", 3)))
        try:
            if conf.get("starttls", True):
                self._ldap.start_tls_s()
            self._ldap.simple_bind()
        except ldap.SERVER_DOWN:
            self._ldap = None
        self.filter = conf.get("filter", None)
        self.ldap_base = conf.get("base", "")

    def get_user_by_extension(self, ext):
        res = self._ldap.search_s(self.ldap_base, ldap.SCOPE_SUBTREE, '(&(objectClass=inetOrgPerson)(telephoneNumber=*923-1330 x%s))' % ext, ('uid',))
        if len(res) == 0:
            return None
        return res[0][1]["uid"][0]

    def get_extension_by_user(self, username):
        res = self._ldap.search_s(self.ldap_base, ldap.SCOPE_SUBTREE, '(&(objectClass=inetOrgPerson)(uid=%s))' % username, ('telephoneNumber',))
        if len(res) == 0:
            return None
        return res[0][1]["telephoneNumber"][0].split(" ")[-1].lstrip("x")

    def get_someones_number(self, name, number_type):
        if number_type is None:
            number_type = "office"
        filter_ = "(cn=*%s*)" % name
        returnkey = {
            "home": "homePhone",
            "office": "telephoneNumber",
        }.get(number_type, number_type) # Default to the actual type

        if self.filter:
            filter_ = "(&%s%s)" % (self.filter, filter_)

        results = self._ldap.search_s(self.ldap_base, ldap.SCOPE_SUBTREE, filter_, ('cn', returnkey,))

        if len(results) == 0:
            return None
        if results[0][1].has_key(returnkey):
            return (results[0][1]["cn"][0], results[0][1][returnkey][0])
        else:
            return (results[0][1]["cn"][0], None)

    def proc(self, M):
        if self._ldap is None:
            return

        for regex in self.regexes:
            m = regex.search(M["body"])
            if m:
                groups = list(m.groups())

                if len(groups) == 1 or groups[0] == "name":
                    number = groups[0]
                    if groups[0] == "name":
                        number = groups[1]
                    p = re.search("(\d{3}).*?(\d{3}).*?(\d{4})", number)
                    numfilter = "*%s*%s*%s" % p.groups()
                    filter_ = "(|(telephoneNumber=%s)(mobile=%s)(homePhone=%s))" % (numfilter, numfilter, numfilter)
                    returnkey = "cn"
                else:
                    if groups[1] == "joe's dad":
                        groups[1] = "Len Gedeon"
                    filter_ = "(cn=*%s*)" % groups[1]
                    returnkey = {
                        "email": "mail",
                        "home": "homePhone",
                        "office": "telephoneNumber",
                    }.get(groups[0], groups[0]) # Default to the actual type

                if self.filter:
                    filter_ = "(&%s%s)" % (self.filter, filter_)

                results = self._ldap.search_s(self.ldap_base, ldap.SCOPE_SUBTREE, filter_, ('cn', returnkey,))

                if len(results) == 0:
                    M.reply("That request does not compute - do better").send()
                    return

                cn = results[0][1]["cn"][0]
                
                if returnkey == "cn":
                    M.reply("%s || %s" % (number, cn)).send()
                else:
                    try:
                        response = results[0][1][returnkey][0]
                    except KeyError:
                        response = ""
                    M.reply("%s || %s" % (cn, response)).send()
                return
