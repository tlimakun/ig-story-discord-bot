import aiohttp
import discord
from discord.ext import tasks
from io import BytesIO
from igGetter import IgGetter
from firebase import Firebase

# Temp variable must be called from secret environment
user = "m1ghty.tuka"
ig_passwd = "mighty24"
email = "araidwadiscord@gmail.com"
password = "!mighty24"
token = "ODM0ODQ0MzY4NjI3OTU3Nzkx.YIGzaA.LArEwxdEiPyyHaPuVp4DTjojgKc"
guild = 579263195940782080
#-----------------------------------------------------

channel_id = None
minInterval = 60
interval = 60 # Second
isLogged =False

ig = IgGetter()
db = Firebase(email=email, passwd=password, ig=ig)
bot = discord.Client()

@tasks.loop(seconds=interval)
async def ig_send():
    if channel_id:
        channel = bot.get_channel(channel_id)
        targetsUrl = dict()
        targetsLog = dict()
        if ig.targets:
            try:
                targetsUrl = await ig.getStories(db, guild)
            except:
                await ig.login(user=user, passwd=ig_passwd)
            print(targetsUrl)
            for target in targetsUrl.keys():
                targetsLog[target] = []
                for log in targetsUrl.get(target):
                    # log[0] = date, log[1] = format, log[2] = url
                    async with aiohttp.ClientSession() as session:
                        async with session.get(log[2]) as resp:
                            if resp.status != 200:
                                return await channel.send(f"Could not download {target}'s story at {log[0]}.")
                            load_pic = BytesIO(await resp.read())
                            content=f"From: {target}\nAt: {log[0]}"
                            print(f"{target}_{log[0].replace(':', '-')}{log[1]}")
                            await channel.send(content=content, file=discord.File(load_pic, f"{target}_{log[0].replace(':', '-')}{log[1]}"))
                    del load_pic
                    targetsLog[target].append(log[0])
            await db.updateLogs(guild, targetsLog)

@ig_send.before_loop
async def before_ig_send():
    await bot.wait_until_ready()

@tasks.loop(minutes=30)
async def update_token_log():
    db.refreshToken()
    db.removeLogs(guild)

@update_token_log.before_loop
async def before_update_token_log():
    await bot.wait_until_ready()

async def assignData(response):
    global channel_id, interval
    if response.get('channel_id'):
        channel_id = int(response.get('channel_id'))
    if response.get('interval'):
        interval = response.get('interval')
        ig_send.change_interval(seconds=interval)

@bot.event
async def on_ready():
    global isLogged
    response = await db.loadData(guild)
    await assignData(response)
    if not isLogged:
        await ig.login(user=user, passwd=ig_passwd)
        isLogged = True
    ig_send.start()
    update_token_log.start()
    print(f'Connecting as {bot.user}')

@bot.event
async def on_message(message):
    global channel_id, interval
    channel = None
    user = message.author
    if user == bot:
        return

    if channel_id:
        channel = bot.get_channel(channel_id)
    else:
        channel = message.channel
    
    if message.channel != channel:
        return

    if message.content.startswith('!ig'):
        cmd = message.content.split(' ')
        if len(cmd) == 1:
            await channel.send(f'Hello {user.mention}! our commands are not available right now.')
        elif cmd[1] == 'set':
            if len(cmd) == 2:
                await channel.send('Please enter what you want to SET.')
            elif cmd[2] == 'channel':
                if len(cmd) == 3:
                    await channel.send('Please enter channel id...')
                elif len(cmd) > 4:
                    await channel.send('Please enter only ONE channel id.')
                else:
                    try:
                        if int(cmd[3]) == channel_id:
                            await channel.send(f"I'am already in {channel.name}.")
                        else:
                            await channel.send(f'I am going to {channel.name}.')
                            channel_id = await db.setChannelId(guild, cmd[3])
                            channel = bot.get_channel(channel_id)
                            await channel.send(f'I am now in {channel.name}.')
                    except:
                        await channel.send('Invalid id! it should be all number.')
            elif cmd[2] == 'interval':
                if len(cmd) == 3:
                    await channel.send('Please enter interval...')
                elif len(cmd) > 4:
                    await channel.send('Please enter only ONE interval.')
                else:
                    try:
                        if int(cmd[3]) == interval:
                            await channel.send(f"Interval already {interval}.")

                        if int(cmd[3]) < minInterval:
                            await channel.send(f"Interval can't be less than {minInterval} seconds.")
                        else:
                            interval = await db.setInterval(guild, int(cmd[3]))
                            ig_send.change_interval(seconds=interval)
                            await channel.send(f'Interval is now {interval} seconds.')
                    except:
                        await channel.send('Invalid interval! it should be all number.')
            else:
                await channel.send(f'No {cmd[2]} to set...')
        elif cmd[1] == 'get':
            if len(cmd) == 2:
                await channel.send('Please enter what you want to CHECK.')
            elif cmd[2] == 'interval':
                if len(cmd) > 3:
                    await channel.send('No need to assign value for check command.')
                else:
                    response = await db.getInterval(guild)
                    await channel.send(f'Current interval: {response}')
            elif cmd[2] == 'targets':
                if len(cmd) > 3:
                    await channel.send('No need to assign value for check command.')
                else:
                    response = await db.getTargets(guild)
                    await channel.send(f'Current targets: {response}')
            else:
                await channel.send(f'No {cmd[2]} to check...')
        elif cmd[1] == 'add':
            if len(cmd) == 2:
                await channel.send('Please enter what you want to ADD.')
            elif cmd[2] == 'targets':
                if len(cmd) == 3:
                    await channel.send('Please enter at least one target to add...')
                else:
                    await channel.send('Updating...')
                    targets = await db.addTargets(guild, cmd[3:])
                    await channel.send(f'Updated! Current Targets: {", ".join(targets)}')
            else:
                await channel.send(f'No {cmd[2]} to add...')
        elif cmd[1] == 'remove':
            if len(cmd) == 2:
                await channel.send('Please enter what you want to REMOVE.')
            elif cmd[2] == 'targets':
                if len(cmd) == 3:
                    await channel.send('Please enter at least one target to remove...')
                else:
                    await channel.send('Removing...')
                    tmp = [target for target in cmd[3:] if target in ig.targets]
                    targets = await db.removeTargets(guild, tmp)
                    await channel.send(f'Removed! Current Targets: {", ".join(targets)}')
            else:
                await channel.send(f'No {cmd[2]} to remove...')
        else:
            await channel.send('Invalid command...')

bot.run(token)
