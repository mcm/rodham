import datetime
import peewee
import re


db = peewee.SqliteDatabase(None)

class BaseModel(peewee.Model):
    class Meta:
        database = db

class PointAssignment(BaseModel):
    giver = peewee.CharField()
    receiver = peewee.CharField()
    date = peewee.DateField()
    points = peewee.IntegerField()

class PlusOnePlugin(object):
    def __init__(self, *args, **kwargs):
        conf = kwargs["conf"]
        self.bot = kwargs["bot"]
        self.db = db
        self.db.init(conf["database_path"])
        self.db.connect()
        if not PointAssignment.table_exists():
            PointAssignment.create_table()
        self.last_cleanup = datetime.date.today() - datetime.timedelta(1)
        self.last = None
        self.admin_users = conf.get("admin_users", [])
        self.max_points = int(conf.get("max_points", 25))
        self.joking_points = int(conf.get("joking_points", 1000))

    def cleanup(self):
        today = datetime.date.today()
        if self.last_cleanup == today:
            return
        for pa in PointAssignment.select().where(PointAssignment.date < today):
            pa.delete_instance()
        self.last_cleanup = today

    def proc(self, M):
        if M["type"] == "groupchat":
            nick = M["mucnick"]
            room = M["mucroom"]
        else:
            return

        self.cleanup()

        m = re.match("^!points(?:$| (reset)$)", M["body"], flags=re.I)
        if m:
            if m.groups()[0] is not None:
                if not M.sender in self.admin_users:
                    return
                PointAssignment.delete().execute()
                M.reply("Points reset").send()
            points = dict()
            for pa in PointAssignment.select().where(PointAssignment.date == datetime.date.today()):
                if not points.has_key(pa.receiver):
                    points[pa.receiver] = 0
                points[pa.receiver] += pa.points
            users = points.keys()
            users.sort(lambda b,a: cmp(points[a], points[b]))
            for user in users:
                M.reply("%s: %s" % (user, points[user])).send()
            return

        m = re.search(r"\+(\d+)", M["body"])
        if m is None:
            self.last = (M.sender, nick)
            return

        points = int(m.groups()[0])
        if points > self.joking_points:
            # Assume they were kidding
            return

        sender = M.sender

        m = re.match("^@(\S+)", M["body"])
        if m is not None:
            lastnick = m.groups()[0]
            lastjid = self.bot.get_jid(lastnick, room)
            if lastjid is None:
                M.reply("%s: can't find that user" % nick).send()
                return
            lastsender = lastjid.user
        else:
            (lastsender, lastnick) = self.last

        pointsgiven = sum([pa.points for pa in PointAssignment.select().where(PointAssignment.giver == sender)])
        if (points + pointsgiven) > self.max_points:
            points = self.max_points - pointsgiven
            if points == 0:
                M.reply("%s: you are out of points to give for today" % nick).send()
                return
            else:
                M.reply("%s: you only have %s points left for the day, assigning them to %s" % (nick, points, lastnick)).send()

        PointAssignment(giver=sender,receiver=lastsender,date=datetime.date.today(),points=points).save()
        M.reply("%s: you were just given %s points by %s" % (lastnick, points, nick)).send()
