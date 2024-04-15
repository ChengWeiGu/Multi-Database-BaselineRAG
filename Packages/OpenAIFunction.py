# -*- coding: utf-8 -*-
import pandas as pd
import configparser
from openai import AzureOpenAI
import random
import Tools
import time
import base64

config=configparser.ConfigParser()
config.read("Config.ini")

## default setting for both embedding and chat
chat_settings = {
    'endpoint':config['AOAI_SE']['endpoint'],
    'api_key1':config['AOAI_SE']['api_key1'],
    'api_key2':config['AOAI_SE']['api_key2'],
    'region':config['AOAI_SE']['region'],
    'api_version':config['AOAI_SE']['api_version'],
    'chat_model_gpt4':config['MODEL']['chat_model_gpt4_1106'],
    'chat_model_gpt35':config['MODEL']['chat_model_gpt35_0613'],
    'api_type':config['AOAI_SE']['api_type']
}

chat_prob = {
    'AOAI_SE':float(config['AOAI_SE']['probability']),
    'AOAI_WU':float(config['AOAI_WU']['probability']),
    'AOAI_DEFAULT':float(config['AOAI_DEFAULT']['probability']),
    'AOAI_CANADAE':float(config['AOAI_CANADAE']['probability']),
    'AOAI_EU2':float(config['AOAI_EU2']['probability'])
}
# regularization for probability
total_prob = sum(chat_prob.values())
for k, v in chat_prob.items():
    chat_prob[k] = v / total_prob
    # print(f"k:{k}, v:{chat_prob.get(k)}")


embedding_settings = {
    'endpoint':config['AOAI_DEFAULT']['endpoint'],
    'api_key1':config['AOAI_DEFAULT']['api_key1'],
    'api_key2':config['AOAI_DEFAULT']['api_key2'],
    'region':config['AOAI_DEFAULT']['region'],
    'api_version':config['AOAI_DEFAULT']['api_version'],
    'embedding_model':config['MODEL']['embedding_model_v3_large'],
    'api_type':config['AOAI_DEFAULT']['api_type']
}


image_gen_settings = {
    'endpoint':config['AOAI_SE']['endpoint'],
    'api_key1':config['AOAI_SE']['api_key1'],
    'api_key2':config['AOAI_SE']['api_key2'],
    'region':config['AOAI_SE']['region'],
    'api_version':config['AOAI_SE']['api_version'],
    'image_generation_model':config['MODEL']['image_generation_model'],
    'api_type':config['AOAI_SE']['api_type']
}


chat_vision_settings = {
    'endpoint':config['AOAI_WU']['endpoint'],
    'api_key1':config['AOAI_WU']['api_key1'],
    'api_key2':config['AOAI_WU']['api_key2'],
    'region':config['AOAI_WU']['region'],
    'api_version':config['AOAI_WU']['api_version'],
    'chat_vision_model':config['MODEL']['chat_vision_gpt4'],
    'api_type':config['AOAI_WU']['api_type']
}

chat_vision_enhance_cognitive_settings = {
    'endpoint':config['ACOG_VIS_ENHANCE_WU']['endpoint'],
    'api_key1':config['ACOG_VIS_ENHANCE_WU']['api_key1'],
    'api_key2':config['ACOG_VIS_ENHANCE_WU']['api_key2'],
    'region':config['ACOG_VIS_ENHANCE_WU']['region'],
    'api_version':config['ACOG_VIS_ENHANCE_WU']['api_version'],
    'api_type':config['ACOG_VIS_ENHANCE_WU']['api_type']
}


# params
max_completion_token = int(config['PARAMETERS']['max_completion_token'])
temperature = float(config['PARAMETERS']['temperature'])
system_prompt=config['PROMPT']['system_prompt'] + "\nThe introduction as below:\n" + Tools.read_introduction_doc()
# params for gpt4-vision
max_vision_completion_token = int(config['PARAMETERS']['max_vision_completion_token'])

