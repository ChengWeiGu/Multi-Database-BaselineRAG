# -*- coding: utf-8 -*-
import pyodbc
import pandas as pd
import configparser
import pickle
import chromadb
from langchain_community.vectorstores.chroma import Chroma
from langchain.docstore.document import Document
from langchain_openai import AzureOpenAIEmbeddings
import OpenAIFunction


config=configparser.ConfigParser()
config.read("Config.ini")
# SR DB Setting
sr_login_info={"driver":config['SR_DB']['driver'],
               "server":config['SR_DB']['server'],
                "database":config['SR_DB']['database'],
                "username":config['SR_DB']['username'],
                "password":config['SR_DB']['password']}
# Chroma db setting
embedding_function=AzureOpenAIEmbeddings(openai_api_version=OpenAIFunction.embedding_settings['api_version'],
                                        openai_api_type=OpenAIFunction.embedding_settings['api_type'],
                                        openai_api_key=OpenAIFunction.embedding_settings['api_key1'],
                                        azure_endpoint=OpenAIFunction.embedding_settings['endpoint'],
                                        azure_deployment=OpenAIFunction.embedding_settings['embedding_model'])

chroma_login_info={"chromadb_path":config['CHROMA_DB']['sr_chromadb_path'],
                   "collection_name":config['CHROMA_DB']['sr_collection_name'],
                   "embedding_function":embedding_function}

class SRDatabase:
    def __init__(self,login_info):
        self.connect_str="Driver={%s};Server=%s;Database=%s;uid=%s;pwd=%s" % (login_info['driver'],login_info['server'],login_info['database'],login_info['username'],login_info['password'])
    def select_tbl_merge_all(self):
        strSQL="""SELECT * FROM [Weintek_Web].[dbo].[SR_Message] it
                LEFT JOIN [Weintek_Web].[dbo].[SR_Thread] h ON it.SR_Uid = h.SR_Uid
                LEFT JOIN [Weintek_Web].[dbo].[SR_Files] f ON it.SR_Uid = f.SR_Uid
                WHERE h.Created_Date >= DATEADD(YEAR,-10,GETDATE())
                AND h.SR_Status = 'Closed' AND h.SR_Replier <> 'seanhuang'"""
        conn = pyodbc.connect(self.connect_str)
        cursor = conn.cursor()
        df = pd.read_sql(strSQL,conn)
        cursor.close()
        conn.close()
        return df
    '''
    1. 只取closed+replied狀態的SR
    2. 承1，近14天內的replied狀態不算數
    3. question or reply 字數皆少於60濾掉
    4. seanhuang的reply濾掉
    5. 如果user一開始發問有附加檔案的也先濾掉 (目前先不考慮一開始只有檔案的發問)
    '''
    def select_tbl_customized(self,where_condition=None):
        strSQL="""WITH CTE0 AS (
                    SELECT * FROM [Weintek_Web].[dbo].[SR_Files]
                    WHERE SR_Message_Uid = 1
                    ), CTE1 AS (
                    SELECT 
                    it.SR_Uid, it.SR_Message_Uid, it.SR_Uid+'_'+ CONVERT(VARCHAR,it.SR_Message_Uid) AS PK,it.User_Uid, it.Post_Date, it.SR_Message, it.SR_Reply, it.SR_Replier, it.SR_ReplyDate, it.SR_ReplyFile, it.SR_ReplyFileName,
                    h.SR_Subject, h.SR_Status, h.EmailNotify, h.SR_Category, h.Created_Date, h.Posts, h.Replies, h.SN, h.MODEL, h.OS, h.Firmware_Version, h.PLC, h.Driver, h.PLC_IF, 
                    h.HMI_COMport, h.Baud_Rate, h.Data_bits, h.Parity, h.Stop_bits, h.Delay, h.LastUpdate_User, h.LastUpdate_Date, h.SR_PType, h.SR_PUid, h.SR_Replier as SR_ORG_Replier,
                    f.SR_Files1, f.SR_Files1_Name, f.SR_Files1_Date,
                    CASE WHEN h.LastUpdate_Date >= DATEADD(DAY,-14,GETDATE()) and h.SR_Status = 'Replied' THEN 'N' ELSE 'Y' END AS Recall_Replied
                    FROM [Weintek_Web].[dbo].[SR_Message] it
                    LEFT JOIN [Weintek_Web].[dbo].[SR_Thread] h ON it.SR_Uid = h.SR_Uid
                    LEFT JOIN [Weintek_Web].[dbo].[SR_Files] f ON it.SR_Uid = f.SR_Uid AND it.SR_Message_Uid = f.SR_Message_Uid
                    WHERE h.SR_Status in ('Closed','Replied') AND h.SR_Replier <> 'seanhuang'
                    AND it.SR_Uid not in (SELECT CTE0.SR_Uid FROM CTE0)
                    AND LEN(it.SR_Message) > 60 AND LEN(it.SR_Reply) > 60
                    )
                    SELECT * FROM CTE1
                    WHERE CTE1.Recall_Replied = 'Y'"""
        if where_condition is not None:
            strSQL+=f" AND {where_condition}"
        conn = pyodbc.connect(self.connect_str)
        cursor = conn.cursor()
        df = pd.read_sql(strSQL,conn)
        cursor.close()
        conn.close()
        return df
    def select_tbl_testing_data(self,where_condition=None):
        strSQL="""WITH CTE0 AS (
                    SELECT * FROM [Weintek_Web].[dbo].[SR_Files]
                    WHERE SR_Message_Uid = 1
                    ), CTE1 AS (
                    SELECT 
                    it.SR_Uid, it.SR_Message_Uid, it.SR_Uid+'_'+ CONVERT(VARCHAR,it.SR_Message_Uid) AS PK,it.User_Uid, it.Post_Date, it.SR_Message, it.SR_Reply, it.SR_Replier, it.SR_ReplyDate, it.SR_ReplyFile, it.SR_ReplyFileName,
                    h.SR_Subject, h.SR_Status, h.EmailNotify, h.SR_Category, h.Created_Date, h.Posts, h.Replies, h.SN, h.MODEL, h.OS, h.Firmware_Version, h.PLC, h.Driver, h.PLC_IF, 
                    h.HMI_COMport, h.Baud_Rate, h.Data_bits, h.Parity, h.Stop_bits, h.Delay, h.LastUpdate_User, h.LastUpdate_Date, h.SR_PType, h.SR_PUid, h.SR_Replier as SR_ORG_Replier,
                    f.SR_Files1, f.SR_Files1_Name, f.SR_Files1_Date,
                    CASE WHEN h.LastUpdate_Date >= DATEADD(DAY,-14,GETDATE()) and h.SR_Status = 'Replied' THEN 'N' ELSE 'Y' END AS Recall_Replied
                    FROM [Weintek_Web].[dbo].[SR_Message] it
                    LEFT JOIN [Weintek_Web].[dbo].[SR_Thread] h ON it.SR_Uid = h.SR_Uid
                    LEFT JOIN [Weintek_Web].[dbo].[SR_Files] f ON it.SR_Uid = f.SR_Uid AND it.SR_Message_Uid = f.SR_Message_Uid
                    WHERE h.SR_Status in ('Closed','Replied') AND h.SR_Replier <> 'seanhuang'
                    AND it.SR_Uid not in (SELECT CTE0.SR_Uid FROM CTE0)
                    AND LEN(it.SR_Message) > 60 AND LEN(it.SR_Reply) > 60
                    )
                    SELECT * FROM CTE1
                    WHERE CTE1.Recall_Replied = 'N'"""
        if where_condition is not None:
            strSQL+=f" AND {where_condition}"
        conn = pyodbc.connect(self.connect_str)
        cursor = conn.cursor()
        df = pd.read_sql(strSQL,conn)
        cursor.close()
        conn.close()
        return df
    def save2pkl(self,df,filename=r"save.pkl"):
        with open(filename,"wb") as file:
            pickle.dump(df,file,protocol=pickle.HIGHEST_PROTOCOL)
        print("save to pkl succeed")
        



