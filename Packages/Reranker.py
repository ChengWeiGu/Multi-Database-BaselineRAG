# -*- coding: utf-8 -*-
import numpy as np
import nltk
from nltk.corpus import stopwords
from rank_bm25 import BM25Okapi
import configparser
from FlagEmbedding import BGEM3FlagModel
import DatabaseProcess
import time
from sklearn.feature_extraction.text import CountVectorizer
import jieba
import warnings
import logging
warnings.filterwarnings("ignore", category=UserWarning, message="Your stop_words may be inconsistent")
logging.getLogger("jieba").setLevel(logging.ERROR)

config=configparser.ConfigParser()
config.read("Config.ini")

stop_words_path = config['RERANKER']['cn_stop_words_path']
# 下载停用词列表（如果尚未下载）
nltk.download('stopwords')


#去除停止文字
def tokenize(text, stop_word_list):
    cut_words = list(jieba.cut(text))
    new_cut_words = []
    for word in cut_words:
        if word not in stop_word_list:
            new_cut_words.append(word)
        else:
            pass 
    return new_cut_words


# 產生中文stop words
def generate_cn_stop_words():
    stop_word_list = []
    with open(stop_words_path,'r', encoding = 'utf-8-sig') as f:
        stop_word_list = [line.strip('\n') for line in f.readlines()]
        # print(stop_word_list)
        f.close()
    return stop_word_list


# 加载中/英文停用词列表
english_stop_words = stopwords.words('english')
chiinese_stop_words = generate_cn_stop_words()
stop_words = english_stop_words + chiinese_stop_words
stop_words = list(set(stop_words))


def reranker_countvectorizer(query,res_docs,top_k:int=10):
    vectorizer = CountVectorizer()
    # tokenize
    seg_list = jieba.cut(query)
    seg_text = " ".join(seg_list)
    vectorizer = CountVectorizer(stop_words=stop_words)
    X = vectorizer.fit_transform([seg_text])
    # document 處理
    token_texts = []
    for doc in res_docs:
        seg_list_temp = jieba.cut(doc[0].page_content) # doc: (document, score)
        seg_text_temp = " ".join(seg_list_temp)
        token_texts.append(seg_text_temp)
    Y = vectorizer.transform(token_texts)
    # print(Y.toarray())
    # 分數處理
    scores = np.sum(Y.toarray(), axis=1)
    reorder_idx = np.argsort(scores)[::-1][:top_k]
    reorder_res_docs = [res_docs[idx] for idx in reorder_idx]
    # 打印词汇表
    # print("Vocabulary:", vectorizer.get_feature_names_out())
    return reorder_res_docs


# BM25 Retriever
def reranker_bm25(query,res_docs,top_k:int=10):
    tokenized_corpus  = []
    for doc in res_docs:
        tokenized_corpus.append(tokenize(doc[0].page_content,stop_words))
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = tokenize(query,stop_words)
    scores = bm25.get_scores(tokenized_query)
    # print(scores)
    reorder_idx = np.argsort(scores)[::-1][:top_k]
    reorder_res_docs = [res_docs[idx] for idx in reorder_idx]
    return reorder_res_docs


# rerank the retrieval data
def rerank_base(database_list, top_k):
    # Collect score : (db_ind, db_data_ind, score)
    score = []
    for db_ind, database in enumerate(database_list):       
        for data_ind , data in enumerate(database):
            score.append((db_ind, data_ind, data[1]))
    
    # Rerank        
    sorted_score = sorted(score, key=lambda x: x[-1], reverse=True)
    sorted_score = sorted_score[:top_k]
    
    # Select rerank data from database_list using sorted_score
    select_database_list = [[] for i in range(len(database_list))]
    
    for top_data in sorted_score:
        select_database_list[top_data[0]].append(database_list[top_data[0]][top_data[1]])
    
    for i in range(len(database_list)):
        print(f"reorder db-{i}: ",len(select_database_list[i]))
          
    return select_database_list




# use LLM for test
def rerank_bgem3_dense(query,res_docs,top_k:int=10,mode:str='Dense'):
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    model.model.eval()
    sentences_1 = [query]
    sentences_2 = [doc[0].page_content for doc in res_docs]
    ts = time.time()
    embeddings_1 = model.encode(sentences_1,
                               batch_size=12,
                               max_length=1536)['dense_vecs']
    embeddings_2 = model.encode(sentences_2)['dense_vecs']
    similarity = embeddings_1 @ embeddings_2.T
    scores = similarity[0]
    reorder_idx = np.argsort(scores)[::-1][:top_k]
    reorder_res_docs = [res_docs[idx] for idx in reorder_idx]
    print(f"T cost: {time.time() - ts}")
    print(similarity)
    return reorder_res_docs


