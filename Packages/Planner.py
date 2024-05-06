# -*- coding: utf-8 -*-
from scipy.spatial import distance
import OpenAIFunction
import time
import configparser
import Tools
import Reranker
import json

config=configparser.ConfigParser()
config.read("Config.ini")
firewall_prompt = config['PROMPT']['firewall_prompt']
close_issues_prompt=config['PROMPT']['close_issues_prompt']


class ZeroShotPlanner:
    def __init__(self):
        # class1: srdb, class2: docdb, class3: jssdkdb, ,class4: weincloud, class5: general task, class6: others
        self.class_dict = {'class1':["This question is about product, software, and hardware issues. It offers a structured QA format, conveniently accessible via email",
                                        "This question is about weintek FAE-customer interactions regarding product usage, troubleshooting, or historical inquiries",
                                        "Customer queries regarding bug, Event Log Issues or equipment (設備)",
                                        "The actual problems encountered in the production environment of machine equipment",
                                        "This question is about finding a solution from historical service request Q & A"],
                            'class2':["This question is about operations related to Weintek's product software and hardware, including EBPro, EB, CODESYS and product introductions, etc",
                                      "This question is about operational procedures related to Weintek's product, such as PLC or HMI (cMT-Series, cMTX-Series, Gateway-Series (G Series), iR-Series, iE-Series, iP-Series, Accessories.)",
                                      "This question is about Weintek's EBPro functionality, event log issue or SQL query for HMI Setting",
                                      "This is the question about EBPro project,including how to download a project (下載project) and some FAQ",
                                      "This is question about writting Macro codes where the macro is embedded in weintek's EBPro",
                                      "Customer wants step-by-step guides to tutorial or operation of Weintek's product (user manual guide)"],
                            'class3':["The question is related to JS Object SDK, providing examples and tutorials for JS SDK usage",
                                      "A specialized repository dedicated to JS Object SDK, offering a plethora of examples and tutorials designed to streamline JS SDK usage",
                                      "Unleash the power of JavaScript, where you'll find a comprehensive collection of resources tailored specifically to JS Object SDK",
                                      "A gateway to mastering JS Object SDK, providing developers with hands-on examples and insightful tutorials to facilitate seamless integration and utilization of JavaScript capabilities within the product ecosystem"],
                            'class4':["This question is about WeinCloud, EA2.0 (EA20), EASYACCESS 2.0, EasyAccess 2.0, Dashboard or IIoT",
                                       "EasyAccess is a remote supporting service. Customer can remotely connect to the HMI through EasyAccess 2.0 to investigate the problem with Hardware Key (HWKey)",
                                       "Weincloud Dashboard is a cloud service aims to help enterprises to expedite deployment of digital assets and improve production and monitoring efficiency",
                                       "Weintek IIoT includes MQTT, OPC UA, AWS IoT, RDS or ALIYUN IOT PLATFORM",
                                       "EasyAccess 2.0 inclues Push Notification (推播通知) and Top-up Card (流量卡)"],
                            'class5':["This question is about Weintek product specifications (規格), questions related to whether it supports memory, processor, I/O interfaces, and other specification-related issues.",
                                      "Weintek product include cMT- series, eMT600- series, eMT3000- series, iRSeries, MT600- series, MT8000- series, MT8000iE- series, MT8000iP- series, MT8000XE- series, mTV- series, G- series"],
                            'class6':["I think we've covered everything for now. Thanks for your help!",
                                      "That clears things up. Appreciate your assistance!",
                                      "Looks like we've got it sorted. Thanks again!",
                                      "I believe we've addressed everything. Thanks for your input!",
                                      "Seems like we've reached a resolution. Thanks for your guidance!"],
                            'class7':["This question is about a general tasks such as language translation, writting an email (寫作風格、寫Email、寫電子郵件), arranging meetings, simple greetings or format conversion (格式轉換), summary tasks, making (or transforming into) a table (表格整理)",
                                      "This is a general task about web crawler, summarizing a website (總結網站資訊, 網頁內容, 彙整網頁資訊), web information extraction (網站資訊萃取)",
                                      "This question is about data analysis, excel formula, human history, astronomy, geography, physics, chemistry, math or biology",
                                      "This question is about introduction of Weintek Company"],
                            'class8':["This question is about personal feelings, love, interpersonal relationships, or friendship issues",
                                      "This question is about hacking, fighting or greetings",
                                      "This question is a sensitive about confidential information (機密資訊), personal privacy (個人隱私), sex (性話題), violence (暴力), politics (政治) and crime (犯罪)"]
                            }
        self.n_class = len(self.class_dict)
        self.step_prompt = """
                            Step 1: Determine the role of the user who must be one of "End Customer" or "Distributor":
                                    (1) if the question contains sentences like "Customer has a ..." or "Our client has encountered..." or "In our customer's case...", he is a "Distributor".
                                    (2) otherwise, he is our "End customer".
                            
                            Step 2: Determine user's purpose from the new question and chat history (between you and user). Use following way to do summary:
                                    (1) Rule: You must consider contextual responses to understand the user's intended goal and help them achieve it.
                                    (2) if user wants to know where to download Weinview model, try to give the web link or ask them to contact their supplier for help
                                    (3) if user wants to know about manipulation and operation method, try to find the answer and reply them with step by step.
                                    (4) if user want to talk with you, you should talk with them carefully. do not talk about sensitive words, such as sex or violence or politics or crime.
                                    (5) If user asks about product specifications, you can provide them with official websites : https://www.weintek.com/globalw/
                                    (6) For User Guide Manual, Weintek Official Download Link is : https://www.weintek.com/globalw/Download/Download.aspx
                                    (7) None the above, please skip this step and proceed to think the next step
                            
                            Step 3: Determine the user's product name, use following way to do summary:
                                    (1) if user's product belongs to TK-Series HMI like TK6071iQ, please just diplomatically ask them to request their supplier
                                    (2) if user does not provde the information, you can ask them "Can you provide your product name for further assiatance?"
                                    (3) If the end customer is from Italy, advise them to reach out to our Italian distributors for assistance.
                                    (4) None the above, please skip this step and proceed to think the next step
                            
                            Step 4: Decompose the user's question and determine if additional sub-tasks need to be performed. please use the rules below:
                                    (1) general tasks includes language translation, writting an email, arranging meetings, table process, format conversion, ...etc.
                                    (2) general tasks includes wirting python, macro, css, c++ or javascript codes.
                                    (3) If the user requests you to provide a table, please transform your answer into Markdown format as possible.
                                    (4) If user wants you to summarize a website via web crawlwer, tell him to use the prompt: 
                                        -- "it is a general task , please use web crawler to summarize the following website: <your link>"
                                    (5) None the above, please skip this step and proceed to think the next step
                            
                            Step 5: Determine how the user can seek assistance accroding to <step 1 result>:
                                    (1) For end customers, you can ask them to contact his distributor for inquiries and helps.
                                    (2) For distributors, you can ask them to "approach us directly for assistance"
                            
                            Step 6: To Determine which references are most relavant to the new question and provide them
                                    (1) Provide the most relevant <source> in retrieved QA or documents where <source> is full filename with pdf, docx or jpg
                                        If you can find the most relevant chapter or subchapter from the source, please show the chapter and its title with the format :
                                        <source> & chapter : <the chapter and its title>
                                    (2) Provide the most relevant <web link> mentioned in retrieved QA or documents where <web link> is full http name
                                    (3) Note that your answer should follow the format:
                                        -- document source: determine result of (1) else 'N'
                                        -- Web link: determine result of (2) else 'N'
                                    (4) If there are no useful reference can be found, please skip this step and proceed to think the next step
                            
                            Step 7: Write down the answer, advice and summary to the new question in English and use the rules below: 
                                    (1) Note that if you can find the answer in the QA paris or retrieved documents, please just show the result and do not mention where it can be found in your summary.
                                    (2) Note that if the answer pertains to operational steps, please provide clear instructions with bullet points.
                                    (3) Note that do not write down any analysis description of user's purpose in your summary.
                                    (4) Note that if the answer cannot be found in the above QA pairs and documents, please says 'I cannot reply. less information. Could you provide more information?' in your summary
                            
                            Output your answers with the following fixing format without any statement of steps:
                            Summary: 
                            <step 7 result in English>
                            Reference:
                            <step 6 result>
                            """
        
    def find_n_closest(self,query_vector, embeddings, n = 1):
        distances=[]
        for index, embedding in enumerate(embeddings):
            dist=distance.cosine(query_vector,embedding)
            distances.append({"distance":dist,"index":index})
        distances_sorted = sorted(distances,key=lambda x:x['distance'])
        return distances_sorted[:n]
    
    def generate_class_embed(self):
        class_texts = []
        for i in range(1,self.n_class+1):
            class_texts.append(". ".join(self.class_dict["class%d"%i]))
        retry_cnt = 0
        max_retries = 3
        while retry_cnt < max_retries:
            try:
                self.embeddings = OpenAIFunction.create_embedding_openai(class_texts)['embeddings']
            except Exception as e:
                print("[ZeroShotPlanner][Create Embedding Error]:",str(e))
                retry_cnt += 1
            else:
                break
    
    def get_intension(self,query):
        self.db_mask = [0]*self.n_class
        retry_cnt = 0
        max_retries = 3
        while retry_cnt < max_retries:
            try:
                query_vector=OpenAIFunction.create_embedding_openai(query)['embeddings'][0]
                distances_sorted = self.find_n_closest(query_vector,self.embeddings) # top2: [{'distance': 0.2576220882938325, 'index': 1}, {'distance': 0.2964973981584623, 'index': 0}]
                for d in distances_sorted:
                    self.db_mask[d['index']] = 1
            except Exception as e:
                print("[ZeroShotPlanner][Plan Mask Error]:",str(e))
                retry_cnt += 1
            else:
                break

    def plan2generate_stream(self,**kwargs):
        lcdb_doc_embed = kwargs['lcdb_doc_embed']
        lcdb_sr_embed = kwargs['lcdb_sr_embed']
        lcdb_jssdk_embed = kwargs['lcdb_jssdk_embed']
        lcdb_wc_embed = kwargs['lcdb_wc_embed']
        lcdb_spec_embed = kwargs['lcdb_spec_embed']
        generate_model = kwargs['generate_model']
        query = kwargs['query']
        history_messages = kwargs['history_messages']
        whole_history_body = query
        error_reason = ""
        # loop try with 3 times
        retry_cnt = 0
        max_retries = 3
        segment_str = "-"*80
        while retry_cnt < max_retries:
            qa_text_body=""
            doc_text_body=""
            try:
                if query.replace(" ","") != "":
                    # calculate mask
                    period_intentsion_1=time.time()
                    self.get_intension(query=query)
                    print("db_mask: ",self.db_mask)
                    period_intension_2 = time.time()
                    print(f"time cost for intension: {period_intension_2-period_intentsion_1}")
                    ###### plan 1: block inpropriate question
                    if self.db_mask[-1] == 1:
                        for word in firewall_prompt:
                            yield word
                            time.sleep(0.01)
                    ###### plan 2: general tasks, no search
                    elif self.db_mask[-2] == 1 :
                        print("this is a general task, then no search")
                        # crawler task
                        links = Tools.acquire_web_links(query)
                        if (len(links) > 0 and "crawler" in query.lower()):
                            generate_model = "gpt4"
                            web_context = Tools.crawler_website(links[0])
                            prompt = f"""The following is a content of a document:\n {web_context}\n
                                        According to the user's question: \n{query}\n Please help user to summarize the document.
                                        If the content shows any error, sex, violence, politics and crime, you should say 
                                        "Sorry, I cannot access to the website." or "Sorry, I detect some inappropriate words to the website".
                                        In your summary, begin with "Summary: <result>"
                                        """
                        else:
                            generate_model = "gpt35" # to speed up general task
                            history_messages = history_messages[-5:] # only consider 5 chats for gpt35
                            prompt=query
                        openai_history_messages = Tools.convert2OpenaiMessages(history_messages, prompt)
                        for chunk_content in OpenAIFunction.chat_completion_openai_history_stream(openai_history_messages=openai_history_messages,
                                                                                                model=generate_model):
                            if chunk_content is not None:
                                yield chunk_content
                    ####### plan 3: the issue is going to be closed
                    elif self.db_mask[-3] == 1:
                        print("This issue is going to be closed")
                        for word in close_issues_prompt:
                            yield word
                            time.sleep(0.01)
                    ####### plan 4: jssdk detected
                    elif (self.db_mask[2] == 1) and (self.db_mask[-1] == 0):
                        print("this is a jssdk-related task, then do jssdk + doc search")
                        period_doc_js_chroma_1 = time.time()
                        # stage1 : searching more
                        jssdk_results = lcdb_jssdk_embed.lc_similarity_search_with_score_topk(query=whole_history_body,k=30) # maybe should do class search
                        doc_results = lcdb_doc_embed.lc_similarity_search_with_score_topk(query=whole_history_body,k=30)
                        period_doc_js_chroma_2 = time.time()
                        print(f"time cost for chroma search: {period_doc_js_chroma_2-period_doc_js_chroma_1}")
                        # stage2: Rerank
                        jssdk_results = Reranker.reranker_bm25(query,jssdk_results,top_k=5)
                        doc_results = Reranker.reranker_bm25(query,doc_results,top_k=5)
                        period_doc_js_rerank_2 = time.time()
                        print(f"time cost for reranker: {period_doc_js_rerank_2-period_doc_js_chroma_2}")
                        
                        # config doc_text_body
                        for j, doc_result in enumerate(doc_results):
                            result, score = doc_result
                            doc_text_body += segment_str + f"\nReference Document#{j+1}\n" + f"Source:{result.metadata['source']}\n" + f"Document Content:\n{result.page_content}\n" + segment_str + "\n\n"
                        # config jssdk and add it to doc_text_body
                        for k, jssdk_result in enumerate(jssdk_results,len(doc_results)):
                            result, score = jssdk_result
                            doc_text_body += segment_str + f"\nReference Document#{k+1}\n" + f"Source:{result.metadata['url']}\n" + f"JS Class:{result.metadata['class_name']}\n" + f"Class Description:{result.metadata['description']}\n" + f"Document Content:\n{result.page_content}\n" + segment_str + "\n\n"
                        # doc + jssdk prompt
                        prompt=f"""You are an efficient and prfessional assistant, sorting messages for customer service at HMI equipment manufacturer named Weintek.
                                Now you recieve the new question from a user regarding our products, software or hardware or firmware: "{query}"
                                Think logically step by step to assist the customer service representative according to the relevant information/documents retrieved from the database as follows:\n\n{doc_text_body}
                                """
                        prompt += "\n\n" + self.step_prompt
                        
                        openai_history_messages = Tools.convert2OpenaiMessages(history_messages, prompt)
                        period_doc_js_gpt_1 = time.time()
                        for chunk_content in OpenAIFunction.chat_completion_openai_history_stream(openai_history_messages=openai_history_messages,
                                                                                                model=generate_model):
                            if chunk_content is not None:
                                yield chunk_content
                        print(f"time cost for gpt: {time.time()-period_doc_js_gpt_1}")
                    ###### plan 5 : sr + wcdb
                    elif (self.db_mask[3] == 1) and (self.db_mask[-1] == 0):
                        print("this is a weincloud-related task, then do sr + wc search")
                        period_sr_wc_chroma_1 = time.time()
                        # stage1 : searching more
                        sr_results = lcdb_sr_embed.lc_similarity_search_with_score_topk(query=whole_history_body,k=5)
                        wc_results = lcdb_wc_embed.lc_similarity_search_with_score_topk(query=whole_history_body,k=30)
                        period_sr_wc_chroma_2 = time.time()
                        print(f"time cost for chroma: {period_sr_wc_chroma_2-period_sr_wc_chroma_1}")
                        # stage2: Rerank
                        # sr_results = Reranker.reranker_bm25(query,sr_results,top_k=5)
                        wc_results = Reranker.reranker_bm25(query,wc_results,top_k=10)
                        period_sr_wc_rerank_2 = time.time()
                        print(f"time cost for rerank: {period_sr_wc_rerank_2-period_sr_wc_chroma_2}")
                        
                        # config qa_text_body
                        for i , sr_result in enumerate(sr_results):
                            result, score = sr_result
                            qa_text_body += f'Q{i+1} : ' + Tools.remove_html_tags(result.metadata['SR_Message']) + f'\nA{i+1} : \n' + Tools.remove_html_tags(result.metadata['SR_Reply']) + "\n\n"
                        # config doc_text_body
                        for k, wc_result in enumerate(wc_results):
                            result, score = wc_result
                            doc_text_body += segment_str + f"\nReference Document#{k+1}\n" + f"Source:{result.metadata['url']}\n" + f"Class:{result.metadata['class_name']}\n" + f"Class Description:{result.metadata['description']}\n" + f"Document Content:\n{result.page_content}\n" + segment_str + "\n\n"
                        # sr + doc prompts
                        prompt=f"""You are an efficient and prfessional assistant, sorting messages for customer service at HMI equipment manufacturer named Weintek.
                                Now you recieve the new question from a user regarding our products, software or hardware or firmware: "{query}"
                                Think logically step by step to assist the customer service representative according to the following historical QA-pair information:\n\n{qa_text_body}
                                To make your answer more precise, you can also refer to the relevant information retrieved from the database as follows:\n\n{doc_text_body}
                                """
                        prompt += "\n\n" + self.step_prompt

                        openai_history_messages = Tools.convert2OpenaiMessages(history_messages, prompt)
                        period_sr_wc_gpt_1 = time.time()
                        for chunk_content in OpenAIFunction.chat_completion_openai_history_stream(openai_history_messages=openai_history_messages,
                                                                                                  model=generate_model):
                            if chunk_content is not None:
                                yield chunk_content
                        print(f"time cost for chat openai {time.time()-period_sr_wc_gpt_1}")
                    ###### plan 6: sr + specdb
                    elif (self.db_mask[4] == 1) and (self.db_mask[-1] == 0):
                        print("this is a product spec related task, then do sr + spec search")
                        period_sr_spec_chroma_1 = time.time()
                        # stage1 : searching more
                        sr_results = lcdb_sr_embed.lc_similarity_search_with_score_topk(query=whole_history_body,k=5)
                        spec_results = lcdb_spec_embed.lc_similarity_search_with_score_topk(query=whole_history_body,k=15)
                        period_sr_spec_chroma_2 = time.time()
                        print(f"time cost for chroma search : {period_sr_spec_chroma_2-period_sr_spec_chroma_1}")
                        # stage2: Rerank
                        # sr_results = Reranker.reranker_bm25(query,sr_results,top_k=5)
                        # spec_results = Reranker.reranker_bm25(query,spec_results,top_k=5)
                        
                        # config qa_text_body
                        for i , sr_result in enumerate(sr_results):
                            result, score = sr_result
                            qa_text_body += f'Q{i+1} : ' + Tools.remove_html_tags(result.metadata['SR_Message']) + f'\nA{i+1} : \n' + Tools.remove_html_tags(result.metadata['SR_Reply']) + "\n\n"
                        # config doc_text_body
                        for k, spec_result in enumerate(spec_results):
                            result, score = spec_result
                            doc_text_body += segment_str + f"\nReference Document#{k+1}\n" + f"Source:{result.metadata['source']}\n" + f"Document Content:\n{result.page_content}\n" + segment_str + "\n\n"
                        # sr + doc prompts
                        prompt=f"""You are an efficient and prfessional assistant, sorting messages for customer service at HMI equipment manufacturer named Weintek.
                                Now you recieve the new question from a user regarding our products, software or hardware or firmware: "{query}"
                                Think logically step by step to assist the customer service representative according to the following historical QA-pair information:\n\n{qa_text_body}
                                To make your answer more precise, you can also refer to the relevant information retrieved from the database as follows:\n\n{doc_text_body}
                                """
                        prompt += "\n\n" + self.step_prompt

                        openai_history_messages = Tools.convert2OpenaiMessages(history_messages, prompt)
                        period_sr_spec_gpt_1 = time.time()
                        for chunk_content in OpenAIFunction.chat_completion_openai_history_stream(openai_history_messages=openai_history_messages,
                                                                                    model=generate_model):
                            if chunk_content is not None:
                                yield chunk_content
                        print(f"time cost for chat: {time.time()-period_sr_spec_gpt_1}")
                    # plan 7 : others   
                    else:
                        print("this is a no class task, then do sr + doc search")
                        period_sr_doc_chroma_1 = time.time()
                        # stage1 : searching more
                        sr_results = lcdb_sr_embed.lc_similarity_search_with_score_topk(query=whole_history_body,k=10)
                        doc_results = lcdb_doc_embed.lc_similarity_search_with_score_topk(query=whole_history_body,k=30)
                        period_sr_doc_chroma_2 = time.time()
                        print(f"time cost for chroma search:{period_sr_doc_chroma_2-period_sr_doc_chroma_1}")
                        # stage2: Rerank
                        # sr_results = Reranker.reranker_bm25(query,sr_results,top_k=5)
                        doc_results = Reranker.reranker_bm25(query,doc_results,top_k=10)
                        period_sr_doc_rerank_2 = time.time()
                        print(f"time cost for rerank: {period_sr_doc_rerank_2-period_sr_doc_chroma_2}")
                        
                        # config qa_text_body
                        for i , sr_result in enumerate(sr_results):
                            result, score = sr_result
                            qa_text_body += f'Q{i+1} : ' + Tools.remove_html_tags(result.metadata['SR_Message']) + f'\nA{i+1} : \n' + Tools.remove_html_tags(result.metadata['SR_Reply']) + "\n\n"
                        # config doc_text_body
                        for j, doc_result in enumerate(doc_results):
                            result, score = doc_result
                            doc_text_body += segment_str + f"\nReference Document#{j+1}\n" + f"Source:{result.metadata['source']}\n" + f"Document Content:\n{result.page_content}\n" + segment_str + "\n\n"
                        # sr + doc prompts
                        prompt=f"""You are an efficient and prfessional assistant, sorting messages for customer service at HMI equipment manufacturer named Weintek.
                                Now you recieve the new question from a user regarding our products, software or hardware or firmware: "{query}"
                                Think logically step by step to assist the customer service representative according to the following historical QA-pair information:\n\n{qa_text_body}
                                To make your answer more precise, you can also refer to the relevant information retrieved from the database as follows:\n\n{doc_text_body}
                                """
                        prompt += "\n\n" + self.step_prompt
                        
                        openai_history_messages = Tools.convert2OpenaiMessages(history_messages, prompt)
                        period_sr_doc_gpt_1 = time.time()
                        for chunk_content in OpenAIFunction.chat_completion_openai_history_stream(openai_history_messages=openai_history_messages,
                                                                                                 model=generate_model):
                            if chunk_content is not None:
                                yield chunk_content
                        print(f"time cost for gpt: {time.time()-period_sr_doc_gpt_1}")
                else:
                    error_reason = "Your query cannot be empty! Please Try again."
                    for word in error_reason:
                        yield word
                        time.sleep(0.01)
            except Exception as e:
                error_reason = f"[ZeroShotPlanner Error]{str(e)}"
                retry_cnt += 1
                time.sleep(15)
            else:
                break
        else:
            error_reason += " => Max retries reached. Exiting..."
            # print(error_reason)
            for word in error_reason: 
                yield word
                time.sleep(0.01)



