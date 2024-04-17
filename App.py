# -*- coding: utf-8 -*-
import sys
sys.path.append("Packages")
from flask import Flask, render_template, request, jsonify, Response
from Packages import Generation
from Packages import OpenAIFunction
import time
import datetime
import socket
import json
from waitress import serve
from os.path import basename, join, exists, dirname, splitext
import configparser
from os import mkdir


config=configparser.ConfigParser()
config.read("Config.ini")
software_version = config['SETTINGS']['version']
max_chat_history = int(config['SETTINGS']['max_chat_history'])
feedback_file_path = config['SETTINGS']['feedback_file_path']
# print('max_chat_history: ',max_chat_history)


current_ip = socket.gethostbyname(socket.gethostname())
app = Flask(__name__)

'''
score : select_score.value,
assist : select_assist.value,
is_OK : select_OK.value,
feedback : input_text_feedback.value,
userAgent : userAgent,
username : username,
query : inputText.value,
generation : output_text.value
'''
# write log for feedback
def feedback_logger(filename,data):
    # print(data)
    cols = ['datetime']
    vals = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    for k, v in data.items():
        if k not in ["qa_retrieval","doc_retrieval"]:
            cols.append(k)
            vals.append(str(v))
    
    #添加數據行
    html_data = "<tr>"
    for val in vals:
        html_data += "<td>{}</td>".format(val)
    html_data += "</tr>"
    
    final_html = ""
    # 添加表頭
    if not exists(filename):
        html = "<table border='1'>"
        html += "<tr>"
        for col in cols:
            html += "<th>{}</th>".format(col)
        html += "</tr>"
        html += html_data
        html += "</table>"
        final_html = html
    else:
        #刪除"</table>"
        with open(filename,'r+', encoding='utf-8') as f:
            content = f.read()
            last_table_index = content.rfind("</table>")
            if last_table_index != -1:
                content = content[:last_table_index]
                content += html_data
                content += "</table>"
                final_html = content
    
    with open(filename,'w', encoding="utf-8") as f:
        f.write(final_html)
    print("send feedback successifully")

# Home Page
@app.route('/')
def index():
    # return render_template('index.html')
    return render_template('index-chat.html')



# sw version
@app.route('/settings', methods=['GET'])
def get_sw_settings():
    return jsonify({'status':'success',
                    'max_chat_history':max_chat_history,
                    'version':software_version})


# rag route
@app.route('/generate_text', methods=['POST'])
def generate_text():
    ###define output columns####
    output_text = ""
    qa_text_body = ""
    doc_text_body=""
    status = "fail"
    qa_retrieved_ids = []
    
    # acquire input question from frontend
    json_str = request.data.decode('utf-8')
    json_data = json.loads(json_str)
    query = json_data["input_text"]
    select_generate_model = json_data["select_generate_model"]
    history_messages = json_data['history_messages']
    client_ip = request.remote_addr
    print("Client IP: %s\nSelect Gen Model: %s\nQuery: %s" % (client_ip,select_generate_model,query))
    # print(history_messages)
    
    time_start = time.time()
    # use planner to generate answer
    rag_output_json = Generation.generate_answer_zeroshotplanner(query=query, 
                                                                 history_messages = history_messages, 
                                                                 generate_model=select_generate_model)
    # redefing output
    if rag_output_json['status'] == 'success':
        output_text = rag_output_json["replied_message"]
        qa_text_body = rag_output_json["qa_text_body"]
        qa_retrieved_ids = rag_output_json["qa_retrieved_ids"]
        doc_text_body = rag_output_json["doc_text_body"]
        status = 'success'
    else:
        output_text = rag_output_json["error_reason"]
    # print("Answer: ",output_text)
    time_end = time.time()
    time_cost = time_end - time_start
    print("time cost(sec): ",time_cost)
    return jsonify({'status':status,
                    'output_text': output_text,
                    'qa_text_body': qa_text_body,
                    'doc_text_body': doc_text_body,
                    'qa_retrieved_ids':qa_retrieved_ids})



