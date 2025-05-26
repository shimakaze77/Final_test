from flask import Flask
app = Flask(__name__)   #name代表目前執行的模組

@app.route("/")   #函式的裝飾(decorator):以含是為基礎提供附加功能
def home():
    return "Hello Flask"

@app.route("/test")  #加一網站跟目錄路徑
def test():
    return "This is a test"

if __name__=="__main__":  #如果以主程式啟動
    app.run()   #立刻啟動伺服器