def rerank_bgem3_colbert(query,res_docs,top_k:int=10):
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    model.model.eval()
    sentences_1 = [query]
    sentences_2 = [doc[0].page_content for doc in res_docs]
    len_setences2 = len(sentences_2)
    ts = time.time()
    output_1 = model.encode(sentences_1,
                                return_dense=True,
                                return_sparse=True,
                                return_colbert_vecs=True)
    output_2 = model.encode(sentences_2,
                                return_dense=True,
                                return_sparse=True,
                                return_colbert_vecs=True)
    scores = []
    for i in range(len_setences2):
        _score = model.colbert_score(output_1['colbert_vecs'][0], output_2['colbert_vecs'][i]).item()
        scores.append(_score)
    reorder_idx = np.argsort(scores)[::-1][:top_k]
    reorder_res_docs = [res_docs[idx] for idx in reorder_idx]
    print(f"T cost: {time.time() - ts}")
    return reorder_res_docs
    


if __name__ == "__main__":
    query_list = ["EasyAccess 2.0支援那些人機型號與OS版本?",
                  "怎麼樣開始使用流量卡? 請提供簡單的步驟",
                  "EA2.0 Error Code有哪些?",
                  "EasyAccess 2.0 中的Domain是甚麼?", 
                  "介紹EA2.0中的Domain是甚麼? ",
                  "Weincloud Dashboard支援的人機型號?",
                  "EA2.0目前同一個人機最多僅能被幾個用戶連接?",
                  "Hello. How can I connect to the OPC DA server? from cmT-SVR 102","您好，想請問QJ71C24N的設備類型要如何選擇?",
                  "How to use HMI Model: MT8150IE ? Software Version ? How to select Model in software ?",
                  "請問我可以改變人機設備從CMT2108X變成MT8102ie嗎?",
                  "如何透過網路下載 Project","what is 事件甘特圖?",
                  "How to decompile files?","Priority level in evenlog?",
                  "For SQL Query, what function is LW-400?","請介紹 Single Pulse Counter 單脈波計數器",
                  "HMI TCP Port中EasyDiagnoser的default port是多少?","use jssdk to read Device/PLC data",
                  "how to get size of data in jssdk","send a post request in jssdk"]
    
    query = query_list[20]
    print(query)
    ##### test for wc
    # chroma_login_info = {"chromadb_path":config['CHROMA_DB']['weincloud_chromadb_path'],
    #                     "collection_name":config['CHROMA_DB']['weincloud_collection_name'],
    #                     "embedding_function":DatabaseProcess.embedding_function}
    
    #####test for sr
    # chroma_login_info = {"chromadb_path":config['CHROMA_DB']['sr_chromadb_path'],
    #                         "collection_name":config['CHROMA_DB']['sr_collection_name'],
    #                         "embedding_function":DatabaseProcess.embedding_function}
    
    #####test for doc
    # chroma_login_info = {"chromadb_path":config['CHROMA_DB']['doc_chromadb_path'],
    #                     "collection_name":config['CHROMA_DB']['doc_collection_name'],
    #                     "embedding_function":DatabaseProcess.embedding_function}
    
    
    #####test for js
    chroma_login_info = {"chromadb_path":config['CHROMA_DB']['JsObjSdk_chromadb_path'],
                        "collection_name":config['CHROMA_DB']['JsObjSdk_collection_name'],
                        "embedding_function":DatabaseProcess.embedding_function}
    
    #####test for spec
    # chroma_login_info = {"chromadb_path":config['CHROMA_DB']['spec_chromadb_path'],
    #                     "collection_name":config['CHROMA_DB']['spec_collection_name'],
    #                     "embedding_function":DatabaseProcess.embedding_function}
    
    lc_obj = DatabaseProcess.LangchainChromaDB(chroma_login_info)
    lc_obj.init_database()
    res_docs = lc_obj.lc_similarity_search_with_score_topk(query=query,k=30)
    for i, res in enumerate(res_docs): print(f'index_{i+1}\n',res[0],'\n')
    print("="*120,"\n\n")
    
    
    ts = time.time()
    finalres = reranker_bm25(query,res_docs,top_k=30)
    # finalres = reranker_countvectorizer(query,res_docs,top_k=15)
    # finalres = rerank_bgem3_dense(query,res_docs,top_k=30)
    # finalres = rerank_bgem3_colbert(query,res_docs,top_k=30)
    for i, res in enumerate(finalres): print(f'index_{i+1}\n',res[0],'\n')
    print(f"T cost: {time.time() - ts}")
    
    pass