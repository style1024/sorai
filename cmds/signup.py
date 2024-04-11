import discord
from discord.ext import commands
from discord.ui import Button, View
import pygsheets
import pandas as pd
import json

with open('setting.json', "r", encoding="utf8") as file:
  data = json.load(file)

#API金鑰
gc = pygsheets.authorize(service_file="api_key.json")

#取得Google Sheet ID
id = data['sheetID']

#報名表單
sheet = gc.open_by_url(f'https://docs.google.com/spreadsheets/d/{id}/edit?usp=sharing')

signupsheet =  sheet[0]
checkin = sheet[1]

class SignUp(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    async def 報名須知(self, ctx):
        Embed = discord.Embed(title="SORAI Unite",
                            description="SORAI Unite社群比賽報名須知",
                            color=discord.Color.random())
        # Embed.set_thumbnail(url="https://i.imgur.com/lyjRujt.gif")
        Embed.add_field(name="/報名", value="根據畫面指示輸入資料完成報名手續，完成後會有成功訊息", inline=False)
        Embed.add_field(name="/取消參賽",value="點選點選畫面上按鈕完成取消參賽手續",inline=False)
        Embed.add_field(name="", value="", inline=False)
        Embed.add_field(name="如有任何問題都可以詢問管理人員", value="", inline=False)
        await ctx.respond(embed=Embed)

    ## TODO : 1.驗證參賽者是否在DC裡面  2. 確認是否有重複報名  3. 隊名是否有重複 
    @commands.slash_command()
    async def 報名(self, ctx):
        modal = SignUpView(title="Unite社群比賽報名表單")
        await ctx.send_modal(modal)

    ## TODO : 1. 點選後抓取使用者的RoleID，之後再寫入Google Sheet
    @commands.slash_command()
    async def 報到(self, ctx):
        embed = discord.Embed(title="報到按鈕", description="這是一個Embed帶有按鈕", color=discord.Color.blue())
        view = CheckInView()
        await ctx.respond(embed=embed, view=view)

    ## TODO : 1. 點選後抓取使用者RoleID，之後再去寫入Google Sheet
    @commands.slash_command()
    async def 取消參賽(self, ctx):
        embed = discord.Embed(title="確認退出比赛", description=f"您確定要退出比赛嗎？", color=discord.Color.red())
        view = ConfirmationView("")
        await ctx.respond(embed=embed, view=view, ephemeral=True)
        await view.wait()
        if view.value is None:
            await ctx.respond("超過時間，操作結束。", ephemeral=True)

# 報到用
class CheckInView(View):
    def __init__(self, *, timeout=10000):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="報到請按我", style=discord.ButtonStyle.primary, custom_id="my_button")
    async def my_button_click(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        values = checkin.get_all_values()
        df = pd.DataFrame(values[0:], columns=values[0])
        end_row = df[df["已報到隊伍"].isin([""])].head(1).index.values[0]
        row = end_row + 1  #最後一欄

        checkin.update_value(f'A{row}', f'{interaction.user.display_name}')  

        await interaction.followup.send("報到成功", ephemeral=True)
# 報到用按鈕
class ConfirmationView(View):
    def __init__(self, team_name):
        super().__init__(timeout=60)  
        self.team_name = team_name
        self.value = None

    @discord.ui.button(label="是", style=discord.ButtonStyle.green)
    async def confirm(self, button: Button, interaction: discord.Interaction):
        self.value = True
        self.stop()
        await interaction.response.send_message(f"已成功退出比赛", ephemeral=True)

    @discord.ui.button(label="否", style=discord.ButtonStyle.grey)
    async def cancel(self, button: Button, interaction: discord.Interaction):
        self.value = False
        self.stop()
        await interaction.response.send_message("操作已取消", ephemeral=True)
# 報名用按鈕
class SignUpView(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(discord.ui.InputText(label="隊伍名稱", placeholder="請輸入隊伍名稱"))
        self.add_item(discord.ui.InputText(label="隊員1 DiscordID", placeholder="預設值，可修改"))
        self.add_item(discord.ui.InputText(label="隊員1 遊戲ID", placeholder="請輸入隊員1的遊戲ID"))
        self.add_item(discord.ui.InputText(label="隊員2 DiscordID", placeholder="請輸入隊員2的DiscordID"))
        self.add_item(discord.ui.InputText(label="隊員2 遊戲ID", placeholder="請輸入隊員2的遊戲ID"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        embed = discord.Embed(title="報名成功!", color=discord.Color.random())
        embed.add_field(name="請確認下方資訊是否有誤\n如有問題或是需要跟換隊員請通知官方人員", value="", inline=False)
        embed.add_field(name="隊伍名稱", value=self.children[0].value, inline=False)
        embed.add_field(name="隊員1 DiscordID", value=self.children[1].value, inline=False)
        embed.add_field(name="隊員1 遊戲ID", value=self.children[2].value, inline=False)
        embed.add_field(name="隊員2 DiscordID", value=self.children[3].value, inline=False)
        embed.add_field(name="隊員2 遊戲ID", value=self.children[4].value, inline=False)

        values = signupsheet.get_all_values()
        df = pd.DataFrame(values[0:], columns=values[0])
        end_row = df[df["隊伍名稱"].isin([""])].head(1).index.values[0]
        row = end_row + 1  #最後一欄

        signupsheet.update_value(f'A{row}', f'{self.children[0].value}')  
        signupsheet.update_value(f'B{row}', f'{self.children[1].value}') 
        signupsheet.update_value(f'C{row}', f'{self.children[2].value}')  
        signupsheet.update_value(f'D{row}', f'{self.children[3].value}')  
        signupsheet.update_value(f'E{row}', f'{self.children[4].value}') 
        signupsheet.update_value(f'F{row}', '參賽')   

        await interaction.followup.send(embeds=[embed], ephemeral=True)

def setup(bot):
    bot.add_cog(SignUp(bot))