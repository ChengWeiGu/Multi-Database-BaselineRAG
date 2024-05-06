# -*- coding: utf-8 -*-
import pandas as pd
import re
import tiktoken
import configparser
import requests
from bs4 import BeautifulSoup
import string
import random
import datetime


config = configparser.ConfigParser()
config.read("config.ini")
cost_per_1k_tokens_ada_v2 = float(config['PRICE']['cost_per_1k_tokens_ada_v2'])



# as fun name to remove html tag
def remove_html_tags(text):
    html_pattern = re.compile('<.*?>')
    nbsp_pattern = re.compile('&nbsp;')
    clean_html_text = re.sub(html_pattern,'',text)
    clean_html_nbsp_text = re.sub(nbsp_pattern,' ',clean_html_text)
    return clean_html_nbsp_text

# cal total tokens by tiktoken
def calculate_tokens(model="text-embedding-ada-002",documents=["Kota Factory (TV Show)","The Last Letter From Your Lover (Movie)"]):
    try:
        enc = tiktoken.encoding_for_model(model)
        total_tokens = sum(len(enc.encode(text)) for text in documents)
        cost_per_1k_tokens = cost_per_1k_tokens_ada_v2
        cost = cost_per_1k_tokens*total_tokens/1000
    except Exception as e:
        err_msg = f"[TOKEN CAL ERROR] {str(e)}"
        print(err_msg)
        total_tokens = 0
        cost = 0
    return total_tokens, cost



# 2024/3/14
# purpose: put all history info and cal similarity
# history_messages = [] if no user's question else [[Q1,A1],[Q2,Q2],...etc]
def create_search_body(history_messages, query, recent_k:int = 3):
    whole_history_body = ''
    history_messages = history_messages[-recent_k:]
    for i, pair in enumerate(history_messages,1):
        Qi, Ai = pair
        # whole_history_body += f"Question{i}:{Qi}\nAnswer{i}:{Ai}\n\n"
        whole_history_body += f"Question{i}:{Qi}\n\n"
    whole_history_body += f"New Question:{query}"
    return whole_history_body

# 2024/3/14
# history_messages = [] if no user's question else [[Q1,A1],[Q2,Q2],...etc]
# query -> the new question without prompt engineering,  prompt -> the new question with prompt engineering
# return openai's messages: [{"role":"user","content":message_request}, {"role": "assistant", "content": message_response},...,{"role":"user","content":prompt}]
def convert2OpenaiMessages(history_messages, prompt):
    openai_history_messages = []
    for i, pair in enumerate(history_messages,1):
        Qi, Ai = pair
        openai_history_messages.append({"role":"user","content":Qi})
        openai_history_messages.append({"role": "assistant", "content": Ai})
    openai_history_messages.append({"role":"user","content":prompt})
    return openai_history_messages
        

# read the comapny introduction which will be added to system prompt
def read_introduction_doc(filename = r".\Databases\Customized_Files\Introduction_weintek.txt"):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()




def acquire_web_links(context):
    links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', context)
    return links


def crawler_website(url = "https://www.weintek.com/globalw/Product/Product_speccMTG.aspx"):
    content_texts = ''
    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        content_texts = soup.get_text()
    except Exception as e:
        content_texts = f"[Crawler Error] {str(e)}"
    return content_texts


def create_random_serial_number(length=10):
    serial_number = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f_')
    for _ in range(length):
        prob = random.random()
        if prob < 0.5:
            serial_number += random.choice(string.ascii_uppercase)
        else:
            serial_number += random.choice(string.digits)
    return serial_number



if __name__ == "__main__":
    # words = """<br />  Dear sirs,<br />  <br />  We have used MT506TV for 3 years.<br />  Now I&nbsp;am exploring your new model MT6070iH, and I am trying to realize a connection between PC, HMI and PLC. HMI-PLC communication seems    OK, but the only posible connection for HMI project&nbsp;downloading I’m realizing is via&nbsp;USB ports. 
    #             <span style="text-decoration: underline">Is it    posible to program HMI via COM port?</span> In your file EB8000_Comport_PassThru_Test_List.pdf&nbsp; I found that communication between    my&nbsp;PLC and PC in pass-through mode&nbsp;is posible but any cable connection&nbsp;I have tried do not&nbsp;establish&nbsp;connection. 
    #             <span    style="text-decoration: underline">Why EB8000 Project Manager (v.3.32) need a IP to realyze a serial communicatoin?</span> In Pass-through mode I    expect to download project to HMI and PLC via one cable connected to the HMI. <span style="text-decoration: underline">Am I right?
    #             </span> The HMI will be    mounted on&nbsp;operator’s panel with 5 push buttons on the side of HMI communication ports, so it is impossible to use USB cable for project    downloading.&nbsp;<span style="text-decoration: underline">Could you give me any advise how to wire and program HMI via COM port, as I have done with    MT506TV model?</span><br />  <br />  Best Regards<br />  Stefan Mihaylov"""
    # print(remove_html_tags(words))
    # print(calculate_tokens(documents=[words]))
    # text = """
    #         (8) If users ask about product specifications, you can provide them with official websites under the following category:
    #         *cMT Series: https://www.weintek.com/globalw/Product/Product_cMT.aspx
    #         *cMTX Series: https://www.weintek.com/globalw/Product/Product_cMTX.aspx
    #         *Gateway Series: https://www.weintek.com/globalw/Product/Product_Gateway.aspx
    #         *IR Series: https://www.weintek.com/globalw/Product/Product_speciR.aspx
    #         *IE Series: https://www.weintek.com/globalw/Product/Product_iE.aspx
    #         *IP Series: https://www.weintek.com/globalw/Product/Product_iP.aspx
    #         *Accessories Series: https://www.weintek.com/globalw/Product/Product_Accessories.aspx
    #         (9) None the above, please skip this step and proceed to think the next step
    #         """
    # text = """please summarise the website
    #         https://support.ihmi.net"""
    
    # print(acquire_web_links(text))
    print(create_random_serial_number())
    
    