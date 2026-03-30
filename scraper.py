import requests
import pandas as pd
from io import StringIO
import json
from datetime import datetime

def fetch_and_save():
    url = "[https://histock.tw/stock/gift.aspx](https://histock.tw/stock/gift.aspx)"
    # 偽裝成真人瀏覽器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("開始抓取資料...")
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        
        # 讀取網頁中的表格
        tables = pd.read_html(StringIO(res.text))
        
        all_data = []
        # 尋找網頁上「所有」包含代號與名稱的表格，把它們全部收集起來
        for t in tables:
            if '代號' in t.columns and '名稱' in t.columns:
                all_data.append(t)
                
        if all_data:
            # 1. 將多個表格合併成一個大表格
            df = pd.concat(all_data, ignore_index=True)
            
            # 2. 清理資料：刪除全空的列，並把空值補成空白字串
            df = df.dropna(subset=['代號'])
            df = df.fillna('')
            
            # 3. 確保代號不重複 (保留最新的一筆)
            df = df.drop_duplicates(subset=['代號'], keep='first')
            
            # 把表格轉換成清單格式
            records = df.to_dict('records')
            
            # 準備要寫入筆記本的內容
            output = {
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": records
            }
            
            # 存成 JSON 筆記本檔案 (配合您的檔名 data.json)
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=4)
                
            print(f"成功！總共抓取了 {len(records)} 筆資料，已儲存至 data.json")
        else:
            print("找不到表格，網站可能改版了。")
            
    except Exception as e:
        print("抓取失敗，錯誤原因:", e)

if __name__ == "__main__":
    fetch_and_save()