def random_set_azure_chat_resc():
    global chat_settings, chat_prob
    # randomly choose one
    # resc_name_list = ['AOAI_SE','AOAI_WU','AOAI_DEFAULT','AOAI_CANADAE','AOAI_EU2']
    # random_resc_name = random.choice(resc_name_list)
    random_num = random.random()
    comulative_prob = 0
    random_resc_name = ''
    for resc_name, resc_prob in chat_prob.items():
        comulative_prob+=resc_prob
        if random_num <= comulative_prob:
            random_resc_name = resc_name
            break
    chat_settings['endpoint']=config[random_resc_name]['endpoint']
    chat_settings['api_key1']=config[random_resc_name]['api_key1']
    chat_settings['api_key2']=config[random_resc_name]['api_key2']
    chat_settings['region']=config[random_resc_name]['region']
    chat_settings['api_version']=config[random_resc_name]['api_version']
    chat_settings['api_type']=config[random_resc_name]['api_type']
    # gpt4
    if chat_settings['region'] == 'eastus':
        chat_settings['chat_model_gpt4']= config['MODEL']['chat_model_gpt4_0125']
    else:
        chat_settings['chat_model_gpt4']= config['MODEL']['chat_model_gpt4_1106']
    # gpt3.5
    if chat_settings['region'] == "westus":
        chat_settings['chat_model_gpt35'] = config['MODEL']['chat_model_gpt35_1106']
    elif chat_settings['region'] == 'canadaeast':
        chat_settings['chat_model_gpt35'] = config['MODEL']['chat_model_gpt35_0125']
    else:
        chat_settings['chat_model_gpt35'] = config['MODEL']['chat_model_gpt35_0613']

# use v3-large
def random_set_azure_embed_resc():
    global embedding_settings
    resc_name_list = ['AOAI_DEFAULT','AOAI_CANADAE','AOAI_EU2']
    random_resc_name = random.choice(resc_name_list)
    embedding_settings['endpoint']=config[random_resc_name]['endpoint']
    embedding_settings['api_key1']=config[random_resc_name]['api_key1']
    embedding_settings['api_key2']=config[random_resc_name]['api_key2']
    embedding_settings['region']=config[random_resc_name]['region']
    embedding_settings['api_version']=config[random_resc_name]['api_version']
    embedding_settings['api_type']=config[random_resc_name]['api_type']
    embedding_settings['embedding_model'] = config['MODEL']['embedding_model_v3_large']

# use dalle3
def random_set_azure_imggen_resc():
    global image_gen_settings
    resc_name_list = ['AOAI_DEFAULT','AOAI_SE']
    random_resc_name = random.choice(resc_name_list)
    image_gen_settings['endpoint'] = config[random_resc_name]['endpoint']
    image_gen_settings['api_key1'] = config[random_resc_name]['api_key1']
    image_gen_settings['api_key2'] = config[random_resc_name]['api_key2']
    image_gen_settings['region'] = config[random_resc_name]['region']
    image_gen_settings['api_version'] = config[random_resc_name]['api_version']
    image_gen_settings['image_generation_model'] = config['MODEL']['image_generation_model']
    image_gen_settings['api_type'] = config[random_resc_name]['api_type']


# use gpt4-vision
def random_set_azure_chat_vision_resc():
    global chat_vision_settings
    resc_name_list = ['AOAI_WU']
    random_resc_name = random.choice(resc_name_list)
    chat_vision_settings['endpoint'] = config[random_resc_name]['endpoint']
    chat_vision_settings['api_key1'] = config[random_resc_name]['api_key1']
    chat_vision_settings['api_key2'] = config[random_resc_name]['api_key2']
    chat_vision_settings['region'] = config[random_resc_name]['region']
    chat_vision_settings['api_version'] = config[random_resc_name]['api_version']
    chat_vision_settings['chat_vision_model'] = config['MODEL']['chat_vision_gpt4']
    chat_vision_settings['api_type'] = config[random_resc_name]['api_type']
    if random_resc_name == 'AOAI_WU':
        chat_vision_enhance_cognitive_settings['endpoint'] = config['ACOG_VIS_ENHANCE_WU']['endpoint']
        chat_vision_enhance_cognitive_settings['api_key1'] = config['ACOG_VIS_ENHANCE_WU']['api_key1']
        chat_vision_enhance_cognitive_settings['api_key2'] = config['ACOG_VIS_ENHANCE_WU']['api_key2']
        chat_vision_enhance_cognitive_settings['region'] = config['ACOG_VIS_ENHANCE_WU']['region']
        chat_vision_enhance_cognitive_settings['api_version'] = config['ACOG_VIS_ENHANCE_WU']['api_version']
        chat_vision_enhance_cognitive_settings['api_type'] = config['ACOG_VIS_ENHANCE_WU']['api_type']
        

