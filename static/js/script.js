//define var
const chatbox = document.getElementById("chatbox");
const userInput = document.getElementById("user-input");
const submitButton = document.getElementById("submit_button");
const sendButton = document.getElementById("send_button");
const clearChatButton = document.getElementById("clear_chat_button");
const select_mode = document.getElementById("select_mode");
const fileInput = document.getElementById("fileInput");
const srcRef = document.getElementById("input_text_srcRef"); //來源網址
var software_version = "";
var max_chat_history = 5;
var lastInputMessage = "";
var lastOutputMessage = "";
var chat_controller;
var img_controller;

// initially, get version/max_chat_history from backend
init_software_settings();


//send feedback
sendButton.addEventListener('click', function() {
    var select_score = document.getElementById('select_score');
    var select_assist = document.getElementById('select_assist');
    var select_OK = document.getElementById('select_OK');
    var input_text_feedback = document.getElementById('input_text_feedback');
    var userAgent = navigator.userAgent;
    var username = localStorage.getItem('username');
    var select_generate_model = "";
    if (select_mode.value == "chat_gen") {
        select_generate_model = "gpt4";
    } else {
        select_generate_model = "dalle3";
    }
    //formdata包裝
    let formData = new FormData();
    let json_data = {
        score : select_score.value,
        assist : select_assist.value,
        is_OK : select_OK.value,
        feedback : input_text_feedback.value,
        userAgent : userAgent,
        username : username,
        query : lastInputMessage,
        generation : lastOutputMessage,
        retrieval_generate_model : select_generate_model,
        software_version : software_version,
        srcRef : srcRef.value
    }
    let file = fileInput.files[0];
    formData.append('json_data',JSON.stringify(json_data));
    formData.append('file',file);
    //post request
    fetch('/feedback',{
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status == 'success'){
            alert("Send Successifully");
        } else {
            alert(data.error_reason);
        }   
    })
})


// send request with enter when cursor in textarea
userInput.addEventListener('keydown',function(event){
    if (event.key == 'Enter' && !event.shiftKey && submitButton.textContent == 'Submit' && userInput.value.trim() != '') {
        event.preventDefault(); //防止 textarea換行
        submitButton.click();
    };
})

//clear all chat content
clearChatButton.addEventListener('click', function() {
    chatbox.innerHTML = `<div class="mb-2 robot-message-container">
                            <p>
                                <div class="icon">
                                    <img src="/static/icon/chatbot_v1.svg" alt="Your Icon" class="custom-robot-icon">
                                </div>
                                <div class="robot-message">
                                    <p class="bg-gray-200 text-gray-700 rounded-lg py-2 px-4 inline-block">Hi, how may I help you today?</p>
                                </div>
                            </p>
                        </div>`;
    saveChatItem();
});



function enableBtn() {
    submitButton.textContent = "Submit";
    submitButton.classList.remove('stop_button','fade-loop');
    sendButton.disabled = false;
    clearChatButton.disabled = false;
    sendButton.classList.remove('btn_disabled');
    clearChatButton.classList.remove('btn_disabled');
}

function disableBtn() {
    submitButton.textContent = "Stop";
    submitButton.classList.add('stop_button','fade-loop');
    sendButton.disabled = true;
    clearChatButton.disabled = true;
    sendButton.classList.add('btn_disabled');
    clearChatButton.classList.add('btn_disabled');
}


function addUserMessage(message) {
    const messageElement = document.createElement("div");
    messageElement.classList.add("mb-2", "text-right","user-message-container");
    message = PreventHtml2Code(message); //preprocess
    messageElement.innerHTML = `
                                <div class="icon">
                                    <img src="/static/icon/user_v1.svg" alt="Your Icon" class="custom-user-icon">
                                </div>
                                <div class="user-message">
                                    <div class="bg-blue-500 text-white rounded-lg py-2 px-4 inline-block">${message}</div>
                                </div>`;
    chatbox.appendChild(messageElement);
    chatbox.scrollTop = chatbox.scrollHeight;
}


