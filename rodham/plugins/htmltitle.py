import mechanize
import re

def get_title(url, return_url=False):
    br = mechanize.Browser()
    br.set_handle_refresh(False)
    br.open(url, timeout=5)
    if return_url:
        return (br.geturl(), br.title())
    else:
        return br.title()

class HtmlTitlePlugin(object):
    def proc(self, M):
        m = re.search(r"(https?://\S+)", M["body"])
        if not m:
            return
        url = m.groups()[0]

        try:
            (realurl, title) = get_title(url, True)
        except:
            return

        M.reply("%s || %s" % (realurl, title)).send()
