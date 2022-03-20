import discord
from discord.ext import commands
from discord.ext import tasks
import os
import traceback
import datetime


prefix = os.getenv('DISCORD_BOT_PREFIX', default='>')
lang = os.getenv('DISCORD_BOT_LANG', default='ja')
token = os.environ['DISCORD_BOT_TOKEN']
intents = discord.Intents.all()
client = commands.Bot(command_prefix=prefix, intents=intents)
boshuData = []
memberData = []
remaindData = []


@client.event
async def on_ready():
    print('ready.')
    await client.change_presence(activity=discord.Game(name=f'{prefix}hでコマンド一覧', type=1))


# 60秒に一回ループ
@tasks.loop(seconds=60)
async def loop():
    global boshuData
    global memberData
    global remaindData
    text = ''
    counter = 0

    # 現在の時刻
    now = datetime.datetime.now().strftime('%H:%M')

    # リマインド時間だった場合、募集名を格納
    for remaind in remaindData:
        if now == remaind[1]:
            boshuName = remaind[0]

            # 募集名から参加者を取得
            for memdata in memberData:
                if boshuName == memdata[0]:
                    member = memdata

            # 通知用のテキストを作成
            for mem in member[1:(len(member) + 1)]:
                text = text + f"{mem.mention} "
            text = text + "\n" + boshuName + "の開始まで5分前です。"
            channel = client.get_channel(840436328930869278)
            await channel.send(text)

    # 指定時刻でリマインド
    for boshu in boshuData:
        if now == boshu[1]:
            boshuName = boshu[0]

            # 募集名から参加者を取得
            for memdata in memberData:
                if boshuName == memdata[0]:
                    member = memdata

            # 通知用のテキストを作成
            for mem in member[1:(len(member) + 1)]:
                text = text + f"{mem.mention} "
            text = text + "\n" + boshuName + "の開始時刻になりました。"
            channel = client.get_channel(840436328930869278)
            await channel.send(text)

            del boshuData[counter]
            del memberData[counter]
            del remaindData[counter]

        counter = counter + 1