# rag route
@app.route('/generate_stream_text', methods=['POST'])
def generate_stream_text():
    # acquire input question from frontend
    json_str = request.data.decode('utf-8')
    json_data = json.loads(json_str)
    query = json_data["input_text"]
    select_generate_model = json_data["select_generate_model"]
    history_messages = json_data['history_messages']
    client_ip = request.remote_addr
    print("Client IP: %s\nSelect Gen Model: %s\nQuery: %s" % (client_ip,select_generate_model,query))
    # print(history_messages)
    # use planner to generate answer
    return Response(Generation.generate_stream_answer_zeroshotplanner(query=query, 
                                                                      history_messages = history_messages, 
                                                                      generate_model=select_generate_model), 
                    mimetype='text/event-stream')



@app.route('/generate_image',methods=['POST'])
def generate_image():
    ## define output
    output_text=""
    status = "fail"
    image_descr=""
    
    json_str = request.data.decode('utf-8')
    json_data = json.loads(json_str)
    prompt = json_data["input_text"]
    client_ip = request.remote_addr
    print("Client IP: %s\nQuery: %s\nModel: %s" % (client_ip,prompt,"Dalle3"))
    
    time_start = time.time()
    if prompt != "":
        image_gen_result = OpenAIFunction.generate_image_openai(prompt)
        if image_gen_result['status'] == 'success':
            status = 'success'
            output_text = image_gen_result['image_url']
            image_descr = image_gen_result['revised_prompt']
        else:
            output_text = image_gen_result['error_reason']
    else:
        output_text = "Your query cannot be empty! Please Try again."
    
    time_end = time.time()
    time_cost = time_end - time_start
    print("time cost(sec): ",time_cost)
    
    return jsonify({
                    'status':status,
                    'prompt':prompt,
                    'image_descr':image_descr,
                    'output_text':output_text
                })


# feedback route (files + comment)
@app.route('/feedback', methods=['POST'])
def collect_feedback():
    # return cols
    status = 'fail'
    error_reason = ""
    # acquire feedback from frontend
    json_str = request.form['json_data']
    json_data = json.loads(json_str)
    uploaded_file = request.files.get('file')
    json_data["client_ip"] = request.remote_addr
    query = json_data["query"]
    generation_ans = json_data["generation"]
    # to check if folder exists. if not, then create folder
    if not exists(feedback_file_path):
        mkdir(feedback_file_path)
    xml_filename = feedback_file_path + "/" + datetime.datetime.now().strftime("Feedback_%Y%m%d.html")
    if (query.replace(" ","") != "") and (generation_ans != ""):
        try:
            if uploaded_file is not None:
                uploaded_filename = uploaded_file.filename
                target_filename = feedback_file_path + "/" + uploaded_filename
                # rename file if exists
                if exists(target_filename):
                    name, extension = splitext(uploaded_filename)
                    new_filename = "{}{}{}".format(name,
                                                    datetime.datetime.now().strftime("_%Y%m%d%H%M%S"),
                                                    extension)
                    target_filename = feedback_file_path + "/" + new_filename
                uploaded_file.save(target_filename)
            else:
                target_filename = ""
            
            json_data["uploaded_filename"] = target_filename
            status = 'success'
        except Exception as e:
            error_reason = str(e)
        else:
            # write log
            feedback_logger(filename=xml_filename, data=json_data)
    else:
        error_reason = "The website has been freshed, please ask a new question and try again."
    # print(json_data)
    return  jsonify({"status":status,
                    "error_reason":error_reason})



if __name__ == '__main__':
    # app.run(host=current_ip,port=6688,debug=True)
    # app.run(host="127.0.0.1",port=6688,debug=True)
    # serve(app, host="127.0.0.1",port=6688,ident=True)
    serve(app, host=current_ip,port=6688,ident=True)
    # serve(app, host=current_ip,port=6689,ident=True)
    pass
