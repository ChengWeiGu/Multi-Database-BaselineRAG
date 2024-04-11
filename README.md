# Multi-Database_Retrieval_Augmented_Generation  
Here is a simple script to implement RAG with Azure OpenAI Resource  

## Installation:  

● Python Version : python=3.11  
● Please run "pip install -r requirements.txt"  

## Introduction of the App.py:  

1. The chatbox has two modes, first mode is the chat generation which use RAG to interact with users:  
  
![image](https://github.com/ChengWeiGu/MultiDatabase-Retrieval-Augmented-Generation/blob/main/chat_gen.png)    
  
2. For second mode, user can use dalle3 to do image generation:  
  
![image](https://github.com/ChengWeiGu/MultiDatabase-Retrieval-Augmented-Generation/blob/main/img_gen.png)  

## Settings  
1. Please set the `config.ini` before running the `App.py`  
2. Description of `config.ini`:  

| Setting  | Description |
| ------------- | ------------- |
| CHROMA_DB  | Five databases used in this case. (Path setting is needed)  |
| Azure Resource  | Five regions used (probabilistic choice).  |
| Model           |  Model name built on AOAI. (Should be consistent)     |
| Parameters      |  Temperature & max_output_token. (In fact, more parameters available)  |   

## Reverse Proxy Settings  
1. In this case, we use nginx as the proxy server  
2. Note that to set "nginx-1.24.0\conf\nginx.conf" before runing nginx.exe    
3. Overall, the system is deployed in environment of flask + waitress + nginx:  

| Setting  | Description |
| ------------- | ------------- |
| worker_processes  | how many workers in process  |
| upstream  | randomly assigned to the binding IP and port  |
| server_name           |  IP of the proxy server     |
| location      |  the settings are used for OpenAI API streaming  |   

4. Use the following commands to operate NGINX:  
● start nginx.exe    //execute nginx   
● tasklist /fi "imagename eq nginx.exe"   //Run the tasklist command-line utility to see nginx processes   
● nginx -s stop	  //fast shutdown   
● nginx -s quit	  //graceful shutdown   
● nginx -s reload	   //changing configuration, starting new worker processes with a new configuration, graceful shutdown of old worker processes   
● nginx -s reopen	   //re-opening log files  
