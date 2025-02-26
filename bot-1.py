##
## OwlMind - Platform for Education and Experimentation with Generative Intelligent Systems
## bot-1.py :: Getting Started with simple HybridAI-based Discord Bot
## 
#  
# Copyright (c) 2024 The Generative Intelligence Lab @ FAU
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
# Class Documentation at:
#    https://github.com/genilab-fau/owlmind/bot-1.md
#
# Disclaimer: 
# Generative AI has been used extensively while developing this package.
# 
import os
from dotenv import load_dotenv, find_dotenv
from owlmind.pipeline import ModelProvider
from owlmind.simple import SimpleEngine
from owlmind.discord import DiscordBot
    
if __name__ == '__main__':

    # Check if .env file exists and load it
    dotenv_path = find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path)
    
    # Load environment variables, falling back to os.getenv if not found in .env
    TOKEN = os.getenv('DISCORD_TOKEN')
    URL = os.getenv('SERVER_URL')
    MODEL = os.getenv('SERVER_MODEL')
    TYPE = os.getenv('SERVER_TYPE')
    API_KEY = os.getenv('SERVER_API_KEY')
    
    #OPENAPI_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    #OPENAPI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    #MODEL_NAME=os.getenv('MODULE_DEPLOYMENT_NAME')

    print(f"TOKEN: {TOKEN}")
    print(f"URL: {URL}")
    print(f"MODEL: {MODEL}")
    print(f"TYPE: {TYPE}")
    print(f"API_KEY: {API_KEY}")
    
    # openai_client = ChatCompletionsClient(
    # endpoint=OPENAPI_ENDPOINT,
    # credential=DefaultAzureCredential(),
    # )

    # response = openai_client.complete(
    #     messages=[
    #         SystemMessage(content="You are a helpful assistant."),
    #         UserMessage(content="I am going to Paris, what should I see?"),
    #     ],
    #     max_tokens=4096,
    #     temperature=1.0,
    #     top_p=1.0,
    #     model=MODEL_NAME
    # )

    # print(response.choices[0].message.content)
    
    # openai_client = AzureOpenAI(
    #     api_key=OPENAPI_KEY,  
    #     api_version="2024-02-01",
    #     azure_endpoint = OPENAPI_ENDPOINT
    #     )
        
    # deployment_name=MODEL_NAME #This will correspond to the custom name you chose for your deployment when you deployed a model. Use a gpt-35-turbo-instruct deployment. 
        
    # # Send a completion call to generate an answer
    # print('Sending a test completion job')
    # start_phrase = 'Write a tagline for an ice cream shop. '
    # response = openai_client.completions.create(model=deployment_name, prompt=start_phrase, max_tokens=10)
    # print(start_phrase+response.choices[0].text)

    # Configure a ModelProvider if there is an URL
    provider = ModelProvider(type=TYPE,  base_url=URL, api_key=API_KEY, model=MODEL) if URL else None

    # Load Simples Bot Brain loading rules from a CSV
    engine = SimpleEngine(id='llm-search')
    engine.model_provider = provider
    engine.load('rules/bot-req-rules.csv')
    
    # Kick start the Bot Runner process
    bot = DiscordBot(token=TOKEN, engine=engine, debug=True)
    bot.run()

