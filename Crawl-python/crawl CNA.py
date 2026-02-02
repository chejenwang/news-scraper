import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
import pandas as pd
import re
from openpyxl.styles import Font, Alignment
import sys  # <--- 新增：用於接收參數
import os   # <--- 新增：用於處理路徑

# ================= 設定區 =================
LIST_URL = "https://www.cna.com.tw/list/aall.aspx"
BASE_URL = "https://www.cna.com.tw"

# 檔名定義
TODAY_STR_FILENAME = datetime.now().strftime('%Y%m%d')
JSON_FILENAME = f"cna_news_{TODAY_STR_FILENAME}.json"
EXCEL_FILENAME = f"cna_news_{TODAY_STR_FILENAME}.xlsx"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.cna.com.tw/",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

# 排除清單
EXCLUDED_KEYWORDS = [
    "/news/ahel/", "/news/asoc/", "/news/aloc/", "/news/acul/", 
    "/news/aspt/", "/news/amov/", "/video", "postwrite", 
    "/business/", "/information/"
]

# 常見地點與結尾詞清單
LOCATIONS = [
    "台北", "新北", "桃園", "台中", "台南", "高雄", "基隆", "新竹", "嘉義", 
    "苗栗", "彰化", "南投", "雲林", "屏東", "宜蘭", "花蓮", "台東", "澎湖", 
    "金門", "馬祖", "東京", "紐約", "華盛頓", "倫敦", "巴黎", "北京", "上海", 
    "香港", "新加坡", "曼谷", "首爾", "舊金山", "洛杉磯", "外電", "綜合", "整理", "連線"
]

# ================= 核心工具函式 =================

def extract_author(content):
    if not content:
        return "中央社"
    match = re.search(r'[（(]中央社記者(.+?)[）)]', content)
    if match:
        raw_text = match.group(1).strip()
        raw_text = re.sub(r'(專?電|特稿)$', '', raw_text)
        raw_text = re.sub(r'\d+日', '', raw_text)
        for loc in LOCATIONS:
            if raw_text.endswith(loc):
                raw_text = raw_text[:-len(loc)]
                break
        return raw_text.strip()
    return "中央社"

def check_is_today(date_str_from_web):
    try:
        clean_str = date_str_from_web.strip()
        date_part = clean_str.split(' ')[0]
        year, month, day = map(int, date_part.split('/'))
        article_date = datetime(year, month, day).date()
        today_date = datetime.now().date()
        return article_date == today_date
    except Exception:
        return False

def is_excluded(url):
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in url.lower():
            return True
    return False

def get_news_links():
    print(f"正在讀取列表頁: {LIST_URL} ...")
    try:
        response = requests.get(LIST_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            news_items = soup.select('.mainList li a')
            for item in news_items:
                url = item.get('href')
                if url and not url.startswith('http'):
                    url = BASE_URL + url
                if '/news/' in url:
                    if is_excluded(url): continue
                    links.append(url)
            return list(dict.fromkeys(links))
        return []
    except Exception as e:
        print(f"抓取列表錯誤: {e}")
        return []

def parse_news_content(url):
    print(f"  正在檢查: {url}")
    time.sleep(random.uniform(1.5, 3.5)) # 稍微縮短測試時間

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None, False

        soup = BeautifulSoup(response.text, 'html.parser')
        date_tag = soup.select_one('.updatetime span')
        if not date_tag: return None, False
        full_date_str = date_tag.text.strip()
        
        if not check_is_today(full_date_str):
            print(f"    -> 非今日新聞 ({full_date_str})，跳過。")
            return None, False

        print(f"    -> 發現今日新聞！日期: {full_date_str}")
        title_tag = soup.select_one('.centralContent h1 span')
        title = title_tag.text.strip() if title_tag else "未知標題"
        content_div = soup.select_one('.paragraph')
        paragraphs = content_div.find_all('p') if content_div else []
        content = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
        subtitle = None
        strong_tag = content_div.find('strong') if content_div else None
        if strong_tag:
            subtitle = strong_tag.text.strip()
        author = extract_author(content)

        news_data = {
            "日期": full_date_str,
            "作者": author,
            "標題": title,
            "副標題": subtitle,
            "內文": content,
            "網址": url,
            "下載時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return news_data, True
    except Exception as e:
        print(f"  解析錯誤: {e}")
        return None, False

# ================= Excel 存檔 =================

def save_optimized_excel(data_list, filename):
    if not data_list: return
    df = pd.DataFrame(data_list)
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='今日新聞')
    
    workbook = writer.book
    worksheet = writer.sheets['今日新聞']
    
    column_widths = {'A': 20, 'B': 15, 'C': 50, 'D': 30, 'E': 80, 'F': 60, 'G': 20}
    for col_letter, width in column_widths.items():
        worksheet.column_dimensions[col_letter].width = width

    link_col_idx = 6 
    for row in range(2, len(data_list) + 2):
        cell = worksheet.cell(row=row, column=link_col_idx)
        if cell.value:
            cell.hyperlink = cell.value
            cell.font = Font(color="0000FF", underline="single")
    
    content_col_idx = 5
    for row in range(2, len(data_list) + 2):
        cell = worksheet.cell(row=row, column=content_col_idx)
        cell.alignment = Alignment(wrap_text=True, vertical='top')

    writer.close()
    print(f"Excel 優化完成：{filename}")

# ================= 主程式 =================

def main():
    print(f"系統日期: {datetime.now().strftime('%Y/%m/%d')}")
    
    # --- 新增：處理傳入的路徑參數 ---
    if len(sys.argv) > 1:
        save_dir = sys.argv[1]
    else:
        save_dir = "." # 如果沒給參數，就存在目前資料夾

    # 確保資料夾存在 (以防萬一)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    links = get_news_links()
    today_news = []
    old_news_count = 0 
    
    for url in links:
        if old_news_count >= 5:
            print("\n連續遇到多篇舊新聞，停止程式。")
            break

        data, is_today_flag = parse_news_content(url)
        if is_today_flag and data:
            today_news.append(data)
            old_news_count = 0 
        elif not is_today_flag:
            old_news_count += 1
    
    # --- 儲存區塊 ---
    if today_news:
        # 使用 os.path.join 結合路徑與檔名
        json_full_path = os.path.join(save_dir, JSON_FILENAME)
        excel_full_path = os.path.join(save_dir, EXCEL_FILENAME)

        # 儲存 JSON
        with open(json_full_path, 'w', encoding='utf-8') as f:
            json.dump(today_news, f, ensure_ascii=False, indent=4)
        
        # 儲存 Excel
        save_optimized_excel(today_news, excel_full_path)
        print(f"\n全部完成！共 {len(today_news)} 篇。")
        print(f"檔案儲存於: {save_dir}")
    else:
        print("\n未發現今日新聞。")

if __name__ == '__main__':
    main()
