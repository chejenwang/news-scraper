import requests
from bs4 import BeautifulSoup
import json
import time
import random
import pandas as pd
from datetime import datetime
from deep_translator import GoogleTranslator
import re
import sys  # <--- 新增：用於接收參數
import os   # <--- 新增：用於處理路徑

# ================= 設定區 =================

TARGET_SECTIONS = {
    "news": "https://www.ng.ru/news/",
    "armies": "https://www.ng.ru/armies/",
    "politics": "https://www.ng.ru/politics/",
    "economics": "https://www.ng.ru/economics/",
    "world": "https://www.ng.ru/world/"
}

# 設定每個欄目要抓幾頁
PAGES_TO_SCRAPE = 1

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://www.ng.ru/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

translator = GoogleTranslator(source='auto', target='zh-TW')

# ================= 工具函式 =================

def clean_text_for_excel(text):
    """ 過濾 Excel 不允許的非法字元 (如 ASCII 0-31 之間的控制碼) """
    if not isinstance(text, str):
        return text
    ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
    return ILLEGAL_CHARACTERS_RE.sub("", text)

def translate_text(text):
    if not text: return ""
    try:
        # NG 的內文通常很長，切片處理防止翻譯報錯
        if len(text) > 4000:
            text = text[:4000]
        return translator.translate(text)
    except Exception as e:
        print(f"  [翻譯錯誤] {e}")
        return text

def get_article_links(section_url):
    """ 抓取該欄目的文章連結 """
    links = []
    try:
        response = requests.get(section_url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 根據 NG 網站結構抓取標題連結
            items = soup.select('.news-list h2 a, .list-item a')
            for item in items:
                href = item.get('href')
                if href and href.startswith('/'):
                    links.append("https://www.ng.ru" + href)
        return list(dict.fromkeys(links))
    except Exception as e:
        print(f"  [列表錯誤] {e}")
        return []

def parse_article(url, category):
    """ 解析文章內容 """
    try:
        time.sleep(random.uniform(1.5, 3.0))
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.select_one('h1')
        title_ru = title_tag.text.strip() if title_tag else "無標題"
        
        date_tag = soup.select_one('.date, .article-date')
        date_str = date_tag.text.strip() if date_tag else "未知日期"
        
        content_div = soup.select_one('.article-content, .text')
        content_ru = content_div.get_text(separator='\n').strip() if content_div else ""

        print(f"  正在處理: {title_ru[:15]}...")
        title_zh = translate_text(title_ru)
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
        print(f"  [解析文章失敗] {url}: {e}")
        return None

# ================= 主程式 =================

def main():
    print(f"=== NG (俄羅斯獨立報) 爬蟲啟動 ===")
    
    # --- 處理傳入的路徑參數 ---
    if len(sys.argv) > 1:
        save_dir = sys.argv[1]
    else:
        save_dir = "."

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    all_data = []
    
    for section_name, section_url in TARGET_SECTIONS.items():
        print(f"\n正在讀取欄目: {section_name}")
        links = get_article_links(section_url)
        
        # 測試抓取每個欄目前 3 篇
        for link in links[:3]:
            article = parse_article(link, section_name)
            if article:
                all_data.append(article)

    if all_data:
        # 轉成 DataFrame
        df = pd.DataFrame(all_data)
        
        # 清洗非法字元，避免 Excel 報錯
        df = df.applymap(clean_text_for_excel)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # 儲存 JSON
        json_path = os.path.join(save_dir, f"ng_news_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
            
        # 儲存 Excel
        excel_path = os.path.join(save_dir, f"ng_news_{timestamp}.xlsx")
        df.to_excel(excel_path, index=False)
        
        print(f"\n✅ 任務完成！共抓取 {len(all_data)} 篇新聞。")
        print(f"檔案已儲存至: {save_dir}")
    else:
        print("\n未發現任何新聞資料。")

if __name__ == '__main__':
    main()
