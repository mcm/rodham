from copy import copy
import peewee
import re

class CostSortedDict(dict):
    def sorteditems(self):
        items = self.items()
        items.sort(lambda a,b: cmp(b[1],a[1]))
        return items

db = peewee.SqliteDatabase(None)

class BaseModel(peewee.Model):
    class Meta:
        database = db

class SwearWord(BaseModel):
    word = peewee.CharField()
    cost = peewee.FloatField()
    
class Swear(BaseModel):
    who = peewee.CharField()
    word = peewee.ForeignKeyField(SwearWord)
    cost = peewee.FloatField()
    
def get_swear_jar(who=None):
    swears = Swear.select()
    if who is not None:
        swears = swears.where(Swear.who==who)
    total = sum([ s.cost for s in swears ])
    return "${:,.2f}".format(total)

class SwearJarPlugin(object):
    def __init__(self, conf, *args, **kwargs):
        self.db = db
        self.db.init(conf["database_path"])
        self.db.connect()
        if not SwearWord.table_exists():        
            SwearWord.create_table()
        if not Swear.table_exists():        
            Swear.create_table()
        self.update_words()
        self.admins = conf["admin_users"]

    def update_words(self):
        self.swear_words = CostSortedDict([(s.word,s.cost) for s in SwearWord.select()])

    def proc(self, M):
        if M["type"] == "groupchat":
            sender = M.get_from().resource
        else:
            sender = M.get_from().user
        if sender == "":
            return
        m = re.match("^!swearjar (add|modify|delete|list|total|leaders|reset)", M["body"], flags=re.I)
        if m:
            action = m.groups()[0].lower()
            if action == "add":
                if not sender in self.admins:
                    return
                m = re.match("^!swearjar add ([\w\s]+?) \$(\d+\.\d{2})$", M["body"], flags=re.I)
                if not m:
                    M.reply("Usage: !swearjar add <word> $0.00").send()
                    return
                (word, cost) = m.groups()
                SwearWord(word=word, cost=float(cost)).save()
                M.reply("Saved!").send()
                self.update_words()
            elif action == "modify":
                if not sender in self.admins:
                    return
                m = re.match("^!swearjar modify ([\w\s]+?) \$(\d+\.\d{2})$", M["body"], flags=re.I)
                if not m:
                    M.reply("Usage: !swearjar modify <word> $0.00").send()
                    return
                (word, cost) = m.groups()
                swear_word = SwearWord.get(word=word)
                swear_word.cost = float(cost)
                swear_word.save()
                M.reply("%s updated" % word).send()
            elif action == "delete":
                if not sender in self.admins:
                    return
                SwearWord.get(word=word).delete()
                M.reply("%s deleted" % word).send()
            elif action == "list":
                words = list()
                for (word, cost) in self.swear_words.sorteditems():
                    words.append("{}: ${:,.2f}".format(word, cost))
                M.reply("\n".join(words)).send()
            elif action == "total":
                M.reply("Swear jar total: %s" % get_swear_jar()).send()
            elif action == "reset":
                if not sender in self.admins:
                    return
                Swear.delete().execute()
                M.reply("Swear jar total: %s" % get_swear_jar()).send()
            elif action == "leaders":
                leaders = CostSortedDict()
                for swear in Swear.select():
                    if not leaders.has_key(swear.who):
                        leaders[swear.who] = 0.0
                    leaders[swear.who] += swear.cost
                M.reply("\n".join([ "{}: ${:,.2f}".format(k,v) for (k,v) in leaders.sorteditems() ])).send()
            else:
                M.reply("Not yet implemented...").send()
            return

        owed = 0.0
        for (word,cost) in self.swear_words.sorteditems():
            pattern = re.sub(r"\b", r"\\b", word)
            r = re.compile(r"(%s)" % pattern, flags=re.I)
            words = r.findall(M["body"])
            owed += cost * len(words)
            if len(words) > 0:
                swear_word = SwearWord.get(word=word)
                for c in range(0, len(words)):
                    Swear(who=sender, word=swear_word, cost=cost).save()
        if owed > 0.0:
            M.reply("Shame on you {}, ${:,.2f} to the swear jar".format(sender, owed)).send()
