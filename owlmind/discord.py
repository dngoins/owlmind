##
## OwlMind - Platform for Education and Experimentation with Hybrid Intelligent Systems
## discord.py :: Bot Runner for Discord
##
#  
# Copyright (c) 2024, The Generative Intelligence Lab @ FAU
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# Documentation and Getting Started:
#    https://github.com/genilab-fau/owlmind
#
# Disclaimer: 
# Generative AI has been used extensively while developing this package.
# 

import re
import discord
import datetime
from discord.ext import commands
from .bot import BotMessage, BotEngine
from .botcommands import BotCommands

class DiscordBot(commands.Bot):
    """
    DiscordBot provides logic to connect the Discord Runner with OwlMind's BotMind, 
    forming a multi-layered context in BotMessage by collecting elements of the Discord conversation
    (layer1=user, layer2=thread, layer3=channel, layer4=guild), and aggregating attachments, reactions, and other elements.

    @EXAMPLE
    How to use this class:

    engine = MyBotEngine(.) 
    TOKEN = {My Token}
    bot = DiscordBot(token=TOKEN, engine=MyBotMind, debug=True)
    bot.run()
    """
    def __init__(self, token, engine:BotEngine, promiscuous:bool=False, debug:bool=False):
        self.token = token
        self.promiscuous = promiscuous
        self.debug = debug
        self.engine = engine
        self.registered_bots = []

        if self.engine: self.engine.debug = debug

        ## Discord attributes
        intents = discord.Intents.all()
        intents.messages = True
        intents.message_content = True
        intents.reactions = True
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        # Initialize the commands.Bot parent class
        super().__init__(command_prefix='!', intents=intents)
        self.pipeline = Pipeline(self)

    async def setup_hook(self):
        await super().setup_hook()
        self.bot_commands = BotCommands(self)
        await self.add_cog(self.bot_commands)
        await self.add_cog(self.pipeline)
        
        
    # When getting bots, you can filter by online status
    async def get_bots(self, context):
        bots = [member for member in context.guild.members 
                if member.bot and member.status != discord.Status.offline 
                and member.name != self.user.name]
        return bots

    # Or to check a specific bot's status
    def is_bot_online(self, bot):
        return bot.status != discord.Status.offline
    
    async def on_ready(self):
        print(f'Bot is running as: {self.user.name}.')
        print(f'Registered commands: {[command.name for command in self.commands]}')  
        # Add this line
       
        if self.debug: print(f'Debug is on!')
        if self.engine: 
            print(f'Bot is connected to {self.engine.__class__.__name__}({self.engine.id}).') 
            if self.engine.announcement: print(self.engine.announcement)
            self.engine.debug = self.debug
        
    async def on_message(self, message):

        # Don't process our own messages first
        if message.author == self.user:
            return

        # Process commands first
        await self.process_commands(message)  
        
        #if len(self.registered_bots) == 0:
        self.registered_bots = await self.get_bots(message)
            #print(f"Registered bots: {self.registered_bots}")

        # CUT-SHORT conditions
        # Only process if message does not come from itself, the bot is configured as promiscuous, or this is a DM or mentions the bot
         # Only then check promiscuous mode and other conditions for non-command messages
        if not self.promiscuous and not (self.user in message.mentions or isinstance(message.channel, discord.DMChannel)):
            if self.debug: print(f'IGNORING: orig={message.author.name}, dest={self.user}') 
            return
        
        
        # Remove calling @Mention if in the message
        text = re.sub(r"<@\d+>", "", message.content,).strip()

        # Collect attachments, reactions and others.
        attachments = [attachment.url for attachment in message.attachments]
        reactions = [str(reaction.emoji) for reaction in message.reactions]

        #get channel bots

        # Create context
        context = BotMessage(
                layer1       = message.guild.id if message.guild else 0,
                layer2       = message.channel.id if hasattr(message.channel, 'id') else 0,
                layer3       = message.channel.id if isinstance(message.channel, discord.Thread) else 0,
                layer4       = message.author.id,
                server_name  = message.guild.name if message.guild else '#dm',
                channel_name    = message.channel.name if hasattr(message.channel, 'name') else '#dm',
                thread_name     = message.channel.name if isinstance(message.channel, discord.Thread) else '',
                author_name     = message.author.name,
                author_fullname = message.author.global_name,
                author          = message.author.global_name,
                bot             = self.user,
                timestamp=datetime.datetime.now(),
                date=datetime.datetime.now().strftime("%d-%b-%Y"),  # Format date as '25-Feb-2024'
                time=datetime.datetime.now().strftime("%H:%M:%S"),  # Format time as '20:58:14'
                message         = text,
                attachments     = attachments,
                reactions       = reactions,
                discord_context = message,
                bots = self.registered_bots)

        if self.debug: print(f'PROCESSING: ctx={context}')
        await message.channel.send("One moment please, I'm thinking...")                      
        
        # Process through engine
        if self.engine:
            await self.engine.process(context)
            await message.channel.send("Processing...")                      
        
        # If the immediate processing of Context generated a result (sync mode), return it through the bot interface
        # @TODO return attachments, issue reactions, etc
        if context.response:
            if len(context.response) > 1900:
                # Calculate number of chunks needed
                chunk_size = 1900  # Using 1900 to leave some buffer
                chunks = [context.response[i:i + chunk_size] 
                        for i in range(0, len(context.response), chunk_size)]
                
                # Send each chunk
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(context.response)
        return

    async def on_error(event, *args, **kwargs):
        with open('err.log', 'a') as f:
            if event == 'on_message':
                f.write(f'Unhandled message: {args[0]}\n')
            else:
                raise

    def run(self):
        super().run(self.token)

   
class Pipeline(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
   
    async def process_message(self, message):
        # Create BotMessage instance with message details
        bot_message = BotMessage(
            layer1=message.guild.id if message.guild else 0,
            layer2=message.channel.id,
            layer3=message.thread.id if hasattr(message, 'thread') and message.thread else 0,
            layer4=message.author.id,
            server_name=message.guild.name if message.guild else '#dm',
            channel_name=message.channel.name,
            thread_name=message.thread.name if hasattr(message, 'thread') and message.thread else '',
            author_name=message.author.name,
            author_fullname=message.author.global_name,
            message=message.content,
            attachments=message.attachments,
            reactions=message.reactions
        )

        # Check if message author is a bot
        if message.author.bot:
            print(f"Message from bot: {message.author.name}")
            # Handle bot message differently if needed
            
            # You could also track this in a database or send a notification
           # await message.channel.send(f"{message.author.name} " + message.content)
            return
