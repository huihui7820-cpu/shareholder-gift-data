import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import json
from datetime import datetime
import time
import re

def format_gift_name(name):
    """標準化紀念品名稱，統一超商商品卡格式"""
    name = str(name).replace('參考圖', '').strip()
    if not name or name == 'nan' or name == '無' or name == '不發放':
        return name
    
    store = ""
    # 辨識超商名稱
    if re.search(r'(7-11|7-eleven|統一超商|統一)', name, re.IGNORECASE):
        store = "7-11超商"
    elif re.search(r'(全家)', name):
        store = "全家超商"
        
    if store:
        # 擷取數字金額 (強制匹配「元」，避免誤判 7-11 的 7)
        amount_match = re.search(r'(\d+)元', name)
        if amount_match:
            amount = amount_match.group(1)
            # 判斷卡片類型，預設為商品卡
            card_type = "商品卡"
            if "禮物卡" in name:
                card_type = "禮物卡"
            elif "購物金" in name:
                card_type = "購物金"
            return f"{store}{amount}元{card_type}"
            
    return name

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
            
            # 建立例外資料校正字典：用於覆寫來源網站之錯誤登錄
            manual_overrides = {
                '國光生': '氣密保鮮罐(不足時將以等值商品替代)'
            }
            
            # 執行例外資料強制覆寫
            if '名稱' in df.columns:
                for stock_name, correct_gift in manual_overrides.items():
                    if '股東會紀念品' in df.columns:
                        df.loc[df['名稱'] == stock_name, '股東會紀念品'] = correct_gift
                    if '紀念品' in df.columns:
                        df.loc[df['名稱'] == stock_name, '紀念品'] = correct_gift
            
            # 執行資料清洗與格式統一
            if '股東會紀念品' in df.columns:
                df['股東會紀念品'] = df['股東會紀念品'].apply(format_gift_name)
            if '紀念品' in df.columns:
                df['紀念品'] = df['紀念品'].apply(format_gift_name)
            
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
