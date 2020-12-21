import discord
from discord.ext import commands # Bot Commands Frameworkのインポート
import datetime
from .modules.reactionchannel import ReactionChannel
from .modules import settings
from .onmessagecog import OnMessageCog
import asyncio

# コグとして用いるクラスを定義。
class ReactionChannelerCog(commands.Cog, name="リアクションチャンネラー"):
    """
    リアクションチャンネラー機能のカテゴリ(リアクションをもとに実行するアクション含む)。
    """
    SPLIT_SIZE = 1900

    # ReactionChannelerCogクラスのコンストラクタ。Botを受取り、インスタンス変数として保持。
    def __init__(self, bot):
        self.bot = bot
        self.reaction_channel = None
        self.onmessagecog = None

    # cogが準備できたら読み込みする
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"load reaction-channeler's guilds{self.bot.guilds}")
        self.reaction_channel = ReactionChannel(self.bot.guilds, self.bot)
        self.onmessagecog = OnMessageCog(self.bot)

    # リアクションチャンネラーコマンド群
    @commands.group(aliases=['rch','reaction','reach'], description='リアクションチャンネラーを操作するコマンド（サブコマンド必須）')
    async def reactionChanneler(self, ctx):
        """
        リアクションチャンネラーを管理するコマンド群です。このコマンドだけでは管理できません。半角スペースの後、続けて以下のサブコマンドを入力ください。
        - リアクションチャンネラーを追加したい場合は、`add`を入力し、絵文字とチャンネル名を指定してください。
        - リアクションチャンネラーを削除したい場合は、`delete`を入力し、絵文字とチャンネル名を指定してください。
        - リアクションチャンネラーを**全て**削除したい場合は、`purge`を入力してください。
        - リアクションチャンネラーを確認したい場合は、`list`を入力してください。
        """
        # サブコマンドが指定されていない場合、メッセージを送信する。
        if ctx.invoked_subcommand is None:
            await ctx.send('このコマンドにはサブコマンドが必要です。')

    # リアクションチャンネラー追加
    @reactionChanneler.command(aliases=['a','ad'], description='リアクションチャンネラーを追加するサブコマンド')
    async def add(self, ctx, reaction:str=None, channel:str=None):
        """
        リアクションチャンネラー（＊）で反応する絵文字を追加します。
        ＊指定した絵文字でリアクションされた時、チャンネルに通知する機能のこと
        """
        # リアクション、チャンネルがない場合は実施不可
        if reaction is None or channel is None:
            await ctx.channel.purge(limit=1)
            await ctx.channel.send('リアクションとチャンネルを指定してください。\nあなたのコマンド：`{0}`'.format(ctx.message.clean_content))
            return
        msg = await self.reaction_channel.add(ctx, reaction, channel)
        await ctx.channel.send(msg)

    # リアクションチャンネラー確認
    @reactionChanneler.command(aliases=['l','ls','lst'], description='現在登録されているリアクションチャンネラーを確認するサブコマンド')
    async def list(self, ctx):
        """
        リアクションチャンネラー（＊）で反応する絵文字とチャンネルのリストを表示します。
        ＊指定した絵文字でリアクションされた時、チャンネルに通知する機能のこと
        """
        msg = await self.reaction_channel.list(ctx)
        await ctx.channel.send(msg)

    # リアクションチャンネラー全削除
    @reactionChanneler.command(aliases=['prg','pg'], description='Guildのリアクションチャンネラーを全削除するサブコマンド')
    async def purge(self, ctx):
        """
        リアクションチャンネラー（＊）で反応する絵文字を全て削除します。
        10秒以内に👌(ok_hand)のリアクションをつけないと実行されませんので、素早く対応ください。
        ＊指定した絵文字でリアクションされた時、チャンネルに通知する機能のこと
        """
        command_author = ctx.author
        # 念の為、確認する
        confirm_text = f'全てのリアクションチャンネラーを削除しますか？\n 問題ない場合、10秒以内に👌(ok_hand)のリアクションをつけてください。\nあなたのコマンド：`{ctx.message.clean_content}`'
        await ctx.channel.purge(limit=1)
        await ctx.channel.send(confirm_text)

        def check(reaction, user):
            return user == command_author and str(reaction.emoji) == '👌'

        # リアクション待ち
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
        except asyncio.TimeoutError:
            await ctx.channel.send('→リアクションがなかったのでキャンセルしました！')
        else:
            msg = await self.reaction_channel.purge(ctx)
            await ctx.channel.send(msg)

    # リアクションチャンネラー削除（１種類）
    @reactionChanneler.command(aliases=['d','del','dlt'], description='リアクションチャンネラーを削除するサブコマンド')
    async def delete(self, ctx, reaction:str=None, channel:str=None):
        """
        リアクションチャンネラー（＊）で反応する絵文字、チャンネルの組み合わせを削除します
        絵文字、チャンネルの記載が必須です。存在しない組み合わせを消す場合でもエラーにはなりません
        ＊指定した絵文字でリアクションされた時、チャンネルに通知する機能のこと
        """
        # リアクション、チャンネルがない場合は実施不可
        if reaction is None or channel is None:
            await ctx.channel.purge(limit=1)
            await ctx.channel.send('リアクションとチャンネルを指定してください。\nあなたのコマンド：`{0}`'.format(ctx.message.clean_content))
            return
        msg = await self.reaction_channel.delete(ctx, reaction, channel)
        await ctx.channel.send(msg)

    # リアクション追加時に実行されるイベントハンドラを定義
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        loop = asyncio.get_event_loop()
        if payload.member.bot:# BOTアカウントは無視する
            return
        if payload.emoji.name == '👌':# ok_handは確認に使っているので無視する(と思っていたが別機能として使用)
            await self.save_file(payload)
            return 
        await self.pin_message(payload)
        await self.reaction_channeler(payload)

    # リアクション削除時に実行されるイベントハンドラを定義
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot:# BOTアカウントは無視する
            return
        await self.unpin_message(payload)

    # ピン留めする非同期関数を定義
    async def pin_message(self, payload: discord.RawReactionActionEvent):
        # 絵文字が異なる場合は対応しない
        if (payload.emoji.name != '📌') and (payload.emoji.name != '📍'):
            return
        if (payload.emoji.name == '📌') or (payload.emoji.name == '📍'):
            guild = self.bot.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.pin()
            return

    # ピン留め解除する非同期関数を定義
    async def unpin_message(self, payload: discord.RawReactionActionEvent):
        # 絵文字が異なる場合は対応しない
        if (payload.emoji.name != '📌') and (payload.emoji.name != '📍'):
            return
        if (payload.emoji.name == '📌') or (payload.emoji.name == '📍'):
            guild = self.bot.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.unpin()
            return

    # リアクションをもとにチャンネルへ投稿する非同期関数を定義
    async def reaction_channeler(self, payload: discord.RawReactionActionEvent):
        # リアクションチャンネラーを読み込む
        guild = self.bot.get_guild(payload.guild_id)
        await self.reaction_channel.set_rc(guild)

        # リアクションから絵文字を取り出す（ギルド絵文字への変換も行う）
        emoji = payload.emoji.name
        if payload.emoji.id is not None:
            emoji = f'<:{payload.emoji.name}:{payload.emoji.id}>'

        # 入力された絵文字でフィルターされたリストを生成する
        filtered_list = [rc for rc in self.reaction_channel.guild_reaction_channels if emoji in rc]

        if settings.IS_DEBUG:
            print(f'*****emoji***** {emoji}')

        # フィルターされたリストがある分だけ、チャンネルへ投稿する
        for reaction in filtered_list:
            from_channel = guild.get_channel(payload.channel_id)
            message = await from_channel.fetch_message(payload.message_id)

            if settings.IS_DEBUG:
                print('guild:'+ str(guild))
                print('from_channel: '+ str(from_channel))
                print('message: ' + str(message))

            # 設定によって、すでに登録されたリアクションは無視する
            if settings.FIRST_REACTION_CHECK:
                if settings.IS_DEBUG:
                    print('reactions:'+ str(message.reactions))
                    print('reactions_type_count:'+ str(len(message.reactions)))
                for message_reaction in message.reactions:
                    if emoji == str(message_reaction) and message_reaction.count > 1:
                        if settings.IS_DEBUG:
                            print('Already reaction added. emoji_count:'+ str(message_reaction.count))
                        return

            contents = [message.clean_content[i: i+200] for i in range(0, len(message.clean_content), 200)]
            if len(contents) != 1 :
                contents[0] += ' ＊長いので分割しました＊'
            embed = discord.Embed(title = contents[0], description = '<#' + str(message.channel.id) + '>', type='rich')
            embed.set_author(name=reaction[0] + ' :reaction_channeler', url='https://github.com/tetsuya-ki/discord-bot-heroku/')
            embed.set_thumbnail(url=message.author.avatar_url)

            created_at = message.created_at.replace(tzinfo=datetime.timezone.utc)
            created_at_jst = created_at.astimezone(datetime.timezone(datetime.timedelta(hours=9)))

            embed.add_field(name='作成日時', value=created_at_jst.strftime('%Y/%m/%d(%a) %H:%M:%S'))

            if len(contents) != 1 :
                for addText in contents[1:]:
                    embed.add_field(name='addText', value=addText + ' ＊長いので分割しました＊', inline=False)

            to_channel = guild.get_channel(int(reaction[2]))
            if settings.IS_DEBUG:
                print('setting:'+str(reaction[2]))
                print('to_channel: '+str(to_channel))

            await to_channel.send(reaction[1] + ': ' + message.jump_url, embed=embed)

    # 画像を保存
    async def save_file(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await self.onmessagecog.save_message_file(message)

# Bot本体側からコグを読み込む際に呼び出される関数。
def setup(bot):
    bot.add_cog(ReactionChannelerCog(bot)) # ReactionChannelerCogにBotを渡してインスタンス化し、Botにコグとして登録する