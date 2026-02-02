import os
import glob
import subprocess
import time
import sys

# ================= 設定區 =================
# 爬蟲程式所在的資料夾
SCRIPTS_DIR = r'D:\Crawl_News'

# 資料要儲存的目標資料夾
DATA_OUTPUT_DIR = r'D:\Crawl_Data'

# 如果你的主程式放在同一個資料夾，請填寫主程式的名稱，避免重複執行到自己
MASTER_SCRIPT_NAME = 'run_all.py' 
# ==========================================

def run_crawlers():
    # 1. 確保資料輸出資料夾存在，不存在就建立它
    if not os.path.exists(DATA_OUTPUT_DIR):
        os.makedirs(DATA_OUTPUT_DIR)
        print(f"已建立資料夾: {DATA_OUTPUT_DIR}")

    # 2. 抓取資料夾內所有的 .py 檔案
    # 使用 os.path.join 確保路徑在 Windows 下正確
    search_path = os.path.join(SCRIPTS_DIR, "*.py")
    files = glob.glob(search_path)

    print(f"=== 偵測到 {len(files)} 個 Python 檔案，準備依序執行 ===")
    print(f"目標儲存路徑: {DATA_OUTPUT_DIR}\n")

    for file_path in files:
        file_name = os.path.basename(file_path)

        # 跳過主程式自己，以免無限迴圈
        if file_name == MASTER_SCRIPT_NAME:
            continue

        print(f"--------------------------------------------------")
        print(f"正在執行爬蟲: {file_name} ...")
        
        start_time = time.time()
        
        try:
            # 3. 執行爬蟲
            # 我們將 'DATA_OUTPUT_DIR' 作為參數傳給爬蟲程式 (詳見下方的說明)
            # cwd=SCRIPTS_DIR 確保爬蟲是在自己的資料夾環境下執行 (避免找不到 import)
            result = subprocess.run(
                ['python', file_path, DATA_OUTPUT_DIR], 
                cwd=SCRIPTS_DIR,
                check=True
            )
            
            elapsed_time = time.time() - start_time
            print(f"✅ 執行成功: {file_name} (耗時: {elapsed_time:.2f} 秒)")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 執行失敗: {file_name}")
            print(f"錯誤代碼: {e.returncode}")
        except Exception as e:
            print(f"❌ 發生未預期錯誤: {e}")

        # (選用) 每個爬蟲跑完休息 2 秒
        time.sleep(2)

    print("\n==================================================")
    print("所有排程已執行完畢。")

if __name__ == '__main__':
    run_crawlers()