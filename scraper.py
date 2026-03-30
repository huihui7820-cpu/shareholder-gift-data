import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, date
import re

def fetch_gift_data():
    url = "https://histock.tw/stock/gift.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"抓取失敗：{e}")
        return []

    results = []
    table = soup.find("table", {"id": "tb1"}) or soup.find("table")
    if not table:
        print("找不到資料表格")
        return []

    rows = table.find_all("tr")[1:]  # 跳過標題列
    today = date.today()

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        
        texts = [c.get_text(strip=True) for c in cells]
        
        # 解析最後買進日（格式可能是 MM/DD 或 YYYY/MM/DD）
        last_buy_raw = texts[3] if len(texts) > 3 else ""
        last_buy_date = parse_date(last_buy_raw)
        
        meeting_raw = texts[4] if len(texts) > 4 else ""
        meeting_date = parse_date(meeting_raw)
        
        # 計算狀態
        status = "unknown"
        days_left = None
        if last_buy_date:
            d = date.fromisoformat(last_buy_date)
            diff = (d - today).days
            days_left = diff
            if diff < 0:
                status = "expired"
            elif diff == 0:
                status = "today"
            elif diff <= 5:
                status = "soon"
            else:
                status = "ok"
        
        # 零股
        zero_share = "可" if "可" in texts[5] else "否"
        
        results.append({
            "code": texts[0],
            "name": texts[1],
            "gift": texts[2],
            "lastBuyDate": last_buy_date,
            "meetingDate": meeting_date,
            "zeroShare": zero_share,
            "agentPhone": texts[6] if len(texts) > 6 else "",
            "status": status,
            "daysLeft": days_left
        })
    
    print(f"共取得 {len(results)} 筆資料")
    return results


def parse_date(raw):
    """把各種日期格式統一轉成 YYYY-MM-DD"""
    raw = raw.strip()
    # 格式：2026/05/10 或 2026-05-10
    m = re.match(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", raw)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # 格式：05/10（只有月日，補上今年）
    m = re.match(r"(\d{1,2})[/-](\d{1,2})$", raw)
    if m:
        year = datetime.now().year
        return f"{year}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


if __name__ == "__main__":
    data = fetch_gift_data()
    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(data),
        "data": data
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("已儲存 data.json")
