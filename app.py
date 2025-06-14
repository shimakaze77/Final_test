# 匯入必要的函式庫
from flask import Flask, request, render_template_string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os # 用於讀取環境變數，更安全

# --- 1. 建立 Flask 應用程式實例 ---
app = Flask(__name__)

# --- 2. 寄件者 Gmail 帳號與應用程式密碼設定 ---
# 警告：直接將密碼寫在程式碼中有安全風險。
# 推薦做法是使用環境變數。您可以取消註解下面兩行來使用環境變數。
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
APP_PASSWORD = os.environ.get('APP_PASSWORD')

# --- 3. HTML 網頁模板 ---
# 將 HTML 程式碼作為多行字串儲存在變數中
# 這是一個包含表單的主頁面模板
FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>線上賀卡寄送服務</title>
    <style>
        body { font-family: 'Microsoft JhengHei', '微軟正黑體', sans-serif; background-color: #f4f4f9; color: #333; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .container { background-color: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); max-width: 600px; width: 100%; overflow: hidden; }
        .card-image { width: 100%; height: auto; display: block; }
        .form-content { padding: 25px 30px; }
        h1 { text-align: center; color: #4a4a4a; margin-bottom: 25px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-weight: 600; margin-bottom: 8px; color: #555; }
        input[type="text"], input[type="email"], textarea {
            width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; transition: border-color 0.3s, box-shadow 0.3s;
        }
        input[type="text"]:focus, input[type="email"]:focus, textarea:focus {
            border-color: #007bff; box-shadow: 0 0 5px rgba(0, 123, 255, 0.5); outline: none;
        }
        textarea { resize: vertical; min-height: 120px; }
        .sender-group { display: flex; justify-content: flex-end; align-items: center; }
        .sender-group label { margin-right: 10px; margin-bottom: 0; }
        .sender-group input { max-width: 200px; }
        .submit-btn {
            display: block; width: 100%; padding: 15px; background-color: #28a745; color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; transition: background-color 0.3s; margin-top: 10px;
        }
        .submit-btn:hover { background-color: #218838; }
        .message { padding: 15px; margin: 20px; border-radius: 8px; text-align: center; font-size: 16px; display: {% if message %}block{% else %}none{% endif %};}
        .message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .message.error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <!-- 顯示賀卡圖片 -->
        <img src="https://images.unsplash.com/photo-1546487922-54d95a9a4b37?q=80&w=1771&auto=format&fit=crop" 
             alt="賀卡圖片" class="card-image"
             onerror="this.onerror=null;this.src='https://placehold.co/600x300/f0f0f0/333?text=圖片載入失敗';">
        
        <div class="form-content">
            <h1>寄送您的祝福</h1>

            <!-- 顯示結果訊息 -->
            <div class="message {{ message_type }}">{{ message }}</div>

            <!-- 寄送表單 -->
            <form method="POST" action="/">
                <div class="form-group">
                    <label for="recipient_name">收件者姓名：</label>
                    <input type="text" id="recipient_name" name="recipient_name" placeholder="請輸入收件者的稱呼" required>
                </div>
                <div class="form-group">
                    <label for="message_content">卡片內容：</label>
                    <textarea id="message_content" name="message_content" placeholder="在這裡寫下您的祝福..." required></textarea>
                </div>
                <div class="form-group sender-group">
                    <label for="sender_name">寄件者姓名：</label>
                    <input type="text" id="sender_name" name="sender_name" placeholder="請輸入您的大名" required>
                </div>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <div class="form-group">
                    <label for="recipient_email">收件者信箱：</label>
                    <input type="email" id="recipient_email" name="recipient_email" placeholder="recipient@example.com" required>
                </div>
                <div class="form-group">
                    <label for="sender_email">您的信箱 (僅供顯示，不會用於寄送)：</label>
                    <input type="email" id="sender_email" name="sender_email" placeholder="sender@example.com" required>
                </div>
                <button type="submit" class="submit-btn">寄送賀卡</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

# --- 4. 寄送電子賀卡的函數 ---
def send_e_card(sender_name, sender_email_display, recipient_name, recipient_email, message_content):
    """
    建立並寄送一封 HTML 格式的電子賀卡。
    """
    print(f"準備寄送賀卡給 {recipient_name} ({recipient_email})")

    # 建立多格式郵件物件
    msg = MIMEMultipart()
    msg["Subject"] = f"{sender_name} 寄來一張溫馨的賀卡！"
    msg["From"] = f"{sender_name} <{SENDER_EMAIL}>" # 寄件者顯示名稱和實際信箱
    msg["To"] = recipient_email

    # 建立 HTML 郵件內容 (這就是收件者會看到的賀卡樣式)
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; border: 1px solid #ddd; border-radius: 10px; overflow: hidden;">
                <img src="https://images.unsplash.com/photo-1546487922-54d95a9a4b37?q=80&w=1771&auto=format&fit=crop" style="width: 100%;" alt="賀卡圖片">
                <div style="padding: 20px 30px;">
                    <h2 style="color: #333;">親愛的 {recipient_name}，</h2>
                    <p style="font-size: 16px; color: #555; line-height: 1.6;">{message_content.replace('\\n', '<br>')}</p>
                    <p style="text-align: right; font-size: 16px; color: #333; margin-top: 30px;">祝福您</p>
                    <p style="text-align: right; font-size: 18px; color: #333; font-weight: bold;">{sender_name}</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 12px; color: #999; text-align: center;">這封郵件由 {sender_name} ({sender_email_display}) 透過線上賀卡服務寄送。</p>
                </div>
            </div>
        </body>
    </html>
    """

    # 將 HTML 內容附加到郵件物件中
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    # 使用 smtplib 連線到 Gmail SMTP 伺服器並寄送
    # 使用 with 陳述式確保連線自動關閉
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        print("正在登入 SMTP 伺服器...")
        server.login(SENDER_EMAIL, APP_PASSWORD)
        print("正在寄送郵件...")
        server.send_message(msg)
        print("郵件寄送成功！")

# --- 5. Flask 網站路由 ---
@app.route("/", methods=['GET', 'POST'])
def index():
    message = None
    message_type = ''

    # 處理表單提交 (POST 請求)
    if request.method == 'POST':
        try:
            # 從表單中獲取使用者輸入的資料
            recipient_name = request.form['recipient_name']
            message_content = request.form['message_content']
            sender_name = request.form['sender_name']
            recipient_email = request.form['recipient_email']
            sender_email_display = request.form['sender_email']

            # 呼叫寄信函數
            send_e_card(
                sender_name,
                sender_email_display,
                recipient_name,
                recipient_email,
                message_content
            )
            # 設定成功訊息
            message = "賀卡已成功寄出！"
            message_type = "success"
        except Exception as e:
            # 如果發生錯誤，設定失敗訊息
            print(f"錯誤: {e}")
            message = f"寄送失敗：{e}"
            message_type = "error"

    # 顯示主頁面 (GET 請求或 POST 處理完畢後)
    return render_template_string(FORM_TEMPLATE, message=message, message_type=message_type)


# --- 6. 啟動 Flask 伺服器 ---
# 如果這個 .py 檔案是作為主程式直接執行
if __name__ == "__main__":
    # 啟動 Flask 開發伺服器，可以從區域網路中的其他裝置訪問
    app.run(host='0.0.0.0', port=5000, debug=True)

