class RulesPlugin(object):
    def proc(self, M):
        if M["body"] != "!rules":
            return

        #TODO: Fix me
        with open("/opt/virtual_envs/rodham/conf/roddy_rules.txt", "r") as f:
            rules = f.read()

        M.reply(rules.strip()).send()
