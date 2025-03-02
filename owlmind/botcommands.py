
from .agent import Agent, Plan
from .context import Context
import discord
from discord.ext import commands

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    @commands.command()
    async def list_bots(self, ctx):
        try:
            print("list bots")
            # Get all members in the server
            bots = [member for member in ctx.guild.members if member.bot]
            # users = [member for member in ctx.guild.members if not member.bot]

            # if member.bot and member.status != discord.Status.offline 
            # Format the response
            response = f"Bots ({len(bots)}):\n"
            for bot in bots:
                #response += f"- {bot.name}\n"
                # 🤖💡🔋⚡
                response += f"🤖"
                if bot.status == discord.Status.online:
                    response += "💡"

                if bot.activity:
                    response += f"⚡{bot.name} (ID: {bot.id}) - status: {bot.status} - {bot.activity.name}\n"
                else:
                    response += f"{bot.name} (ID: {bot.id}) - status: {bot.status} - no activity\n" 
        
            # Split message if it's too long
            if len(response) > 1900:
                await ctx.send(response[:1900])
                await ctx.send(response[1900:])
            else:
                await ctx.send(response)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            print(f"Error in list_bots: {e}")

    @commands.command()
    async def is_bot(self, ctx, *, member_name):
        try:
            member = discord.utils.get(ctx.guild.members, name=member_name)
            if member is None:
                await ctx.send(f"Couldn't find user {member_name}")
                return
                
            if member.bot:
                await ctx.send(f"{member.name} is a bot")
            else:
                await ctx.send(f"{member.name} is a human user")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"BotCommands ready")
        

   
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print(f"BotCommand error: {error}")

    @commands.command()
    async def reset_chat(self, ctx):
        """Reset the chat history"""
        self.bot.engine.model_provider.reset_session()
        await ctx.send("Chat history has been reset!")

    @commands.command()
    async def show_history(self, ctx):
        """Show the current chat history"""
        history = self.bot.engine.model_provider.session_history
        formatted_history = "Chat History:\n"
        for msg in history:
            formatted_history += f"{msg['role']}: {msg['content'][:100]}...\n"
        await ctx.send(formatted_history)

    @commands.command()
    async def reset_conversation(self, ctx):
        """Reset the conversation for the current channel"""
        if self.bot.engine.model_provider:
            self.bot.engine.model_provider.reset_session()
            await ctx.send("Conversation history has been reset for this channel!")

    @commands.command()
    async def show_conversation(self, ctx):
        """Show the current conversation history"""
        if self.bot.engine.model_provider and self.bot.engine.model_provider.session_history:
            history = "Current conversation history:\n"
            for msg in self.bot.engine.model_provider.session_history:
                role = msg['role']
                content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                history += f"{role}: {content}\n"
            await ctx.send(history)
        else:
            await ctx.send("No conversation history available.")


