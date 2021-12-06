import discord
from discord.ext import commands
from music_cog import music_cog

bot = commands.Bot(command_prefix='!')
bot.add_cog(music_cog(bot))

print('TekkersBot Started')
bot.run('discordBot Token')
