//global var
const feedback_container = document.getElementById("feedback_container");
var feedback_query = ""; // selected chat query
var feedback_generation = ""; // selected chat resp
var feedback_chat_id = ""; // selected chat id
var scroll_enable = true;
var now = getStringTime();


//submit for generation
submitButton.addEventListener('click', function() {
    // disable feedback_container
    feedback_container.style.display = "none";
    // define time_now for purpose of unique id only when btn is "submit"
    if (submitButton.textContent == 'Submit') {
        now = getStringTime();
    }
    // acquire inpu text
    let InputMessage = userInput.value.trim();
    // disable generate-btn for last resp
    hideLastRetryBtn();
    // enable auto scroll
    scroll_enable = true;
    chatbox.scrollTop = chatbox.scrollHeight;
    // chat mode
    if (submitButton.textContent == 'Submit' && select_mode.value == 'chat_gen') {
        // define gen model
        var select_generate_model = "gpt4";
        //前置流程
        disableBtn();
        addUserMessage(InputMessage,now);
        userInput.value = "";
        // add bot message and cursor
        let BotIDs = addNewBotMessageID(now);
        const botMsgDivElement = document.getElementById(BotIDs.botMsgID);
        const botToolBar = document.getElementById(BotIDs.toolbarID);
        //抓取歷史資料 => []
        var history_messages = acquire_history_messages(max_chat_history);
        chat_controller = new AbortController();
        // post data to backend
        fetch('/generate_stream_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ input_text: InputMessage ,
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
                        // 最後一次regex處理 (增加table的處理)
                        let realTimeMsg = regex_flow(result);
                        botMsgDivElement.innerHTML = `${realTimeMsg} <br><br><span class="resp_id_span" style="font-size:12px;">Response ID : ${now}</span>`
                        // 紀錄上一次的id 以便disable retry for next request
                        lastChatID = now;
                        return { result, finalData };
                    }
                    const chunk = decoder.decode(value);
                    result += chunk;
                    // 保持換行顯示, cursor保持在最後, real-time doing streaming regex
                    let realTimeMsg = regex_stream(result);
                    botMsgDivElement.innerHTML = `${realTimeMsg} <span id="${BotIDs.cursorID}" class="cursor">|</span>`
                    if (scroll_enable){
                        chatbox.scrollTop = chatbox.scrollHeight;
                    }
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
            // display the toolbar
            botToolBar.style.display="flex";
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
        disableBtn();
        addUserMessage(InputMessage);
        addBotMessageAnimation();
        userInput.value = "";
        img_controller = new AbortController();
        //post prompt to backend
        fetch('/generate_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ input_text: InputMessage}),
            signal: img_controller.signal //cancel
        })
        .then(response => response.json())
        .then(data => {
                removeLastMessage(); //bot animation
                if (data.status == 'success'){
                    addBotMessageForImageMode(data.output_text,data.image_descr,now);
                } else {
                    addBotMessage(data.output_text,now);
                }
                saveChatItem();
                img_controller = null;
                enableBtn();
        });
    } else {
        
        if (select_mode.value=="chat_gen") {
            chat_controller.abort();
            chat_controller = null;
            //移除cursor sapn "|"
            var spanElements = document.querySelectorAll(".robot-message .cursor");
            spanElements.forEach(function(span){
                span.parentNode.removeChild(span);
            });
            // show resp id for bot msg
            let botmsg = document.getElementById("botMsg_"+now);
            botmsg.innerHTML += `<br><br><span class="resp_id_span" style="font-size:12px;">Response ID : ${now}`;
            // display the toolbar
            let toolbar = document.getElementById("toolbar_"+now);
            toolbar.style.display="flex";
            // 紀錄上一次的id 以便disable retry for next request
            lastChatID = now;
        } else { 
            img_controller.abort();
            img_controller = null;
            removeLastMessage(); //bot animation
            addBotMessage("You have canceled the request. How may I assist you next?",now);
        }
        
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
    let toolbarID = "toolbar_" + timestamp;
    let feedbackBtnID = "feedbackBtn_" + timestamp;
    let feedbackBtnIconID = "feedbackBtnIcon_" + timestamp;
    let copyBtnID = "copyBtn_" + timestamp;
    let copyBtnIconID = "copyBtnIcon_" + timestamp;
    let regenBtnID = "regenBtn_" + timestamp;
    let regenBtnIconID = "regenBtnIcon_" + timestamp;
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
                                <div>

                                <div>
                                    <div id="${toolbarID}" class="robot-toolbar-container">
                                        <div id="${feedbackBtnID}" class="icon-text-tool-container" onclick="showFeedbackPopup(this)">
                                            <img id="${feedbackBtnIconID}" src="/static/icon/feedback_v1.svg" alt="Your Icon" class="custom-tool-icon">
                                            <span style="font-size:12px;">Feedback</span>
                                        </div>
                                        <div id="${copyBtnID}" class="icon-text-tool-container" onclick="copyRobotText(this)">
                                            <img id="${copyBtnIconID}" src="/static/icon/copy_v1.svg" alt="Your Icon" class="custom-tool-icon">
                                            <span style="font-size:12px;">Copy</span>
                                        </div>
                                        <div id="${regenBtnID}" class="icon-text-tool-container" onclick="reGenText(this)">
                                            <img id="${regenBtnIconID}" src="/static/icon/regen_v1.svg" alt="Your Icon" class="custom-tool-icon">
                                            <span style="font-size:12px;">Retry</span>
                                        </div>
                                    </div>
                                </div>`;
    
    chatbox.appendChild(messageElement);
    chatbox.scrollTop = chatbox.scrollHeight;
    // return a object
    return { botMsgID , cursorID , toolbarID };
}


function copyRobotText(element) {
    // get the botmsg chosen
    var copyArea = document.getElementById(element.id.replace("copyBtn_","botMsg_"));
    var copyText = copyArea.textContent;
    // remove response id
    copyText = copyText.replace(/Response ID : \d+/g, "");
    // create an textArea element
    var textArea = document.createElement("textarea");
    textArea.value = copyText;
    document.body.appendChild(textArea);
    // 選中臨時文本區域的內容
    textArea.select();
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            // 提示使用者複製成功
            // alert('Copying text successful!');
            // get copy icon
            var copyIcon = document.getElementById(element.id.replace("copyBtn_", "copyBtnIcon_"));
            // change the icon
            let originImageSrc = copyIcon.src;
            copyIcon.src = "/static/icon/check_v1.svg";
            setTimeout(function(){
                copyIcon.src = originImageSrc;
            },500);
        }
        else {
            alert('copying text unsuccessful!');
        }
    } catch (err) {
        alert('Oops, unable to copy');
    } finally {
        document.body.removeChild(textArea);
    }
    
}


function showFeedbackPopup(element){
    // animation shows popup successifully
    var feedbackIcon = document.getElementById(element.id.replace("feedbackBtn_", "feedbackBtnIcon_"));
    // change the icon
    let originImageSrc = feedbackIcon.src;
    feedbackIcon.src = "/static/icon/check_v1.svg";
    setTimeout(function(){
        feedbackIcon.src = originImageSrc;
        // set this container to be flex
        feedback_container.style.display = "block";
    },500);
    // init value of feedback elements
    var select_score = document.getElementById('select_score');
    var select_assist = document.getElementById('select_assist');
    var select_OK = document.getElementById('select_OK');
    var fileInput = document.getElementById('fileInput');
    var input_text_feedback = document.getElementById('input_text_feedback');
    var srcRef = document.getElementById("input_text_srcRef"); //來源網址
    srcRef.value = "";
    input_text_feedback.value = "";
    fileInput.value = "";
    // set feedback_query
    var userMsgDivElement_chosen = document.getElementById(element.id.replace("feedbackBtn_", "userMsg_"));
    feedback_query = userMsgDivElement_chosen.textContent;
    // set feedback_generation
    var botMsgDivElement_chosen = document.getElementById(element.id.replace("feedbackBtn_", "botMsg_"));
    // remove response id
    feedback_generation = botMsgDivElement_chosen.textContent.replace(/Response ID : \d+/g, "");
    // convert html to text
    feedback_generation = PreventHtml2Code(feedback_generation);
    var show_selected_label = document.getElementById("show_selected_label_id");
    show_selected_label.textContent = "Response ID : "+element.id.split("_")[1];
    // re-arrange the layout of chat_feedback_container
    leftChatBoxLayout();
    // set this container to be none
    feedback_container.style.display = "none";
}

// 關閉feedback視窗
closeFeedbackFormButton.addEventListener('click', function() {
    // disable feedback form
    feedback_container.style.display = "none";
    // reset chatbox layout
    resetChatBoxLayout();
})

// chatbox滾輪事件
var lastScrollTop = 0;
chatbox.addEventListener('scroll', function() {
    const currentScrollTop = chatbox.scrollTop; //獲取當前滾動位置
    if (currentScrollTop < lastScrollTop) {
        scroll_enable = false;
    } else {
        scroll_enable = true;
    }
    lastScrollTop = currentScrollTop;
})

function hideLastRetryBtn() {
    // if the last retry btn was removed by user or other function, an error will be catched
    try {
        // hide regen button
        var regenBtn = document.getElementById("regenBtn_"+lastChatID);
        regenBtn.style.display = "none";
        // resize the tool bar
        var toolbar = document.getElementById("toolbar_"+lastChatID);
        toolbar.style.width = "150px"; 
    } catch (error) {
       console.log(error);
    }
}

// Re-generate Text(only available for the lastest message)
function reGenText(element) {
    // animation
    var reTryIcon = document.getElementById(element.id.replace("regenBtn_", "regenBtnIcon_"));
    // change the icon
    let originImageSrc = reTryIcon.src;
    reTryIcon.src = "/static/icon/check_v1.svg";
    setTimeout(function(){
        reTryIcon.src = originImageSrc;
    },500);
    // reset interaction model to chat generation
    select_mode.value = 'chat_gen';
    // get last user query and then set userInput to userMsg
    var userMsgDivElement_chosen = document.getElementById(element.id.replace("regenBtn_", "userMsg_"));
    userInput.value = userMsgDivElement_chosen.textContent;
    // remove the last robot/user message
    for (var i = 0; i < 2; i++) {
        removeLastMessage();
    }
    // click submit button
    submitButton.click();
}


// reset chat box layout to center
function resetChatBoxLayout() {
    var chat_feedback_container = document.getElementById("chat_feedback_container");
    chat_feedback_container.classList.remove("chat_feedback_container_left");
    chat_feedback_container.classList.add("chat_feedback_container_center");
}

// left chat box layout
function leftChatBoxLayout() {
    var chat_feedback_container = document.getElementById("chat_feedback_container");
    chat_feedback_container.classList.remove("chat_feedback_container_center");
    chat_feedback_container.classList.add("chat_feedback_container_left");
}


function isValidJSON(str) {
    try {
        JSON.parse(str);
    } catch (error) {
        return false;
    }
    return true;
}