# initially, random-choose once
random_set_azure_chat_resc()
random_set_azure_embed_resc()
random_set_azure_imggen_resc()
random_set_azure_chat_vision_resc()


def create_embedding_openai(texts):
    # to confirm using correct resc for embed
    random_set_azure_embed_resc()       
    # single string to a string list
    if isinstance(texts,str):
        texts=[texts]
    # define return fmt
    return_json={'texts':texts,
                'embeddings':[[]],
                'prompt_tokens': 0,
                'total_tokens': 0,
                'status':"fail",
                'error_reason':""}
    
    # call openai api
    try:
        client = AzureOpenAI(api_key = embedding_settings['api_key1'], 
                             api_version = embedding_settings['api_version'], 
                             azure_endpoint = embedding_settings['endpoint'])
        resp=client.embeddings.create(model=embedding_settings['embedding_model'],
                                      input=texts)
        resp_dict=resp.model_dump()
        # reconstruct the return fmt
        return_json['embeddings'] = [data['embedding'] for data in resp_dict['data']]
        return_json['prompt_tokens'] = resp_dict['usage']['prompt_tokens']
        return_json['total_tokens'] = resp_dict['usage']['total_tokens']
        return_json['status'] = 'success'
    except Exception as e:
        error_reason = f"[OPENAI ERROR]{str(e)}"
        return_json['error_reason'] = error_reason
        print(error_reason)
    return return_json


# three roles: system, user and assistant
def chat_completion_openai(message, model=None):
    # to confirm use correct resc for different region
    random_set_azure_chat_resc()
    print('az_region: ',chat_settings['region'])
    if model == 'gpt4':
        model = chat_settings['chat_model_gpt4']
    elif model == 'gpt35':
        model = chat_settings['chat_model_gpt35']
    else:
        model = chat_settings['chat_model_gpt35'] # default
    # define return fmt
    return_json={
                'prompt_tokens': 0,
                'completion_tokens':0,
                'total_tokens': 0,
                'status':"fail",
                'selected_model':model,
                'replied_message':"",
                'error_reason':""
            }
    try:
        client = AzureOpenAI(
                            api_key = chat_settings['api_key1'], 
                            api_version = chat_settings['api_version'], 
                            azure_endpoint = chat_settings['endpoint']
                        )
        chat_completion = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_completion_token,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                messages=[{"role":"system","content":system_prompt},
                        {"role":"user","content":f"{message}"}]
            )
        return_json['prompt_tokens'] = chat_completion.usage.prompt_tokens
        return_json['completion_tokens'] = chat_completion.usage.completion_tokens
        return_json['total_tokens'] = chat_completion.usage.total_tokens
        return_json['replied_message'] = chat_completion.choices[0].message.content
        return_json['prompt_tokens'] = chat_completion.usage.prompt_tokens
        return_json['status'] = "success"
        # print(chat_completion)
    except Exception as e:
        error_reason = f"[OPENAI ERROR]{str(e)}"
        return_json['error_reason'] = error_reason
        # print(error_reason)
    return return_json


# three roles: system, user and assistant
# chat with history, openai_history_messages should includes the newest question
def chat_completion_openai_history(openai_history_messages:list=[], model=None):
    # to confirm use correct resc for different region
    random_set_azure_chat_resc()
    print('az_region: ',chat_settings['region'])
    if model == 'gpt4':
        model = chat_settings['chat_model_gpt4']
    elif model == 'gpt35':
        model = chat_settings['chat_model_gpt35']
    else:
        model = chat_settings['chat_model_gpt35'] # default
    # define return fmt
    return_json={
                'prompt_tokens': 0,
                'completion_tokens':0,
                'total_tokens': 0,
                'status':"fail",
                'selected_model':model,
                'replied_message':"",
                'error_reason':""
            }
    try:
        client = AzureOpenAI(
                            api_key = chat_settings['api_key1'], 
                            api_version = chat_settings['api_version'], 
                            azure_endpoint = chat_settings['endpoint']
                        )
        chat_completion = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_completion_token,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                messages=[{"role":"system","content":system_prompt}] + openai_history_messages
            )
        return_json['prompt_tokens'] = chat_completion.usage.prompt_tokens
        return_json['completion_tokens'] = chat_completion.usage.completion_tokens
        return_json['total_tokens'] = chat_completion.usage.total_tokens
        return_json['replied_message'] = chat_completion.choices[0].message.content
        return_json['prompt_tokens'] = chat_completion.usage.prompt_tokens
        return_json['status'] = "success"
        # print(chat_completion)
    except Exception as e:
        error_reason = f"[OPENAI ERROR]{str(e)}"
        if "Error code: 400" in error_reason:
            return_json['error_reason'] = "[OPENAI ERROR][Context Length Exceeded] : Please shorten your input words"
        else:
            return_json['error_reason'] = error_reason
        # print(error_reason)
    return return_json