@client.command()
async def rec(ctx, name, time, amount):
    global boshuData
    global memberData
    global remaindData
    registData = []
    member = []
    remaind = []
    existFlg = False

    # 引数のフォーマットチェック
    dte = datetime.datetime.strptime(time, '%H%M').strftime('%H:%M')
    if not amount.isdigit():
        raise commands.CommandError("not number format.")

    # 募集の存在チェック
    for memdata in memberData:
        if name == memdata[0]:
            existFlg = True
            break

    # リマインド時刻の設定
    dt = datetime.datetime.strptime(time, '%H%M')
    dt2 = dt + datetime.timedelta(minutes=-5)
    dt2 = dt2.strftime('%H:%M')

    if not existFlg:
        # 募集データの登録
        registData.append(name)
        registData.append(dte)
        registData.append(amount)
        boshuData.append(registData)
        member.append(name)
        member.append(ctx.author)
        memberData.append(member)
        remaind.append(name)
        remaind.append(dt2)
        remaindData.append(remaind)

        # アナウンス
        embed = discord.Embed(title="募集を受け付けました。", color=0xff9900)
        embed.add_field(name="募集名", value=name, inline=False)
        embed.add_field(name="期限", value=dte, inline=False)
        embed.add_field(name="人数上限", value=amount, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(name + "は既に存在する募集です。\n名前を変更してください。")


@client.command()
async def join(ctx, name):
    global memberData
    existFlg = False
    joinFlg = False
    member = []
    counter = 0

    # 募集が存在するかチェック
    for memdata in memberData:
        if name == memdata[0]:
            existFlg = True
            member = memdata
            break
        counter = counter + 1

    # 募集に参加しているかチェック
    for mem in member:
        if ctx.author == mem:
            joinFlg = True
            break

    if not existFlg:
        await ctx.send(name + "は存在しない募集です。")
    elif joinFlg:
        await ctx.send("既に" + name + "に参加しています。")
    else:
        # 募集人数が超過しているかチェック
        for boshu in boshuData:
            if name == boshu[0]:
                if len(member) - 2 < int(boshu[2]):
                    member.append(ctx.author)
                    memberData[counter] = member
                    if len(member) - 2 == int(boshu[2]):
                        await ctx.send(name + "に参加しました。参加上限のため締め切ります。(" + str(len(member) - 2) + "/" + boshu[2] + ")")
                    else:
                        await ctx.send(name + "に参加しました。(" + str(len(member) - 2) + "/" + boshu[2] + ")")
                else:
                    await ctx.send(name + "は募集上限に達しています。")


@client.command()
async def can(ctx, name):
    global boshuData
    global memberData
    global remaindData
    existFlg = False
    ownerFlg = False
    guestFlg = False
    counter = 0
    member = []

    # 募集が存在するかチェック
    for memdata in memberData:
        if name == memdata[0]:
            member = memdata
            existFlg = True
            break
        counter = counter + 1

    if not existFlg:
        await ctx.send(name + "は存在しない募集です。")
    else:
        # 募集主かどうかチェック
        if ctx.author == member[1]:
            ownerFlg = True

        # ゲストかどうかチェック
        for mem in member[2:(len(member) + 1)]:
            if ctx.author == mem:
                guestFlg = True
                break

        if ownerFlg:
            # 募集を削除
            del boshuData[counter]
            del memberData[counter]
            del remaindData[counter]
            await ctx.send(name + "を募集一覧から削除しました。")
        elif guestFlg:
            # 募集への参加を削除
            memberData[counter].remove(ctx.author)
            await ctx.send(name + "への参加をキャンセルしました。")
        else:
            # 募集に参加していないことを伝える
            await ctx.send(name + "に参加していません。")


@client.command()
async def dl(ctx, name):
    global boshuData
    global memberData
    existFlg = False
    ownerFlg = False
    counter = 0
    boshudata = []

    # 募集が存在するかチェック
    for boshu in boshuData:
        if name == boshu[0]:
            boshudata = boshu
            existFlg = True
            break
        counter = counter + 1

    if not existFlg:
        await ctx.send(name + "は存在しない募集です。")
    else:
        # 募集主かどうかチェック
        if ctx.author == boshudata[1]:
            ownerFlg = True

        # 手動締め切り
        if ownerFlg:
            amount = len(memberData[counter]) - 2
            boshudata[2] = amount
            boshuData[counter] = boshudata
            await ctx.send(name + "の募集を締め切ります。")
        else:
            await ctx.send("手動締め切りは募集主のみ可能です。")


@client.command()
async def show(ctx):
    couter = 0

    if len(boshuData) == 0:
        await ctx.send("現在受付中の募集はありません。")
    else:
        embed = discord.Embed(title="募集一覧です。", color=0xff9900)
        for boshu in boshuData:
            val = boshu[1] + "まで, 現在募集人数：" + str(len(memberData[couter]) - 2) + "/" + boshu[2]
            embed.add_field(name=boshu[0], value=val, inline=False)
        await ctx.send(embed=embed)


@client.command()
async def h(ctx):
    message = f'''◆◇◆{client.user.name}の使い方◆◇◆
{prefix}＋コマンドで命令できます。
{prefix}rec 募集名 時間（HHMM）募集人数 ：指定内容で募集を受け付けます。
{prefix}join 募集名：指定の募集に参加します。
{prefix}can 募集名：募集主の場合、募集を削除します。ゲスト参加の場合、参加を解除します。
{prefix}dl 募集名：現在の人数で募集を締め切ります。募集主のみ可能の操作です。
{prefix}show：現在募集中の一覧を表示します。
不具合、要望があればサバの味噌煮まで'''
    await ctx.send(message)


@client.event
async def on_command_error(ctx, error):
    '''
    if isinstance(error, commands.CommandError):
        await ctx.send('引数が不正です。')
    el
    '''
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send('存在しないコマンドです。')
    elif isinstance(error, ValueError):
        await ctx.send('時間の形式に不正があります。\nHHMMで入力してください。')
    else:
        orig_error = getattr(error, 'original', error)
        error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
        await ctx.send(error_msg)

# loop start
loop.start()

client.run(token)
