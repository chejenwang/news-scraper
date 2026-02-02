import os
import glob
import subprocess
import time
import sys

# ================= 設定區 (自動偵測路徑) =================
# 自動取得目前 run_all.py 檔案所在的資料夾
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 爬蟲程式所在的資料夾 (設為與 run_all.py 相同目錄)
SCRIPTS_DIR = CURRENT_DIR

# 資料要儲存的目標資料夾 (優先使用參數傳入的路徑，沒有則在目前目錄建立 data)
if len(sys.argv) > 1:
    DATA_OUTPUT_DIR = sys.argv[1]
else:
    DATA_OUTPUT_DIR = os.path.join(CURRENT_DIR, "data")

MASTER_SCRIPT_NAME = 'run_all.py' 
# =======================================================

def run_crawlers():
    if not os.path.exists(DATA_OUTPUT_DIR):
        os.makedirs(DATA_OUTPUT_DIR)
        print(f"✅ 已建立儲存資料夾: {DATA_OUTPUT_DIR}")

    # 搜尋同資料夾下所有的 .py 檔案
    search_path = os.path.join(SCRIPTS_DIR, "*.py")
    files = glob.glob(search_path)

    print(f"🚀 偵測到 {len(files)} 個檔案，準備執行...")

    for file_path in files:
        file_name = os.path.basename(file_path)
        
        # 跳過自己以及非爬蟲檔案
        if file_name == MASTER_SCRIPT_NAME:
            continue

        print(f"\n--- 執行中: {file_name} ---")
        start_time = time.time()
        
        try:
            # 在 GitHub (Linux) 環境下，必須明確指定 python3 執行
            # 並將目標儲存路徑當作參數傳給爬蟲
            subprocess.run(
                ['python3', file_path, DATA_OUTPUT_DIR], 
                check=True
            )
            print(f"✅ {file_name} 成功 (耗時: {time.time() - start_time:.1f}s)")
        except Exception as e:
            print(f"❌ {file_name} 失敗: {e}")

if __name__ == "__main__":
    run_crawlers()
