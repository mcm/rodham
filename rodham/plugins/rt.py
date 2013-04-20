import requests
import re

class RtPlugin(object):
    def __init__(self, conf, *args, **kwargs):
        self.auth_payload = {
            "user": conf["username"],
            "pass": conf["password"],
        }
        self.urlroot = conf["url"]
        self.session = requests.Session()
        self.session.post(self.urlroot, data=self.auth_payload, verify=False)
        self.admins = conf.get("admin_users", [])

    def proc(self, M):
        sender = M.sender

        def steal_ticket(ticket):
            payload = { "content": "Action: Steal" }
            self.session.post("%s/REST/1.0/ticket/%s/take" % (self.urlroot, ticket), data=payload)

        def assign_ticket(ticket, owner):
            payload = { "content": "Owner: %s" % owner }
            self.session.post("%s/REST/1.0/ticket/%s/edit" % (self.urlroot, ticket), data=payload)

        def open_ticket(ticket):
            payload = { "content": "Status: open" }
            self.session.post("%s/REST/1.0/ticket/%s/edit" % (self.urlroot, ticket), data=payload)

        def close_ticket(ticket):
            payload = { "content": "Status: resolved" }
            self.session.post("%s/REST/1.0/ticket/%s/edit" % (self.urlroot, ticket), data=payload)

        def get_ticket_info(ticket):
            r = self.session.get("%s/REST/1.0/ticket/%s/show" % (self.urlroot, ticket))
            lines = r.content.split("\n")[2:]
            if lines[0] == "# Ticket %s does not exist." % ticket:
                return None

            info = dict()
            lastkey = ""
            for line in lines:
                line = line.rstrip()
                if line == "":
                    continue
                try:
                    (key, value) = line.split(":", 1)
                except ValueError:
                    info[lastkey] += line
                else:
                    info[key.lower()] = value.strip()
                    lastkey = key.lower()
            info["id"] = info["id"].split("/")[1]
            info["link"] = "https://rt.hurricanedefense.com/Ticket/Display.html?id=%s" % info["id"]
            return info

        m = re.match("!rt (take|give \w+|open|close|resolve|admin_users) hd\s*#\s*(\d+)", M["body"], flags=re.I)
        if m:
            (action, ticket) = m.groups()
            info = get_ticket_info(ticket)
            if info is None:
                M.reply("Ticket %s does not exist." % ticket).send()
                return

            action = action.lower()

            if action == "open":
                if (info["status"] != "new" and info["owner"] != sender) and sender not in self.admins:
                    M.reply("%s: Unable to open ticket: status is %s and you are not the owner" % (sender, info["status"])).send()
                    return
                open_ticket(ticket)
            elif action == "close" or action == "resolve":
                if info["owner"] != sender and sender not in self.admins:
                    M.reply("%s: Unable to close ticket: you are not the owner" % sender).send()
                    return
                close_ticket(ticket)
            elif action == "take":
                if (info["owner"].lower() != "nobody" and info["owner"] != "stuart") and sender not in self.admins:
                    M.reply("%s: Unable to take ticket: ticket is owned by %s" % (sender, info["owner"])).send()
                    return
                elif info["owner"] != "stuart":
                    # Need to steal ticket first
                    steal_ticket(ticket)
                assign_ticket(ticket, sender)
            elif action[:4] == "give":
                (action, target) = action.split(" ", 1)
                if (info["owner"] != "nobody" and info["owner"] != sender) and sender not in self.admins:
                    M.reply("%s: Unable to give ticket: ticket is owned by %s" % (sender, info["owner"])).send()
                    return
                elif info["owner"] != "stuart":
                    # Need to steal ticket first
                    steal_ticket(ticket)

                if target != "stuart":
                    assign_ticket(ticket, target)
#            elif action == "admin_users":
#                M.reply(",".join(self.admins)).send()
#                return

        # Including above actions, if the message matches the hd#, return ticket info
        m = re.search("hd\s*#\s*(\d+)", M["body"], flags=re.I)
        if m:
            ticket = m.groups()[0]
            info = get_ticket_info(ticket)
            if info:
                M.reply("HD#%(id)s || Queue: %(queue)s || Status: %(status)s || %(subject)s || Owner: %(owner)s || %(link)s" % info).send()
            else:
                M.reply("Ticket %s does not exist." % ticket).send()