class LangchainChromaDB:
    def __init__(self,login_info):
        self.top_k = 10
        self.set_log_info(login_info)
    def set_log_info(self,new_login_info):
        self.login_info = new_login_info
    def set_topk(self,k:int):
        self.top_k = k
    def init_database(self):
        print("Init db...")
        self.client = chromadb.PersistentClient(
                                path=self.login_info['chromadb_path']
                            )
        self.collection = self.client.get_or_create_collection(
                                name=self.login_info['collection_name']
                            )
        print("Available Collections: ", self.client.list_collections())
        print("Init db done\n")
    def wrap_data2doc(self,ids=[],texts=[],metadatas=[]):
        documents=[]
        for id, text, metadata in zip(ids,texts,metadatas):
            page = Document(
                        page_content=text, 
                        metadata=metadata,
                        id=id
                    )
            documents.append(page)
        return documents
    def insert_data2db(self,documents):
        print("Insert data...")
        self.lcdb = Chroma.from_documents(
                                client=self.client,
                                documents=documents,
                                collection_name=self.login_info['collection_name'],
                                embedding=self.login_info['embedding_function']
                            )
        print("After insert, total Data Count: ", self.collection.count())
        print("Insert data done\n")
    def lc_similarity_search_with_score(self,query):
        self.lcdb = Chroma(
                        client=self.client,
                        collection_name=self.login_info['collection_name'],
                        embedding_function=self.login_info['embedding_function']
                    )
        res_docs = self.lcdb.similarity_search_with_score(query,k=self.top_k)
        # print("Top 2 data: ",self.collection.peek(2))
        # print("Total Data Count: ", self.lcdb._collection.count())
        return res_docs
    def lc_similarity_search_with_score_topk(self,query,k):
        self.lcdb = Chroma(
                        client=self.client,
                        collection_name=self.login_info['collection_name'],
                        embedding_function=self.login_info['embedding_function']
                    )
        res_docs = self.lcdb.similarity_search_with_score(query,k)
        return res_docs
        

    

if __name__ == "__main__":
    # test azure embedding
    # query_res = embedding_function.embed_query("this is a test document")
    # print(query_res)
    
    # get srdb data
    # srdb = SRDatabase(sr_login_info)
    # df_res = srdb.select_tbl_customized()
    # df_res = srdb.select_tbl_testing_data()
    # srdb.save2pkl(df_res,"customized_res.pkl")
    # print(f"total_len_df:{len(df_res)}")
    # print(df_res.head(20))
    # print(df_res.to_dict(orient='records')[:20])
    
    # test searching
    # query = "I asked how to make a simple project in CoDeSys (Weintek Built-in CODESYS)?"
    # lc_obj = LangchainChromaDB(chroma_login_info)
    # lc_obj.init_database()
    # res_docs = lc_obj.lc_similarity_search_with_score(query)
    # print(res_docs)
    
    chroma_login_info = {"chromadb_path":config['CHROMA_DB']['weincloud_chromadb_path'],
                        "collection_name":config['CHROMA_DB']['weincloud_collection_name'],
                        "embedding_function":embedding_function}
    lc_obj = LangchainChromaDB(chroma_login_info)
    lc_obj.init_database()
    res_docs = lc_obj.lc_similarity_search_with_score_topk(query="EasyAccess 2.0支援那些人機型號與OS版本?請用表格顯示",k=25)
    print(res_docs)
    
    pass