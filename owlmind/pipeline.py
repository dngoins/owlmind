##
## OwlMind - Platform for Education and Experimentation with Hybrid Intelligent Systems
## pipeline.py :: Pipeline for GenAI System
## 
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

import requests
import json
from urllib.parse import urljoin
import time


class ModelRequestMaker():

    def url_models(self, url):
        raise(f'!!ERROR!! url_models() must be overload')

    def url_chat(self, url):
        raise(f'!!ERROR!! url_chat() must be overload')
    
    def package(self, prompt, model, **kwargs):
        raise(f'!!ERROR!! package() must be overload')

    def unpackage(self, response):
        raise(f'!!ERROR!! unpackage() must be overload')

class OllamaRequest(ModelRequestMaker):
    
    def url_chat(self, url):
        return urljoin(url, '/api/generate')
    
    def package(self, model, prompt, **kwargs):
        payload = {
            "model": model, 
            "prompt": prompt, 
            "stream": False,
        }

        # Load kwargs into payload.options
        if kwargs:
            payload["options"] = {key: value for key, value in kwargs.items()}
        return payload
    
    def unpackage(self, response):
        return response['response'] if 'response' in response else None


class OpenWebUIRequest(ModelRequestMaker):
    def url_chat(self, url):
        return urljoin(url, '/api/chat/completions')
    
    def package(self, model, prompt, **kwargs):
        payload = {
            "model": model if model else self.model, 
            "messages": [ {"role" : "user", "content": prompt } ]
        }

        # @NOTE: Need to find out the right syntax to load the arguments here!
        #kwargs = {key: value for key, value in self.__dict__}
        #if kwargs:
        #   payload["options"] = {key: value for key, value in kwargs.items()}
        return payload
    
    def unpackage(self, response):
        return response['choices'][0]['message']['content'] if 'choices' in response else None


###
### MODEL PROVIDER
### 

class ModelProvider():
    def __init__(self, base_url, type=None, api_key=None, model=None):
        self.base_url = base_url
        self.api_key = api_key
        self.type = None
        self.model = model
        self.req_maker = None
        self.delta = -1
        self.response = None
        self.models = None
        self.model_names =[]
        self.eval_model = None
        self.template_before = ''
        self.template_after = ''
        self.prompt = ''
        self.reason = ''

        if type == 'ollama':
            self.req_maker = OllamaRequest()
            self.type = 'ollama'
        elif type == 'open-webui':
            self.req_maker = OpenWebUIRequest()
            self.type = 'open-webui'
        
        self.models = self.list_models()
