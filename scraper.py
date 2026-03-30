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
        
        df = None
        for t in tables:
            if '代號' in t.columns and '名稱' in t.columns:
                df = t
                break
                
        if df is not None:
            # 把空缺的資料補成空白，避免出錯
            df = df.fillna('')
            
            # 把表格轉換成清單格式
            records = df.to_dict('records')
            
            # 準備要寫入筆記本的內容
            output = {
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": records
            }
            
            # 存成 JSON 筆記本檔案
            with open('stock_gifts.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=4)
                
            print("成功！已儲存最新的 stock_gifts.json")
        else:
            print("找不到表格，網站可能改版了。")
            
    except Exception as e:
        print("抓取失敗，錯誤原因:", e)

if __name__ == "__main__":
    fetch_and_save()
