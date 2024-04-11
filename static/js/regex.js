var text = `The supported HMI models and OS versions for EasyAccess 2.0 are as follows:

| Model | OS Version (included and after) |
|-------------------|---------------------------------|
| eMT3070A | 20140624 |
| eMT3070B | No version limit |
| eMT3105 | 20140701 |
| eMT3120 | 20140701 |
| eMT3150 | 20140701 |
| MT8070iE | 20140626 |
| MT8100iE | 20140626 |
| MT8050iE | 20140624 |
| MT8071iE | 20140624 |
| MT8101iE | 20140624 |
| MT8090XE | No version limit |
| MT8091XE | No version limit |
| MT8121XE | 20140624 |
| MT8150XE | 20140624 |
| mTV-100 | 20140815 |
| cMT-SVR | 20140715 |

Please note that eMT3105, eMT3120, and eMT3150 models purchased before June 2012 do not support EasyAccess 2.0.

Reference:
-- document source: Reference Document#3
-- Web link: N`;


function text2HTMLTable(text){
    text = "\n\n"+text+"\n\n";
    let tableRegex = /\n?(\n\|[\s\S]*?\|\n)\n/g;
    let rowRegex = /\|[\s\S]*?\|\n/g;
    //抓整表
    text = text.replace(tableRegex, function(match,p1){
        // Table列處理
        let tableHTML = `<table class="robot-table">`;
        let allRows = [...p1.matchAll(rowRegex)];
        // console.log(p1);
        allRows.forEach((rowMatch,index)=>{
            // console.log(index);
            // console.log(rowMatch);
            if (index != 1) {
                // headers
                if (index == 0) {
                    let headers = rowMatch[0].trim().split('|');
                    headers.shift();
                    headers.pop();
                    tableHTML += "<tr>";
                    headers.forEach(header => {
                        tableHTML += `<th>${header.trim()}</th>`;
                    });
                    tableHTML += "</tr>";
                // items
                } else {
                    let items = rowMatch[0].trim().split('|');
                    items.shift();
                    items.pop();
                    tableHTML += "<tr>";
                    items.forEach(item => {
                        tableHTML += `<td>${item.trim()}</td>`;
                    });
                    tableHTML += "</tr>";
                }
            }
        });
        tableHTML += "</table>";
        return `\n${tableHTML}\n`;
    });
    return text.trim();
}


function codeText2HTML(text) {
    let hasJS = text.includes("```javascript");
    let hasPy = text.includes("```python");
    let hasCss = text.includes("```css");
    let hasC = text.includes("```c");
    let hasJson = text.includes("```json");
    let hasSH = text.includes("```sh");
    let hasHTML = text.includes("```html");
    text = text.replace(/```(?:html|javascript|python|css|c|json|sh|plaintext).*\n/g,'```');
    // html特殊處理
    if (hasHTML){
        text = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
    //文字code處理
    text = text.replace(/```([^`]+)```/g, '<pre class="code-block">$1</pre>');
    return text;
}

//console.log(text2HTMLTable(text));


function header2HTML(text) {
    text = text.replace(/\*\*(.*?)\*\*/g, '<span style="font-weight: bold; font-size : 18px;">$1</span>');
    return text;
}

function formula2Markdown(text) {
    text = text.replace(/\\\[(.*?)\\\]/g,'`$1`');
    return text;
}


function highlightMarkText(text) {
    text = text.replace(/`(.*?)`/g, '<span style="font-weight: bold !important;">$1</span>');
    return text
}


function Anno_Url_2HTML(text) {
    text = text.replace(/(\/\/.*\n)|(\(?\'?\"?https?:\/\/[^\s]+)|(#.*\n)/g, function(match, p1, p2, p3){
        if (p1 !== undefined) {
            return '<span class="comment" style="color:gray">' + p1 +'</span>';
        } else if (p2 !== undefined) {
            // http暫時不做處理
            // p2_link = p2.replace('"','').replace("'",'').replace("''",'').replace(")",'').replace("(",'').replace(",",'');
            // return '<a href="' + p2_link + '" target="_blank" style="color:blue;">"' + p2_link.replace("'",'') + '"</a>';
            return p2
        } else {
            return '<span class="comment" style="color:gray">' + p3 +'</span>';
        }
    });
    return text;
}


function PreventHtml2Code(text) {
    // Encode HTML tags to prevent them from being interpreted as HTML
    text = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    text = text.replace(/\n/g,"<br>");
    return text;
}


function regex_flow(message) {
    //表格處理
    message = text2HTMLTable(message);
    //文字code處理
    message = codeText2HTML(message);
    //重點標頭
    message = header2HTML(message);
    //公式變成markdown格式
    message = formula2Markdown(message);
    //highlight文字
    message = highlightMarkText(message);
    // 註釋+url處理
    message = Anno_Url_2HTML(message);
    //換行處理
    message = message.replace(/\n/g,"<br>");
    return message;
}

