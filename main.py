import discord
from discord.ext import commands
import json
import os
import asyncio

# 加载设置
with open('setting.json', "r", encoding="utf8") as file:
  data = json.load(file)

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), help_command=commands.DefaultHelpCommand(), intents=discord.Intents.all())

# 添加事件
@bot.event
async def on_ready():
    print(f"I am running on {bot.user.name}")
    print(f"With the ID: {bot.user.id}")
    print('Bot is ready to be used')
    print("\n" + bot.user.name + "有管理權的伺服器")
    for guild in bot.guilds:
        print(f"伺服器名稱: {guild.name}")
        print(f"伺服器ID: {guild.id}")

async def load():
  for filename in os.listdir('cmds'):
    if filename.endswith('.py'):
      try:
        bot.load_extension(f"cmds.{filename[:-3]}")
      except Exception as e:
        print(f"Error loading extension {filename[:-3]}: {e}")

@bot.slash_command()
async def reload(ctx, extension):
    bot.reload_extension(f'cmds.{extension}')
    await ctx.respond(f'Reloading {extension} done!')


async def main():
  await load()

if __name__ == "__main__":
  asyncio.run(main())
  bot.run(data['TOKEN1'])