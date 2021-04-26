import pytz
from instaloader import Instaloader, Profile

tz = pytz.timezone('Asia/Bangkok')

class IgGetter:
    def __init__(self):
        self.ig = Instaloader()
        self.targets = set()
        self.targetsUserId = list()

    async def login(self, user, passwd):
        self.ig.login(user=user, passwd=passwd)
        print(f'You are logging in as {self.ig.context.username}')
        return self.ig.context.username

    async def addTargets(self, targets):
        self.targets = self.targets.union(set(targets))
        await self.__getTargetsUserId()
        return self.targets

    async def removeTargets(self, targets):
        self.targets = self.targets.difference(targets)
        await self.__getTargetsUserId()
        return self.targets

    async def __getTargetsUserId(self):
        for target in self.targets:
            profile = Profile.from_username(self.ig.context, target)
            self.targetsUserId.append(profile.userid)

    async def getStories(self, db, guild):
        if not self.targets:
            return False
        targetsUrl = dict()
        targetsLogs = await db.getLogs(guild, self.targets)
        for story in self.ig.get_stories(userids=self.targetsUserId):
            targetsUrl[story.owner_username] = list()
            for item in story.get_items():
                date = item.date_local.astimezone(tz).strftime("%d %b %Y %H:%M:%S")
                if date not in targetsLogs.get(story.owner_username):
                    if item.is_video:
                        targetsUrl[story.owner_username].insert(0, (date, '.mp4', item.video_url))
                    elif not item.is_video:
                        targetsUrl[story.owner_username].insert(0, (date, '.jpg', item.url))
        return targetsUrl
