import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import json
from datetime import datetime
import time

def fetch_and_save():
    url = "[https://histock.tw/stock/gift.aspx](https://histock.tw/stock/gift.aspx)"
    # 偽裝成真人瀏覽器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        session = requests.Session()
        print("開始抓取第 1 頁資料...")
        res = session.get(url, headers=headers)
        res.raise_for_status()
        
        all_data = []
        page = 1
        
        while True:
            # 1. 解析當前網頁表格
            tables = pd.read_html(StringIO(res.text))
            for t in tables:
                if '代號' in t.columns and '名稱' in t.columns:
                    all_data.append(t)
                    break
            
            # 2. 尋找「下一頁」的機制 (破解 ASP.NET 隱藏表單)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 找出隱藏的狀態欄位
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
            
            # 尋找包含「下一頁碼」的 <a> 標籤 (例如第2頁、第3頁)
            next_page_str = str(page + 1)
            next_page_link = soup.find('a', string=next_page_str)
            
            if not next_page_link:
                print(f"找不到第 {page + 1} 頁，代表已經抓到最後一頁了！")
                break
                
            # 解析 href 中的換頁代碼 (例如 javascript:__doPostBack('ctl00$CPH1$Pager1$ctl02',''))
            href = next_page_link.get('href', '')
            if '__doPostBack' in href:
                target = href.split("'")[1]  # 取出第一個單引號內的值
            else:
                break
            
            # 3. 準備送出翻頁請求
            data = {
                '__EVENTTARGET': target,
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': viewstate['value'] if viewstate else '',
                '__VIEWSTATEGENERATOR': viewstategenerator['value'] if viewstategenerator else '',
                '__EVENTVALIDATION': eventvalidation['value'] if eventvalidation else ''
            }
            
            page += 1
            print(f"正在抓取第 {page} 頁資料 (休息 2 秒防鎖)...")
            time.sleep(2) # 休息2秒，避免對網站造成負擔被封鎖
            res = session.post(url, headers=headers, data=data)
            res.raise_for_status()

        # 4. 彙整所有頁面的資料
        if all_data:
            df = pd.concat(all_data, ignore_index=True)
            # 清理資料：刪除全空的列，並把空值補成空白字串
            df = df.dropna(subset=['代號'])
            df = df.fillna('')
            # 確保代號不重複 (保留最新的一筆)
            df = df.drop_duplicates(subset=['代號'], keep='first')
            
            # 把表格轉換成清單格式
            records = df.to_dict('records')
            
            # 準備要寫入筆記本的內容
            output = {
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": records
            }
            
            # 存成 JSON 筆記本檔案
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=4)
                
            print(f"成功！總共抓取了 {page} 頁，共 {len(records)} 筆資料，已儲存至 data.json")
        else:
            print("找不到任何表格資料，網站可能改版了。")
            
    except Exception as e:
        print("抓取失敗，錯誤原因:", e)

if __name__ == "__main__":
    fetch_and_save()
