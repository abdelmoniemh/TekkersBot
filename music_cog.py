import discord
from discord.ext import commands
import spotipy
from spotipy import SpotifyClientCredentials
from yt_dlp import YoutubeDL
import random



class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # all the music related stuff
        self.is_playing = False

        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio'}
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = ""

     # searching the item on youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" %
                                        item, download=False)['entries'][0]
            except Exception:
                return False

            for version in info['formats']:
                if 'storyboard' not in version['format']:
                    return {'source': version['url'], 'title': info['title']}
        return 0

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            # get the first url
            m_url = self.music_queue[0][0]['source']

            # remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(
                m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    # infinite loop checking
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            # try to connect to voice channel if you are not already connected

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])

            await ctx.send("Now playing: " + self.music_queue[0][0]['title'])

            # remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(
                m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
            if len(self.music_queue) == 0:
                await self.vc.disconnect()

    @commands.command(name="play", help="Plays a selected song from youtube")
    async def p(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            # you need to be connected so that the bot knows where to go
            await ctx.send("Connect to a voice channel!")
        else:
            foundSong = self.search_yt(query)
            if type(foundSong) == type(True):
                await ctx.send("Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            else:
                await ctx.send(f"{foundSong['title']} added to the queue")

                self.music_queue.append([foundSong, voice_channel])

                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="queue", help="Displays the current songs in queue")
    async def q(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += self.music_queue[i][0]['title'] + "\n"

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")

    @commands.command(name="skip", help="Skips the current song being played")
    async def skip(self, ctx):
        if self.vc != "" and self.vc:
            self.vc.stop()
            # try to play next in the queue if it exists
            await self.play_music(ctx)

    @commands.command(name="clear", help="Clears Queue")
    async def clear(self, ctx):
        self.music_queue = []
        await self.skip(ctx)
        await ctx.send("Music queue is now empty")

    @commands.command(name="disconnect", help="Disconnecting bot from VC")
    async def dc(self, ctx):
        await self.vc.disconnect()
    
    @commands.command(name="shuffle", help="Shuffles the current queue")
    async def shffle(self, ctx):
        random.shuffle(self.music_queue)
        await self.queueInternal(ctx)
    
    async def playInternal(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            # you need to be connected so that the bot knows where to go
            await ctx.send("Connect to a voice channel!")
        else:
            foundSong = self.search_yt(query)
            if type(foundSong) == type(True):
                await ctx.send("Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            else:
                await ctx.send(f"{foundSong['title']} added to the queue")

                self.music_queue.append([foundSong, voice_channel])

                if self.is_playing == False:
                    await self.play_music(ctx)
    async def queueInternal(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += self.music_queue[i][0]['title'] + "\n"

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")

    async def spotifyToQueue(self, ctx, url: str):
        spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials('client_id', 'client_secret'))
        items = spotify.playlist_items(url, None, 100, 0, None)
        tempQueue = []
        for item in items['items']:
            searchParameter = item['track']['name'] + " "
            for artist in item['track']['artists']:
                searchParameter += artist['name']  + " "
            searchParameter += " official audio"
            tempQueue.append(searchParameter)
        
        for song in tempQueue:
            await self.playInternal(ctx, song)



    @commands.command(name="playSpotify", help="plays spotify playlist using link")
    async def playSpotify(self, ctx, url):
        print(url)
        await self.spotifyToQueue(ctx, url)
