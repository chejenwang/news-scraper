import os, glob, subprocess, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 爬蟲跟 run_all.py 放一起
DATA_DIR = os.path.join(BASE_DIR, "data")
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

python_cmd = 'python3' if sys.platform != 'win32' else 'python'
files = glob.glob(os.path.join(BASE_DIR, "*.py"))

for f in files:
    name = os.path.basename(f)
    if name == 'run_all.py': continue
    print(f">>> 執行: {name}")
    # 傳入 data 資料夾路徑當作參數
    subprocess.run([python_cmd, f, DATA_DIR])