def generate_image_openai(prompt,n=1):
    # to confirm use correct resc for img gen
    random_set_azure_imggen_resc()
    return_json={
                'revised_prompt':"",
                'image_url':"",
                'prompt': prompt,
                'status':"fail",
                'selected_model':image_gen_settings['image_generation_model'],
                'error_reason':""
            }
    try:
        client = AzureOpenAI(
                            api_key = image_gen_settings['api_key1'], 
                            api_version = image_gen_settings['api_version'], 
                            azure_endpoint = image_gen_settings['endpoint']
                        )
        generation_result = client.images.generate(
                                model=image_gen_settings['image_generation_model'],
                                prompt=prompt,
                                n=1
                            )
        return_json['revised_prompt'] = generation_result.data[0].revised_prompt
        return_json['image_url'] = generation_result.data[0].url
        return_json['status'] = "success"
        print('az_region: ',image_gen_settings['region'])
    except Exception as e:
        error_reason = f"[OPENAI ERROR]{str(e)}"
        if "Error code: 400" in error_reason:
            return_json['error_reason'] = "[OPENAI ERROR][Safety Error] : Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system"
        else:
            return_json['error_reason'] = error_reason
        # print(error_reason)
    return return_json



# single chat with stream
def chat_completion_openai_stream(message, model=None):
    # to confirm use correct resc for different region
    random_set_azure_chat_resc()
    print('az_region: ',chat_settings['region'])
    if model == 'gpt4':
        model = chat_settings['chat_model_gpt4']
    elif model == 'gpt35':
        model = chat_settings['chat_model_gpt35']
    else:
        model = chat_settings['chat_model_gpt35'] # default
    try:
        client = AzureOpenAI(
                            api_key = chat_settings['api_key1'], 
                            api_version = chat_settings['api_version'], 
                            azure_endpoint = chat_settings['endpoint']
                        )
        chat_completion = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_completion_token,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                messages=[{"role":"system","content":system_prompt},
                        {"role":"user","content":f"{message}"}],
                stream=True
            )
        # EOS -> chunk_content is None
        for chunk in chat_completion:
            if chunk.choices != []:
                chunk_content = chunk.choices[0].delta.content
                yield chunk_content
                time.sleep(0.05)
    except Exception as e:
        error_reason = f"[OPENAI ERROR]{str(e)}"
        for word in error_reason:
            yield word
            time.sleep(0.01)


# history with stream
def chat_completion_openai_history_stream(openai_history_messages:list=[], model=None):
    # to confirm use correct resc for different region
    random_set_azure_chat_resc()
    print('az_region: ',chat_settings['region'])
    if model == 'gpt4':
        model = chat_settings['chat_model_gpt4']
    elif model == 'gpt35':
        model = chat_settings['chat_model_gpt35']
    else:
        model = chat_settings['chat_model_gpt35'] # default
    try:
        client = AzureOpenAI(
                            api_key = chat_settings['api_key1'], 
                            api_version = chat_settings['api_version'], 
                            azure_endpoint = chat_settings['endpoint']
                        )
        chat_completion = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_completion_token,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                messages=[{"role":"system","content":system_prompt}] + openai_history_messages,
                stream=True
            )
        # EOS -> chunk_content is None
        for chunk in chat_completion:
            if chunk.choices != []:
                chunk_content = chunk.choices[0].delta.content
                yield chunk_content
                time.sleep(0.05)
        # print(chat_completion)
    except Exception as e:
        error_reason = f"[OPENAI ERROR]{str(e)}"
        if "Error code: 400" in error_reason:
            error_reason = "[OPENAI ERROR][Context Length Exceeded] : Please shorten your input words"
            for word in error_reason:
                yield word
                time.sleep(0.01)


