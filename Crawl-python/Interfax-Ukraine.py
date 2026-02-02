import requests
from bs4 import BeautifulSoup
import json
import time
import random
import pandas as pd
from datetime import datetime
from deep_translator import GoogleTranslator
from openpyxl.styles import Alignment
import sys  # ### 修改: 加入 sys
import os   # ### 修改: 加入 os

# ================= 設定區 =================
BASE_URL = "https://ru.interfax.com.ua"
CATEGORIES = {
    "政治": "/news/political.html",
    "外交": "/news/diplomats.html",
    "經濟": "/news/economic.html"
}

PAGES_TO_SCRAPE = 1 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://ru.interfax.com.ua/"
}

translator = GoogleTranslator(source='auto', target='zh-TW')

# ================= 工具函式 =================

def translate_text(text):
    if not text: return ""
    try:
        if len(text) > 4500:
            text = text[:4500]
        return translator.translate(text)
    except Exception as e:
        print(f"  [翻譯錯誤] {e}")
        return text

def get_article_links(category_url):
    full_url = BASE_URL + category_url
    print(f"\n[系統] 讀取欄目頁: {full_url}")
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        articles = soup.select('.article a')
        for a in articles:
            href = a['href']
            if href.startswith('/news/'):
                links.append(BASE_URL + href)
        
        return list(dict.fromkeys(links)) 
    except Exception as e:
        print(f"  抓取列表失敗: {e}")
        return []

def parse_article(url, category_name):
    print(f"  正在處理 [{category_name}]: {url}")
    time.sleep(random.uniform(1.0, 3.0)) 

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')

        title_tag = soup.select_one('h1.article-title') or soup.select_one('h1')
        title_ru = title_tag.text.strip() if title_tag else ""

        date_tag = soup.select_one('.article-time') or soup.select_one('.time')
        date_str = date_tag.text.strip() if date_tag else ""

        content_div = soup.select_one('.article-content') or soup.select_one('.post-content')
        content_ru = ""
        if content_div:
            for div in content_div.find_all(['div', 'script', 'style']):
                div.decompose()
            content_ru = content_div.get_text(separator='\n').strip()

        title_tw = translate_text(title_ru)
        content_tw = translate_text(content_ru)

        return {
            "日期": date_str,
            "欄目": category_name,
            "標題_俄文": title_ru,
            "標題_中文": title_tw,
            "內文_俄文": content_ru,
            "內文_中文": content_tw,
            "網址": url,
            "下載時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"  解析錯誤: {e}")
        return None

def save_to_excel(df, filename):
    """儲存並優化 Excel 格式"""
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    df.to_excel(writer, index=False)
    worksheet = writer.sheets['Sheet1']
    
    column_settings = {
        'A': 18, 'B': 10, 'C': 40, 'D': 40, 'E': 50, 'F': 50, 'G': 40, 'H': 20
    }
    for col_letter, width in column_settings.items():
        worksheet.column_dimensions[col_letter].width = width
    
    for row in range(2, len(df) + 2):
        for col in [5, 6]: 
            worksheet.cell(row=row, column=col).alignment = Alignment(wrap_text=True, vertical='top')
    writer.close()

# ================= 主程式 =================

def main():
    all_data = []
    
    for cat_name, cat_url in CATEGORIES.items():
        links = get_article_links(cat_url)
        
        for link in links[:15]: 
            article = parse_article(link, cat_name)
            if article:
                all_data.append(article)
                print(f"    -> 已收錄: {article['標題_中文'][:15]}...")
            
            if len(all_data) % 5 == 0:
                time.sleep(5) 

    if all_data:
        df = pd.DataFrame(all_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        excel_file = f"interfax_combined_{timestamp}.xlsx"

        # ### 修改: 判斷儲存路徑
        if len(sys.argv) > 1:
            save_dir = sys.argv[1]
        else:
            save_dir = "."
        
        excel_full_path = os.path.join(save_dir, excel_file)
        
        save_to_excel(df, excel_full_path)
        print(f"\n[完成] 共有 {len(all_data)} 筆資料，已儲存至 {excel_full_path}")
    else:
        print("\n[錯誤] 未抓取到任何資料。")

if __name__ == "__main__":
    main()