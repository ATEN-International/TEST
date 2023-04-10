from ai_voice_sdk import VoiceConverter
from ai_voice_sdk import Voice

if __name__ == "__main__":
    token = "API_ACCESS_TOKEN"
    server_url = "SERVER_URL"
    converter = VoiceConverter(server_url, token, Voice.NOETIC) # 建立轉換器，參數 token = '顯示於網頁上的token', Voice = 要使用的語音(預設為 NOETIC)
    converter.set_voice(Voice.LITERARY) # 調整轉換器使用的語音，參數 Voice = 要使用的語音

    converter.add_text("歡迎體驗宏正優聲學，讓好聲音為您的應用提供加值服務。")
    converter.add_text("宏正自動科技的人工智慧語音合成技術，帶來超逼真的合成語音。")
    print(f"{converter.get_text()}\n") # 獲得文章清單

    converter.open_text_file("textfile.txt") # 開啟文字檔並加入文章，參數 encode 設定文字格式
    converter.show_text() # 顯示文章

    converter.delete_text(1) # 刪除第1個段落
    converter.delete_text(0) # 刪除第0個段落
    converter.show_text() # 顯示文章

    converter.start_convert(wait_time = 0) # 參數wait_time = 0，表示server忙碌時，不排隊重試合成語音

    converter.get_result("my_aivoice") # 將語音存為'my_aivoice.wav'，預設檔名為'aivoice.wav'
