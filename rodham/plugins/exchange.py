import os
import re
import requests

class RulesPlugin(object):
    def __init__(self, *args, **kwargs):
        self.conf = kwargs["conf"]

    def proc(self, M):
        m = re.match("^!exchange", M["body"], flags=re.I)
        if not m:
            return

        amount = None
        base = None
        target = None

        m = re.match("^!exchange ([A-Z]+) to ([A-Z]+)", M["body"], flags=re.I)
        if m:
            base,target = m.groups()

        m = re.match("^!exchange ([0-9.]+)([A-Z]+) to ([A-Z]+)", M["body"], flags=re.I)
        if m:
            amount,base,target = m.groups()

        if base is None or target is None:
            return

        url = "http://openexchangerates.org/api/latest.json?app_id=747d3ac6105f45c09c4d45f6829be195&base={}".format(base)
        rates = requests.get(url).json()["rates"]

        if target not in rates:
            response = "Target currency not found"
        else:
            amount = 1.0 if amount == None else float(amount)
            exchange = rates[target] * amount
            response = "{}{} = {}{}".format(amount, base, exchange, target)

        M.reply(response).send()
