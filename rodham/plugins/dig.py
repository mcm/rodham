import copy
import dns.resolver
import re

class DigPlugin(object):
    regexes = [
        re.compile(r"!(dig|host) (?P<target>[^\s]+)", flags=re.I),
        re.compile(r"!(dig|host) (?P<rrtype>a|aaaa|mx|ns|ptr) (?P<target>[^\s]+)", flags=re.I),
        re.compile(r"!(dig|host) @(?P<ns>[^\s]+) (?P<rrtype>a|aaaa|mx|ns|ptr) (?P<target>[^\s]+)", flags=re.I),
    ]

    def proc(self, M):
        if re.match("^!dig", M["body"]) or re.match("^!host", M["body"]):
            for regex in self.regexes:
                m = regex.search(M["body"])
                if m:
                    d = m.groupdict()
                    try:
                        if d.has_key("rrtype"):
                            if d.has_key("ns"):
                                R = dns.resolver.Resolver()
                                R.nameservers = [ d["ns"] ]
                                answers = R.query(d["target"], d["rrtype"])
                            else:
                                answers = dns.resolver.query(d["target"], d["rrtype"])
                        else:
                            # Just a target
                            answers = dns.resolver.query(d["target"], "A")
                    except dns.resolver.NXDOMAIN:
                        answers = None

                    if answers:
                        M.reply(answers[0].to_text()).send()

    def help(self, M):
        M.reply("dig @nameserver querytype hostname").send()
