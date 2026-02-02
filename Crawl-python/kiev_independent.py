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
BASE_URL = "https://kyivindependent.com"
# 您指定的六個欄目
SECTIONS = ["war", "politics", "business", "russia", "europe", "opinion"]

# 模擬人類 Headers 避免被封鎖
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://kyivindependent.com/"
}

translator = GoogleTranslator(source='auto', target='zh-TW')

# ================= 工具函式 =================

def translate_text(text):
    if not text: return ""
    try:
        # 避免翻譯請求過快導致 IP 被鎖
        time.sleep(random.uniform(0.5, 1.2))
        if len(text) > 4500:
            return translator.translate(text[:4500]) + translator.translate(text[4500:9000])
        return translator.translate(text)
    except Exception as e:
        print(f"  [翻譯錯誤] {e}")
        return text

def parse_article_content(url):
    """ 解析單篇文章內文與中譯 """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200: return None, None, None, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 抓取日期與作者
        date_tag = soup.select_one('.article-date, time')
        date_str = date_tag.text.strip() if date_tag else "未知日期"
        
        author_tag = soup.select_one('.article-author, .author-name')
        author_str = author_tag.text.strip() if author_tag else "Kyiv Independent"

        # 抓取內文
        content_div = soup.select_one('.article-content, .post-content')
        if not content_div: return None, None, None, None
        
        paragraphs = content_div.find_all('p')
        full_text_en = "\n\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
        
        # 翻譯內文
        print(f"    正在翻譯內文 ({len(full_text_en)} 字)...")
        full_text_tw = translate_text(full_text_en)
        
        return date_str, author_str, full_text_en, full_text_tw
    except Exception as e:
        print(f"  [解析文章失敗] {url}: {e}")
        return None, None, None, None

def save_to_excel_optimized(df, full_output_path):
    """ 格式化並儲存 Excel """
    writer = pd.ExcelWriter(full_output_path, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='KyivIndependent')
    
    worksheet = writer.sheets['KyivIndependent']
    
    # 設定欄寬
    column_widths = {'A': 12, 'B': 15, 'C': 15, 'D': 40, 'E': 40, 'F': 60, 'G': 40}
    for col, width in column_widths.items():
        worksheet.column_dimensions[col].width = width
    
    # 內文換行設定
    for row in range(2, len(df) + 2):
        worksheet.cell(row=row, column=6).alignment = Alignment(wrap_text=True, vertical='top')
    
    writer.close()
    print(f"Excel 存檔成功: {full_output_path}")

# ================= 主程式 =================

def main():
    print(f"=== Kyiv Independent 爬蟲啟動 ===")
    
    # --- 處理傳入的路徑參數 ---
    if len(sys.argv) > 1:
        save_dir = sys.argv[1]
    else:
        save_dir = "."

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    all_final_data = []
    seen_urls = set()

    for section in SECTIONS:
        section_url = f"{BASE_URL}/{section}/"
        print(f"\n正在讀取欄目: {section.upper()}")
        
        try:
            response = requests.get(section_url, headers=HEADERS, timeout=15)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # 抓取文章清單 (根據網站結構調整 selector)
            links = soup.select('.article-title a, .post-title a')
            
            count = 0
            for link in links:
                full_url = link.get('href')
                if not full_url.startswith('http'):
                    full_url = BASE_URL + full_url
                
                if full_url not in seen_urls:
                    title_en = link.text.strip()
                    print(f"  發現文章: {title_en[:30]}...")
                    
                    # 翻譯標題
                    title_tw = translate_text(title_en)
                    
                    # 抓取內容
                    date, author, text_en, text_tw = parse_article_content(full_url)
                    
                    if text_tw: 
                        all_final_data.append({
                            "欄目": section.upper(),
                            "日期": date,
                            "作者": author,
                            "標題_英文": title_en,
                            "標題_中文": title_tw,
                            "內文_中文": text_tw,
                            "網址": full_url,
                            "下載時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        seen_urls.add(full_url)
                        count += 1
                
                # 測試模式：每個欄目抓 3 篇即可，避免跑太久
                if count >= 3: break
                    
        except Exception as e:
            print(f"  [欄目錯誤] {section}: {e}")

    # --- 儲存資料 ---
    if all_final_data:
        df = pd.DataFrame(all_final_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"KyivIndependent_{timestamp}.xlsx"
        
        # 結合路徑與檔名
        full_excel_path = os.path.join(save_dir, filename)
        
        save_to_excel_optimized(df, full_excel_path)
        print(f"\n全部任務完成！共抓取 {len(all_final_data)} 篇新聞。")
        print(f"資料夾位置: {save_dir}")
    else:
        print("\n未抓取到任何今日新聞。")

if __name__ == '__main__':
    main()
