//submit for generation
submitButton.addEventListener('click', function() {
    // chat mode
    if (submitButton.textContent == 'Submit' && select_mode.value == 'chat_gen') {
        // define gen model
        var select_generate_model = "gpt4";
        //前置流程
        disableBtn();
        lastInputMessage = userInput.value.trim();
        addUserMessage(lastInputMessage);
        userInput.value = "";
        // add bot message and cursor
        let now = getStringTime();
        let BotIDs = addNewBotMessageID(now);
        const botMsgDivElement = document.getElementById(BotIDs[0]);
        //抓取歷史資料 => []
        var history_messages = acquire_history_messages(max_chat_history);
        chat_controller = new AbortController();
        // post data to backend
        fetch('/generate_stream_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ input_text: lastInputMessage ,
                                    select_generate_model : select_generate_model ,
                                    history_messages : history_messages
                                }),
            signal: chat_controller.signal //cancel
        })
        .then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let result = "";
            let finalData = {}; //empty object
            //遞歸讀取
            const read = () => {
                return reader.read().then(({ done, value }) => {
                    if (done) {
                        return { result, finalData };
                    }
                    const chunk = decoder.decode(value);
                    result += chunk;
                    // 保持換行顯示, cursor保持在最後, real-time doing regex
                    let realTimeMsg = regex_flow(result);
                    botMsgDivElement.innerHTML = `${realTimeMsg} <span id="${BotIDs[1]}" class="cursor">|</span>`
                    lastOutputMessage = result;
                    chatbox.scrollTop = chatbox.scrollHeight;

                    return read();
                });
            };
            
            return read();
        })
        .then(({result,finalData}) => {
            //移除cursor sapn "|"
            var spanElements = document.querySelectorAll(".robot-message .cursor");
            spanElements.forEach(function(span){
                span.parentNode.removeChild(span);
            });
            //save to local storage
            saveChatItem();
            //rest controller
            chat_controller = null;
            //enable button
            enableBtn();
        });
    // image mode
    } else if (submitButton.textContent == 'Submit' && select_mode.value == 'image_gen') {
        //前置流程
        lastInputMessage = userInput.value.trim();
        disableBtn();
        addUserMessage(lastInputMessage);
        addBotMessageAnimation();
        userInput.value = "";
        img_controller = new AbortController();
        //post prompt to backend
        fetch('/generate_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ input_text: lastInputMessage}),
            signal: img_controller.signal //cancel
        })
        .then(response => response.json())
        .then(data => {
                removeLastMessage(); //bot animation
                if (data.status == 'success'){
                    addBotMessageForImageMode(data.output_text,data.image_descr);
                } else {
                    addBotMessage(data.output_text);
                }
                lastOutputMessage = data.output_text;
                saveChatItem();
                img_controller = null;
                enableBtn();
        });
    } else {
        if (select_mode.value=="chat_gen") {
            chat_controller.abort();
            chat_controller = null;
        } else { 
            img_controller.abort();
            img_controller = null;
        }
        removeLastMessage(); //bot animation
        addBotMessage("You have canceled the request. How may I assist you next?");
        saveChatItem();
        enableBtn();
        return;
    }
});



function getStringTime(){
    var currentDate = new Date();
    var year = currentDate.getFullYear();
    var month = ('0'+ (currentDate.getMonth()+1)).slice(-2);
    var day = ('0' + currentDate.getDate()).slice(-2);
    var hours = ('0' + currentDate.getHours()).slice(-2);
    var minutes = ('0' + currentDate.getMinutes()).slice(-2);
    var seconds = ('0' + currentDate.getSeconds()).slice(-2);
    var formattedDateTime = year + month + day + hours + minutes + seconds;
    console.log(formattedDateTime);
    return formattedDateTime
}


function addNewBotMessageID(timestamp) {
    let botMsgID = "botMsg_"+ timestamp;
    let cursorID = "botcursor_" + timestamp;
    const messageElement = document.createElement("div");
    messageElement.classList.add("mb-2", "robot-message-container");
    messageElement.innerHTML = `
                                <div class="icon">
                                    <img src="/static/icon/chatbot_v1.svg" alt="Your Icon" class="custom-robot-icon">
                                </div>
                                <div class="robot-message">
                                    <div id="${botMsgID}" class="bg-gray-200 text-gray-700 rounded-lg py-2 px-4 inline-block">
                                        <span id="${cursorID}" class="cursor">|</span>
                                    </div>
                                </div>`;
    
    chatbox.appendChild(messageElement);
    chatbox.scrollTop = chatbox.scrollHeight;
    return [botMsgID,cursorID];
}


function isValidJSON(str) {
    try {
        JSON.parse(str);
    } catch (error) {
        return false;
    }
    return true;
}