import mechanize
import re

def get_title(url):
    br = mechanize.Browser()
    br.set_handle_refresh(False)
    br.open(url, timeout=5)
    return br.title()

class HtmlTitlePlugin(object):
    def proc(self, M):
        m = re.search(r"(https?://\S+)", M["body"])
        if not m:
            return
        url = m.groups()[0]

        #try:
        M.reply("%s || %s" % (url,get_title(url))).send()
        #except:
        #    pass
