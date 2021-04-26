import pyrebase
import pytz
from datetime import datetime, timedelta

tz = pytz.timezone('Asia/Bangkok')

class Firebase:
    def __init__(self, email, passwd, ig):
        self.config = {
            "apiKey": "AIzaSyCHHOoccxNNwEIDV14Ad2wfoiqSL8nbF78",
            "authDomain": "ig-discord-bot.firebaseapp.com",
            "projectId": "ig-discord-bot",
            "databaseURL": "https://ig-discord-bot-default-rtdb.firebaseio.com",
            "storageBucket": "ig-discord-bot.appspot.com",
            "messagingSenderId": "895815632431",
            "appId": "1:895815632431:web:295ea069211886322be8da",
            "measurementId": "G-9XCNZCW8XD"
        }
        self.firebase = pyrebase.initialize_app(self.config)
        self.auth = self.firebase.auth()
        self.user = self.auth.sign_in_with_email_and_password(email=email, password=passwd)
        self.token = self.user['idToken']
        self.db = self.firebase.database()
        self.ig = ig
    
    def refreshToken(self):
        self.user = self.auth.refresh(self.user['refreshToken'])
        self.token = self.user['idToken']

    async def loadData(self, guild):
        if self.db.child(guild).get(self.token).val():
            self.db.child(guild).update({"init": 1}, self.token)
        data = self.db.child(guild).get(self.token).val()
        if 'targets' in data.keys():
            await self.ig.addTargets([target.replace(' ', '.') for target in data.get('targets')])
        return {"channel_id": data.get('channel_id'), "interval": data.get('interval')}

    async def setChannelId(self, guild, channel_id):
        self.db.child(guild).update({"channel_id": channel_id}, self.token)
        return int(channel_id)

    async def setInterval(self, guild, interval):
        self.db.child(guild).update({"interval": interval}, self.token)
        return interval

    async def getInterval(self, guild):
        interval = self.db.child(guild).child("interval").get(self.token).val()
        return interval

    async def addTargets(self, guild, targets):
        targets_dict = dict()
        for target in targets:
            tmp = target.replace('.', ' ')
            targets_dict[tmp] = 1
        self.db.child(guild).child("targets").update(targets_dict, self.token)
        updated = await self.ig.addTargets(targets)
        return updated
    
    async def removeTargets(self, guild, targets):
        for target in targets:
            self.db.child(guild).child("targets").child(target.replace('.', ' ')).remove(self.token)
        updated =  await self.ig.removeTargets(targets)
        return updated

    async def getTargets(self, guild):
        targets = self.db.child(guild).child("targets").get(self.token).val()
        if targets:
            targets = ', '.join([target.replace(' ', '.') for target in targets.keys()])
        return targets

    async def updateLogs(self, guild, targetsLogs):
        for target in targetsLogs.keys():
            log_dict = dict()
            for log in targetsLogs.get(target):
                log_dict[log] = 1
            self.db.child(guild).child("logs").child(target.replace('.', ' ')).update(log_dict, self.token)

    async def getLogs(self, guild, targets):
        targetsLogs = dict()
        for target in targets:
            temp = self.db.child(guild).child("logs").child(target.replace('.', ' ')).get(self.token).val()
            if temp:
                targetsLogs[target] = list(temp.keys())
            else:
                targetsLogs[target] = list()
        return targetsLogs
    
    def removeLogs(self, guild):
        targetsLogs = self.db.child(guild).child("logs").get(self.token).val()
        if targetsLogs:
            for target in targetsLogs.keys():
                for log in targetsLogs.get(target).keys():
                    now = datetime.now(tz)
                    time_diff = now - datetime.strptime(log, "%d %b %Y %H:%M:%S").astimezone(tz)
                    if time_diff > timedelta(hours=24):
                        self.db.child(guild).child("logs").child(target).child(log).remove(self.token)