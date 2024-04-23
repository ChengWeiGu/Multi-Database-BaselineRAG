// 清除本地存儲中的所有資料
function clearLocalStorage() {
    localStorage.clear();
    alert('Local Storage cleared successfully!');
}

// 加載時從本地存儲加載聊天記錄
window.onload = function() {
    var savedChat = localStorage.getItem('chatbox');
    if (savedChat) {
        // reload savechat
        document.getElementById('chatbox').innerHTML = savedChat;
        // reload data
        data = JSON.parse(localStorage.getItem('data'));
        lastChatID = data.lastChatID;
        //滾動到最底部
        var chatbox = document.getElementById('chatbox');
        chatbox.scrollTop = chatbox.scrollHeight;
    }
};

// 存儲聊天記錄到本地存儲
function saveChatItem() {
    // chatbox block
    var chatbox = document.getElementById('chatbox').innerHTML;
    localStorage.setItem('chatbox', chatbox);
    // save info data
    data = {"lastChatID" : lastChatID}
    localStorage.setItem('data', JSON.stringify(data));
}