if __name__ == "__main__":
    planner = ZeroShotPlanner()
    planner.generate_class_embed()
    
    for query in ["how to install EBPro on my PC?",
                "今天天氣真好!!你覺得呢?",
                "I want to use macro to do page switch?",
                """Dear Sir/Madam how to install EBPro on my PC? sincerely, Foo Brandon""",
                "give me a sample code for JSSDK",
                "I wanna use Canvas to draw a rectangle with green color please give me an example",
                "1+1=?",
                "你有什麼特別的計劃或活動?",
                "Hi can you chat?",
                "Hey, I sent a video with the problem and the project too, if you can’t see it, I ask you to send me a number so I can send it via WhatsApp",
                "Here’s a photo of what the IHM looks like with the problem",
                """Hello, I’m from Pinto Brasil Company and we are using your HMI products us standard.
                    My question is not specifically about HMI type described on header of this page, but also about other versions and models.
                    We are using function "Data Sampling" in some devices.  We have configured it to save data on HMI memory. 
                    We have reasons to belive that our log data has been compromised. We have configured a preservation limit of 7 files and 2000 records in each file (see attached file).
                    We can assume that each day will consume one file right?
                    So, my main question is: In what conditions this logged data, through "Data Sampling" function, can be compromised (eg. deleted)?
                    We know that by doing a download, data will be reset. Your local representant also informed us that there is a bit that can be used for that for HMI recent modules. There is any other way? Can local operators do it using reset button? Removing battery? Changing dip switchs on back of HMIs? ...any way?""",
                "你知道中國歷史上是秦始皇統一天下嗎?",
                "I will kill you"]:
        ts = time.time()
        planner.get_intension(query) # cal mask
        print(f"query:{query} => mask: ",planner.db_mask)
        te = time.time()
        print("time cost: %f sec"%(te-ts))