# vision model: gpt4-vision (no enhancement)
def chat_completion_vision_openai(query="Describe this picture:",image_rul=None, image_filename=None):
    # to comfirm use correct resc for vision
    random_set_azure_chat_vision_resc()
    print('az_region: ', chat_vision_settings['region'])
    try:
        client = AzureOpenAI(
                            api_key = chat_vision_settings['api_key1'], 
                            api_version = chat_vision_settings['api_version'], 
                            azure_endpoint = chat_vision_settings['endpoint'],
                        )
        response = client.chat.completions.create(
                            model=chat_vision_settings['chat_vision_model'],
                            messages=[
                                { "role": "system", "content": "You are a helpful assistant." },
                                { "role": "user", "content": [  
                                    { 
                                        "type": "text", 
                                        "text": query 
                                    },
                                    { 
                                        "type": "image_url",
                                        "image_url": {
                                            "url": image_rul
                                        }
                                    }
                                ]}
                            ],
                            max_tokens=max_vision_completion_token 
                        )
        replied_message = response.choices[0].message.content
        return replied_message
    except Exception as e:
        error_reason = f"[OPENAI ERROR]{str(e)}"
        print(error_reason)
        return error_reason


# vision model: gpt4-vision (with enhancement)
def chat_completion_vision_enhance_openai_history(openai_history_messages:list=[]):
    # to comfirm use correct resc for vision
    random_set_azure_chat_vision_resc()
    print('az_region: ', chat_vision_settings['region'])
    try:
        client = AzureOpenAI(
                            api_key = chat_vision_settings['api_key1'], 
                            api_version = chat_vision_settings['api_version'], 
                            azure_endpoint = chat_vision_settings['endpoint'],
                        )
        response = client.chat.completions.create(
                            model=chat_vision_settings['chat_vision_model'],
                            messages=[
                                { "role": "system", "content": "You are a helpful assistant." },
                                { "role": "user", "content": openai_history_messages}
                            ],
                            extra_body={
                                "data_sources":[
                                    {
                                        "type":"AzureComputerVision",
                                        "parameters":{
                                            "endpoint": chat_vision_enhance_cognitive_settings['endpoint'],
                                            "key": chat_vision_enhance_cognitive_settings['api_key1']
                                        }
                                    }],
                                "enhancements":{
                                    "ocr": {
                                        "enabled": True
                                    },
                                    "grounding": {
                                        "enabled": True
                                    }
                                }
                            },
                            max_tokens=max_vision_completion_token 
                        )
        replied_message = response.choices[0].message.content
        # result = response.json()
        return replied_message
    except Exception as e:
        error_reason = f"[OPENAI ERROR]{str(e)}"
        print(error_reason)
        return error_reason



if __name__ == "__main__":
    # print(len(create_embedding_openai(texts=["you're a good man","yes i understand"])['embeddings'][0])) #3072
    
    # message="Hi can we have a short conversation?"
    # print(system_prompt)
    # print(chat_completion_openai(message))
    
    # print(generate_image_openai("a crockdile floating on the water"))
    
    # chat_completion_openai_stream(message="中國歷史上誰統一天下?")
    # import os
    # result = ""
    # for word in chat_completion_openai_stream(message="提供一個python code範例"):
    #     if word is not None:
    #         os.system('cls')
    #         result += word
    #         print(result)
    
    # gpt4-vision
    # result = chat_completion_vision_openai(image_rul="url")
    # gpt4-vision enhancement
    encoded_image1 = base64.b64encode(open(r"D:\Projects\EBProWhisper\PFXGP4603TAD_screenshot.jpg", "rb").read()).decode('ascii')
    encoded_image2 = base64.b64encode(open(r"D:\Projects\EBProWhisper\home.jpg", "rb").read()).decode('ascii')
    openai_history_messages = [{ 
                "type": "text", 
                "text": "This image shows a hmi screen which designed for user to operate." 
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jepg;base64,{encoded_image1}"
                }
            },
            {
                "type": "text",
                "text": "This element is extracted from the screenshot. please describe the element and give it a name"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jepg;base64,{encoded_image2}"
                }
            },
            {
                "type": "text",
                "text": "output your result with {\"descr\":<element description>,\"name\":<element name>}"
            }]
    result = chat_completion_vision_enhance_openai_history(openai_history_messages=openai_history_messages)
    print(result)
    pass
    