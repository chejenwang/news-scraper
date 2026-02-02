import requests
from bs4 import BeautifulSoup
import json
import time
import random
import pandas as pd
from datetime import datetime
from deep_translator import GoogleTranslator
from openpyxl.styles import Alignment
import sys  # <--- 新增
import os   # <--- 新增

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
    print(f"正在抓取目錄: {category_url}")
    links = []
    try:
        response = requests.get(BASE_URL + category_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('.cat_news_item a')
            for item in items:
                href = item.get('href')
                if href and href.startswith('/news/'):
                    links.append(BASE_URL + href)
        return list(dict.fromkeys(links))
    except Exception as e:
        print(f"抓取連結錯誤: {e}")
        return []

def parse_article(url, category):
    try:
        time.sleep(random.uniform(1, 2))
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_ru = soup.select_one('.article_title').text.strip()
        date_str = soup.select_one('.article_date').text.strip()
        content_div = soup.select_one('.article_content')
        content_ru = content_div.get_text(separator='\n').strip() if content_div else ""

        print(f"  正在翻譯標題: {title_ru[:20]}...")
        title_zh = translate_text(title_ru)
        print(f"  正在翻譯內文...")
        content_zh = translate_text(content_ru)

        return {
            "分類": category,
            "日期": date_str,
            "標題_中文": title_zh,
            "標題_俄文": title_ru,
            "內文_中文": content_zh,
            "內文_俄文": content_ru,
            "網址": url,
            "下載時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"解析文章失敗: {url}, 錯誤: {e}")
        return None

def save_to_excel_optimized(df, full_path):
    """
    接收完整路徑並儲存 Excel
    """
    writer = pd.ExcelWriter(full_path, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Interfax新聞')
    
    worksheet = writer.sheets['Interfax新聞']
    column_settings = {
        'A': 10, 'B': 20, 'C': 40, 'D': 40, 'E': 60, 'F': 60, 'G': 40, 'H': 20
    }
    for col_letter, width in column_settings.items():
        worksheet.column_dimensions[col_letter].width = width
    
    for row in range(2, len(df) + 2):
        for col in [5, 6]: 
            worksheet.cell(row=row, column=col).alignment = Alignment(wrap_text=True, vertical='top')
    
    writer.close()
    print(f"Excel 已儲存: {full_path}")

# ================= 主程式 =================

def main():
    print(f"=== Interfax Ukraine 爬蟲啟動 ===")
    
    # --- 處理傳入的路徑參數 ---
    if len(sys.argv) > 1:
        save_dir = sys.argv[1]
    else:
        save_dir = "."

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    all_data = []
    
    for cat_name, cat_url in CATEGORIES.items():
        links = get_article_links(cat_url)
        
        # 測試抓取前 5 篇 (可自行調整數量)
        for link in links[:5]: 
            article = parse_article(link, cat_name)
            if article:
                all_data.append(article)
                print(f"    -> 已收錄: {article['標題_中文'][:15]}...")

    if all_data:
        df = pd.DataFrame(all_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"Interfax_Ukraine_{timestamp}.xlsx"
        
        # 結合路徑與檔名
        full_excel_path = os.path.join(save_dir, filename)
        
        save_to_excel_optimized(df, full_excel_path)
        print(f"\n任務完成！共抓取 {len(all_data)} 篇新聞。")
    else:
        print("\n未抓取到任何資料。")

if __name__ == '__main__':
    main()
