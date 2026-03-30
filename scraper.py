import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import json
from datetime import datetime
import time

def fetch_and_save():
    # 拆分網址字串，避免編輯器解析錯誤
    url = "https://" + "histock.tw/stock/gift.aspx"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        session = requests.Session()
        res = session.get(url, headers=headers)
        res.raise_for_status()
        
        all_data = []
        page = 1
        
        while True:
            # 1. 擷取當前頁面表格
            tables = pd.read_html(StringIO(res.text))
            
            # 篩選具備正確欄位結構之表格
            for t in tables:
                if '代號' in t.columns and '名稱' in t.columns:
                    all_data.append(t)
            
            # 2. 解析分頁機制
            soup = BeautifulSoup(res.text, 'html.parser')
            
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
            
            next_page_str = str(page + 1)
            next_page_link = soup.find('a', string=next_page_str)
            
            if not next_page_link:
                break
                
            href = next_page_link.get('href', '')
            if '__doPostBack' in href:
                target = href.split("'")[1]
            else:
                break
            
            # 3. 執行換頁請求
            data = {
                '__EVENTTARGET': target,
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': viewstate['value'] if viewstate else '',
                '__VIEWSTATEGENERATOR': viewstategenerator['value'] if viewstategenerator else '',
                '__EVENTVALIDATION': eventvalidation['value'] if eventvalidation else ''
            }
            
            page += 1
            time.sleep(2) # 遵守網頁請求頻率限制
            res = session.post(url, headers=headers, data=data)
            res.raise_for_status()

        # 4. 資料清洗與輸出
        if all_data:
            df = pd.concat(all_data, ignore_index=True)
            df = df.dropna(subset=['代號'])
            df = df.fillna('')
            df = df.drop_duplicates(subset=['代號'], keep='first')
            
            # 清除「參考圖」贅字與多餘空白
            if '股東會紀念品' in df.columns:
                df['股東會紀念品'] = df['股東會紀念品'].astype(str).str.replace('參考圖', '', regex=False).str.strip()
            if '紀念品' in df.columns:
                df['紀念品'] = df['紀念品'].astype(str).str.replace('參考圖', '', regex=False).str.strip()
            
            records = df.to_dict('records')
            
            output = {
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": records
            }
            
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=4)
                
    except Exception as e:
        pass # 於自動化流程中略過錯誤輸出

if __name__ == "__main__":
    fetch_and_save()
