import os
import glob
import subprocess
import time
import sys

# ================= 設定區 (自動偵測路徑) =================
# 取得目前這個 run_all.py 所在的絕對目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 爬蟲程式所在的資料夾 (設為與 run_all.py 相同)
SCRIPTS_DIR = BASE_DIR 

# 資料儲存路徑：優先使用 GitHub 傳入的參數，若無則在本地建立 data 資料夾
if len(sys.argv) > 1:
    DATA_OUTPUT_DIR = sys.argv[1]
else:
    DATA_OUTPUT_DIR = os.path.join(BASE_DIR, "data")

MASTER_SCRIPT_NAME = 'run_all.py' 
# =======================================================

def run_crawlers():
    if not os.path.exists(DATA_OUTPUT_DIR):
        os.makedirs(DATA_OUTPUT_DIR)
        print(f"✅ 已確認儲存資料夾: {DATA_OUTPUT_DIR}")

    # 搜尋該目錄下所有 .py 檔案
    search_path = os.path.join(SCRIPTS_DIR, "*.py")
    files = glob.glob(search_path)

    print(f"🚀 開始執行任務，偵測到 {len(files)-1} 個爬蟲腳本...")

    for file_path in files:
        file_name = os.path.basename(file_path)
        if file_name == MASTER_SCRIPT_NAME:
            continue

        print(f"\n>>> 正在執行: {file_name}")
        start_time = time.time()
        
        try:
            # 關鍵修正：在 GitHub (Linux) 必須使用 python3 指令
            python_cmd = 'python3' if sys.platform != 'win32' else 'python'
            
            # 執行爬蟲並傳入路徑參數
            subprocess.run(
                [python_cmd, file_path, DATA_OUTPUT_DIR], 
                check=True
            )
            print(f"✅ {file_name} 執行成功！")
        except Exception as e:
            print(f"❌ {file_name} 執行失敗: {e}")

if __name__ == "__main__":
    run_crawlers()