function addBotMessage(message) {
    const messageElement = document.createElement("div");
    messageElement.classList.add("mb-2", "robot-message-container");
    //正則化處理
    message = regex_flow(message);
    messageElement.innerHTML = `
                                <div class="icon">
                                    <img src="/static/icon/chatbot_v1.svg" alt="Your Icon" class="custom-robot-icon">
                                </div>
                                <div class="robot-message">
                                    <div class="bg-gray-200 text-gray-700 rounded-lg py-2 px-4 inline-block">${message}</div>
                                </div>`;
    
    chatbox.appendChild(messageElement);
    chatbox.scrollTop = chatbox.scrollHeight;
}


function removeLastMessage() {
    // 獲取最後一個子元素
    var lastMessage = chatbox.lastChild;
    // 如果最後一個子元素存在且不是 null，則將其從 DOM 中刪除
    if (lastMessage !== null) {
        chatbox.removeChild(lastMessage);
    }
}


// customize the bot message for image generation
function addBotMessageForImageMode(image_url,image_descr="") {
    const messageElement = document.createElement("div");
    messageElement.classList.add("mb-2", "robot-message-container");
    let message = `Sure, here is your image:\n
                    <a href="${image_url}" target="_blank" style="color:blue; font-size:14px;">${image_url}</a>\n
                    <img src="${image_url}" alt="${image_descr}">`
    //換行處理
    message = message.replace(/\n/g,"<br>");

    messageElement.innerHTML = `
                                <div class="icon">
                                    <img src="/static/icon/chatbot_v1.svg" alt="Your Icon" class="custom-robot-icon">
                                </div>
                                <div class="robot-message">
                                    <div class="bg-gray-200 text-gray-700 rounded-lg py-2 px-4 inline-block">${message}</div>
                                </div>`;
    
    chatbox.appendChild(messageElement);
    chatbox.scrollTop = chatbox.scrollHeight;
}



// animation for image generation
function addBotMessageAnimation() {
    var message = "Generating ··";
    const messageElement = document.createElement("div");
    message = message.replace(/\n/g,"<br>");
    // fade-loop
    messageElement.classList.add("mb-2", "robot-message-container","fade-loop",); // 添加 fade-loop 類名
    messageElement.innerHTML = `
                                <div class="icon">
                                    <img src="/static/icon/chatbot_v1.svg" alt="Your Icon" class="custom-robot-icon">
                                </div>
                                <div class="robot-message">
                                    <p id="bot_animate" class="bg-gray-200 text-gray-700 rounded-lg py-2 px-4 inline-block">${message}</p>
                                </div>`;
    chatbox.appendChild(messageElement);
    chatbox.scrollTop = chatbox.scrollHeight;
    // text loop
    var animate_text = document.getElementById('bot_animate');
    var loadingInterval = setInterval(function(){
        animate_text.textContent += '···';
        if (animate_text.textContent.length > 60) {
            animate_text.textContent = message;
        }
    },500);
}


// transform historical messages into QA list
function acquire_history_messages(qa_cnt) {
    var robotMessages = document.querySelectorAll('.robot-message div'); //第一個是p忽略
    var userMessages = document.querySelectorAll('.user-message div');
    var lastQAMessages = [];
    if (userMessages.length > 0) {
        var startIndex = Math.max(userMessages.length - qa_cnt,0);
        for (var i = startIndex; i < userMessages.length; i++) {
            lastQAMessages.push([userMessages[i].textContent.trim(),robotMessages[i].textContent.trim()]);
        }
    }
    return lastQAMessages;
}


// get info and settings from backend
function init_software_settings() {
    var divElement = document.getElementById("version_div");
    fetch('/settings')
    .then(response => response.json())
    .then(data => {
        // sw version
        software_version = data.version;
        divElement.innerText = software_version;
        // max history chat considered
        max_chat_history = data.max_chat_history;
    })
    .catch(error => {
        console.error('Error:', error);
    })
}



