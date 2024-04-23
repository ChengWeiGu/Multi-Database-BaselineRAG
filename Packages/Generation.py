# -*- coding: utf-8 -*-
import OpenAIFunction
import DatabaseProcess
import time
import configparser
import Planner

config=configparser.ConfigParser()
config.read("Config.ini")


chroma_login_infos = {"srdb":{"chromadb_path":config['CHROMA_DB']['sr_chromadb_path'],
                            "collection_name":config['CHROMA_DB']['sr_collection_name'],
                            "embedding_function":DatabaseProcess.embedding_function},
                    "docdb":{"chromadb_path":config['CHROMA_DB']['doc_chromadb_path'],
                        "collection_name":config['CHROMA_DB']['doc_collection_name'],
                        "embedding_function":DatabaseProcess.embedding_function},
                    "jssdkdb":{"chromadb_path":config['CHROMA_DB']['JsObjSdk_chromadb_path'],
                        "collection_name":config['CHROMA_DB']['JsObjSdk_collection_name'],
                        "embedding_function":DatabaseProcess.embedding_function},
                    "wcdb":{"chromadb_path":config['CHROMA_DB']['weincloud_chromadb_path'],
                        "collection_name":config['CHROMA_DB']['weincloud_collection_name'],
                        "embedding_function":DatabaseProcess.embedding_function},
                    'specdb': {"chromadb_path":config['CHROMA_DB']['spec_chromadb_path'],
                        "collection_name":config['CHROMA_DB']['spec_collection_name'],
                        "embedding_function":DatabaseProcess.embedding_function}}

## init database
lcdb_sr_embed = DatabaseProcess.LangchainChromaDB(login_info=chroma_login_infos['srdb'])
lcdb_doc_embed = DatabaseProcess.LangchainChromaDB(login_info=chroma_login_infos['docdb'])
lcdb_jssdk_embed = DatabaseProcess.LangchainChromaDB(login_info=chroma_login_infos['jssdkdb'])
lcdb_wc_embed = DatabaseProcess.LangchainChromaDB(login_info=chroma_login_infos['wcdb'])
lcdb_spec_embed = DatabaseProcess.LangchainChromaDB(login_info=chroma_login_infos['specdb'])
lcdb_sr_embed.init_database()
lcdb_doc_embed.init_database()
lcdb_jssdk_embed.init_database()
lcdb_wc_embed.init_database()
lcdb_spec_embed.init_database()


## init planner (2024/3/5)
zs_planner = Planner.ZeroShotPlanner()
zs_planner.generate_class_embed()


'''
zero shot with no streaming
'''
def generate_answer_zeroshotplanner(query, history_messages, generate_model='gpt4'):
    return zs_planner.plan2generate(query=query,
                                    history_messages = history_messages,
                                    lcdb_doc_embed=lcdb_doc_embed,
                                    lcdb_sr_embed=lcdb_sr_embed,
                                    lcdb_jssdk_embed=lcdb_jssdk_embed,
                                    lcdb_wc_embed=lcdb_wc_embed,
                                    lcdb_spec_embed=lcdb_spec_embed,
                                    generate_model=generate_model)


'''
zero shot with streaming
'''
def generate_stream_answer_zeroshotplanner(query, history_messages, generate_model='gpt4'):
    return zs_planner.plan2generate_stream(query=query,
                                            history_messages = history_messages,
                                            lcdb_doc_embed=lcdb_doc_embed,
                                            lcdb_sr_embed=lcdb_sr_embed,
                                            lcdb_jssdk_embed=lcdb_jssdk_embed,
                                            lcdb_wc_embed=lcdb_wc_embed,
                                            lcdb_spec_embed=lcdb_spec_embed,
                                            generate_model=generate_model)




if __name__ == "__main__":
    query = "如何設定與使用EasyBuilder Pro的MQTT物件"
    # query = "Hello,problem on editor iti is impossible to drag any object in other position for exemple I select one object nd copy and past it then try to drag the copied object to another place no work...Thank you"
    # query = "Hi, today is good weather!! thanks"
    # query="how to get the error information with my iR-COP? are there any address definition?"
    # query="""已知Macro中有一個函式SetData(variable, "local HMI", LB, 1 or 0, 1)可以透過輸入variable = ON or OFF來觸發一個LB位置的狀態。我想要LB0的位置代表window_10，輸入0代表close視窗，輸入1代表開啟。現在我想要用這個狀態控制視窗切換，請問我要怎麼設計Macro?當中添加5分鐘delay然後切換windows_10視窗"""
    # query = "please provide me an example for JS Object SDK. I'm  beginner. especially for mousearea~"
    # no streaming
    # query = """cmt-G05 Spec是什麼? 提供表格並用中文回答"""
    # output_json = generate_answer_zeroshotplanner(query,[["Hi ","Hi, how can i assist u?"]])
    # print(output_json['replied_message'])
    # streaming
    import os
    result = ''
    for word in generate_stream_answer_zeroshotplanner(query,[["Hi ","Hi, how can i assist u?"]]):
        result += word
        os.system('cls')
        print(result, end='\r')
    
    