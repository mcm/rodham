#(sk[0-9]+)
#https://supportcenter.checkpoint.com/supportcenter/portal?eventSubmit_doGoviewsolutiondetails=&solutionid=

from .htmltitle import get_title

import re

class SkTitlePlugin(object):
    def proc(self, M):
        m = re.search("\b(sk[0-9]+)", M["body"])
        if m is None:
            return

        sk = m.groups()[0]
        url = "https://supportcenter.checkpoint.com/supportcenter/portal?eventSubmit_doGoviewsolutiondetails=&solutionid=%s" % sk
        M.reply("%s || %s" % (url, get_title(url))).send()

    def help(self, M):
        M.reply("sk19423 will return a link plus title of usercenter page for that SK").send()