#        print(self.models)

        hasId = False
        if 'model' in self.models[0]:
            self.model_names = [model['model'] for model in self.models]
        else:
            hasId = True
            self.model_names = [model['id'] for model in self.models]
            
        self.eval_model = self.evaluate_models(self.models)

        if hasId:
            self.eval_model = self.eval_model['id']
        else:
            self.eval_model = self.eval_model['model']

        self.template_before = f'You are an agent that searches for LLMs and selects the best LLM based on its description, parameter size, speed, and knowledge base. Only select from the model names: {self.model_names}. Based on the parameter size, {self.eval_model} is the best model, but choose another if its description better matches the prompt. As an agent, you also create LLM prompts for the selected LLM. When you select the LLM provide a detailed explanation of why you selected that LLM. Explain the strengths and weaknesses of the LLM and how it compares to other LLMs.'    
        
        self.template_after = 'Only return the name of the LLM and corresponding prompt, nothing else, no metadata, no header, no comments, no dashes, ONLY THE LLM Name and PROMPT. In the returned prompt, make sure to say to limit the response to 1990 characters or less. Use the following format: {"model": "GPT-4:latest", "prompt": "LLM Prompt", "reason": "GPT uses a fast and efficient model that is able to generate text quickly and accurately on the most widely used topics dealing with science"}'
        
        return

    def _call(self, url, payload=None):
        """
        Issue the HTTP-Request to the Model Provider
        """
        headers = dict()
        headers["Content-Type"] = "application/json"
        if self.api_key: 
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            start_time = time.time()
            response = requests.post(url=url, data=payload, headers=headers)
            delta = time.time() - start_time
        except:
            return -1, f"!!ERROR!! Request failed! You need to adjust .env with URL({self.base_url})"
        
        return delta, response

    def list_models(self):
                
        headers = dict()
        headers["Content-Type"] = "application/json"
        if self.api_key: headers["Authorization"] = f"Bearer {self.api_key}"

        # Send out request to Model Provider
        try:
            hasFauedu = False
            if 'fau.edu' in self.base_url:
                hasFauedu = True
                response = requests.get(f'{self.base_url}/api/models', headers=headers)
            else:
                response = requests.get(f'{self.base_url}/api/tags', headers=headers)
            
            models = response.json()
            if hasFauedu:
                models = models["data"]
            else:
                models = models["models"]
            
            # the models json looks like this: 
                    
        except:
            return -1, f"!!ERROR!! Request failed! You need to adjust prompt-eng/config with URL({self.base_url})"

        # Checking the response and extracting the 'response' field
        if response is None:
            return -1, f"!!ERROR!! There was no response (?)"
        elif response.status_code == 200:
            return models
    
    def extractParameterSize(self, parameter_size):
        if parameter_size.endswith("M"):
            return float(parameter_size[:-1])
        elif parameter_size.endswith("B"):
            return float(parameter_size[:-1]) * 1000


    def evaluate_models(self, models):
        best_model = None
        best_score = float('-inf')
        
        for model in models:
            
            if 'info' in model:
                description = model['info']['meta']['description']
                examples = model['info']['meta']['suggestion_prompts']
            
            # Example evaluation logic: prioritize models with higher parameter count
            if 'ollama' in model:
                score = self.extractParameterSize(model['ollama']['details']['parameter_size'])
            elif 'details' in model:
                score = self.extractParameterSize(model['details']['parameter_size'])
            else:
                score = 0
        
            if score > best_score:
                best_score = score
                best_model = model
        
        return best_model

    def models(self):
        """
        Issue request about Models Available
        """
        url = self.req_maker.url_models(base_url=self.url)
        return self._call(url=url)


    def request(self, prompt, **kwargs):
        """
        Execute the logic for request/response to a Model Provider.
        Creates the payload, issues the Request to the target Model provider.
        Unpackage the response, it any
        """

        ## (1) Creates the payload through the ModelRequestMaker
        url = self.req_maker.url_chat(self.base_url)
        self.prompt = self.template_before + '\n' + prompt + '\n' + self.template_after
        payload = self.req_maker.package(model=self.model, prompt=self.prompt, **kwargs)
        payload = json.dumps(payload) if payload else None

        ## (2) Creates the HTTP-Req
        delta, response = self._call(url=url, payload=payload)
        
        # first remove the 'json' prefix from the response
        #response = response.replace('json', '')

        # now remove the ``` from the response
        #response = response.replace('```', '')  

        print('Response->', url, response.json())
        
        # extract the Model name from the Json formatted response. The response looks like this 'json{"model": "LLM Name", "prompt": "LLM Prompt"}'
        if response:
            try:
                json_response = json.loads(response.json()['choices'][0]['message']['content'])
                self.eval_model = json_response['model']
                self.prompt = json_response['prompt'] + '\nStrong Emphasis: Limit the response to less than 1990 characters. This is a requirement.'
                self.reason = json_response['reason']
               
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                print(f"Response content: {response}")
            
        payload = self.req_maker.package(model=self.eval_model, prompt=self.prompt, **kwargs)
        payload = json.dumps(payload) if payload else None

        print('P->', url, payload)

        ## (2) Creates the HTTP-Req
        delta, response = self._call(url=url, payload=payload)
      
        # (3) Load the results
        if response is None:
            self.delta = -1
            self.response = None
            self.result = "!!ERROR!! There was no response (?)"
        elif isinstance(response,str):
            self.delta = -1
            self.response = None
            self.result = response
            print('\nFinalResponse->\n', url, response)
        elif response.status_code == 401:
            self.delta = -1
            self.response = None
            self.result = f"!!ERROR!! Authentication issue. You need to adjust .env with API_KEY ({self.base_url})"
        elif response.status_code == 200:
            self.delta = round(delta, 3)
            self.response = response.json()
            print('\nFinalResponse->\n', url, response.json())
            self.result = self.req_maker.unpackage(self.response)
            
        else: 
            self.delta = -1
            self.response = None
            if response.text == '{"detail":"Model not found"}':
                self.result = f"!!ERROR!! {self.eval_model} not found.\n {self.reason}\nIt's possible this model is not available or loaded in Ollama, sorry."
            else:
                self.result = f"!!ERROR!! HTTP Response={response.status_code}, {response.text}"
        
        print('\nResult->', self.result)
        return self.result 


##
## DEBUG
## TO BE DELETED

if __name__ == '__main__':
    from dotenv import dotenv_values

    # load token from .env
    config = dotenv_values('.env')
    URL = config['SERVER_URL']
    MODEL = config['SERVER_MODEL'] if 'SERVER_MODEL' in config else None
    TYPE = config['SERVER_TYPE'] if 'SERVER_TYPE' in config else None
    API_KEY = config['SERVER_API_KEY'] if 'SERVER_API_KEY' in config else None

    # Configure a ModelProvider if there is an URL
    provider = ModelProvider(type=TYPE,  base_url=URL, api_key=API_KEY, model=MODEL) if URL else None
    print(provider.request(prompt="1+1"))

