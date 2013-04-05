class RulesPlugin(object):
    def proc(self, M):
        if M["body"] != "!help phones":
            return

        #TODO: Fix me
        with open("/opt/virtual_envs/rodham/conf/phone_help.txt", "r") as f:
            rules = f.read()

        M.reply(rules.strip()).send()
