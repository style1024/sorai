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

signupsheet = sheet[0]
checkin = sheet[1]

class SignUp(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description='報名參加比賽')
    async def 報名(self, ctx, 隊長r6id: str, 隊員dcid: discord.Member, 隊員r6id: str, 隊名: str):
        隊長dcid = ctx.author
        await ctx.defer(ephemeral=True)

        ## Google Sheet 
        values = signupsheet.get_all_values()
        df = pd.DataFrame(values[1:], columns=values[0])
        end_row = df[df["隊伍名稱"].isin([""])].head(1).index.values[0]
        row = end_row + 2  #最後一欄

        ## 確認是否有重複報名
        if 隊長dcid == 隊員dcid:
            await ctx.followup.send(f"隊長ID會自動抓取，不用輸入自己的DCID，只需提供另一隊隊友的DCID即可", ephemeral=True)
            return
        
        ## 確認是否有重複報名
        if len(signupsheet.find(隊長dcid.name)) != 0:
            await ctx.followup.send(f"<@{隊長dcid.id}> 重複報名，請確認隊伍名單，如有問題起聯絡管理員", ephemeral=True)
            return

        if len(signupsheet.find(隊員dcid.name)) != 0:
            await ctx.followup.send(f"<@{隊員dcid.id}> 重複報名，請確認隊伍名單，如有問題起聯絡管理員", ephemeral=True)
            return

        ## 隊名是否有重複
        if 隊名 in df['隊伍名稱'].values:
            await ctx.followup.send("隊名已存在，請選擇其他隊名，如有問題起聯絡管理員。", ephemeral=True)
            return

        ## 創建隊伍身分組
        team_role = await ctx.guild.create_role(name=隊名, color=discord.Color.dark_grey())
        await 隊長dcid.add_roles(team_role)
        await 隊員dcid.add_roles(team_role)

        ## 提供身分組給隊長
        leader_role = ctx.guild.get_role(1230786345291616292)
        await 隊長dcid.add_roles(leader_role)

        ## 修改報名人名稱
        await 隊長dcid.edit(nick=隊長r6id)
        await 隊員dcid.edit(nick=隊員r6id)

        ## 寫進Google Sheet
        signupsheet.update_value(f'A{row}', f'{隊名}')  
        signupsheet.update_value(f'B{row}', f'{隊長dcid.name}') 
        signupsheet.update_value(f'C{row}', f'{隊長r6id}')  
        signupsheet.update_value(f'D{row}', f'{隊員dcid.name}')  
        signupsheet.update_value(f'E{row}', f'{隊員r6id}') 
        signupsheet.update_value(f'F{row}', '參賽')   

        embed = discord.Embed(title="報名成功!", color=discord.Color.random())
        embed.add_field(name="請確認下方資訊是否有誤\n如有問題或是需要跟換隊員請通知官方人員", value="", inline=False)
        embed.add_field(name="隊伍名稱", value=隊名, inline=False)
        embed.add_field(name="隊長 DiscordID", value=隊長dcid.name, inline=False)
        embed.add_field(name="隊長 遊戲ID", value=隊長r6id, inline=False)
        embed.add_field(name="隊員2 DiscordID", value=隊員dcid.name, inline=False)
        embed.add_field(name="隊員2 遊戲ID", value=隊員r6id, inline=False)

        await ctx.followup.send(embeds=[embed], ephemeral=True)

    @commands.slash_command()
    async def 報到(self, ctx):
        embed = discord.Embed(title="報到按鈕", description="這是一個Embed帶有按鈕", color=discord.Color.blue())
        view = CheckInView()
        await ctx.respond(embed=embed, view=view)

    @commands.slash_command()
    async def 取消參賽(self, ctx):
        await ctx.defer(ephemeral=True)

        ## Google Sheet
        values = signupsheet.get_all_values()

        ## 隊長身分組
        role = ctx.guild.get_role(1230786345291616292)
        member = ctx.author

        # 檢查是否有角色
        if role in member.roles:
            embed = discord.Embed(title="確認退出比赛", description=f"您確定要退出比賽嗎？", color=discord.Color.red())
            view = ConfirmationView()
            await ctx.respond(embed=embed, view=view, ephemeral=True)
            await view.wait()
            if view.value is True:
                df = pd.DataFrame(values[1:], columns=values[0]) 

                # 找到需要更新的行
                row = signupsheet.find(ctx.author.name)[0].row

                # 更新 Google Sheet 中的行
                signupsheet.update_value(f'F{row}', '取消')   
                team_role_value = signupsheet.get_value(f'A{row}')
                team_role = discord.utils.get(ctx.guild.roles, name=team_role_value)
                await team_role.delete()
                await member.remove_roles(role)
                await ctx.respond("您已成功退出比赛。", ephemeral=True)

            elif view.value is False:
                await ctx.respond("操作已取消。", ephemeral=True)

            else:
                await ctx.respond("超過時間，操作結束。", ephemeral=True)
        else:
            await ctx.respond("你不是隊長無法操作這個動作", ephemeral=True)

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

# 取消參賽用按鈕
class ConfirmationView(View):
    def __init__(self):
        super().__init__(timeout=60)  
        self.value = None

    @discord.ui.button(label="是", style=discord.ButtonStyle.green)
    async def confirm(self, button: Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="否", style=discord.ButtonStyle.grey)
    async def cancel(self, button: Button, interaction: discord.Interaction):
        self.value = False
        self.stop()

def setup(bot):
    bot.add_cog(SignUp(bot))
