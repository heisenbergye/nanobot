---
inclusion: always
---

# 開發環境規則

## 虛擬環境

**必須使用項目中的虛擬環境 `.venv`**

- 項目路徑: `d:\Users\zyzhan\projects\nanobot`
- 虛擬環境: `d:\Users\zyzhan\projects\nanobot\.venv`
- Python: `.venv\Scripts\python.exe`

執行 Python 時使用：
```
d:\Users\zyzhan\projects\nanobot\.venv\Scripts\python.exe script.py
```

或：
```
python -m nanobot ...
```
（在項目目錄下，會自動使用 .venv）

## Shell 選擇

**優先使用 Git Bash 或直接調用 Python，避免使用 PowerShell 和 CMD**

Git Bash 路徑：
```
D:\Users\zyzhan\AppData\Local\Programs\Git\bin\bash.exe
```

執行命令格式：
```bash
& "D:\Users\zyzhan\AppData\Local\Programs\Git\bin\bash.exe" -c "cd /d/Users/zyzhan/projects/nanobot && source .venv/Scripts/activate && your_command"
```

或直接用 Python：
```
python d:\Users\zyzhan\projects\nanobot\your_script.py
```

## 禁止

- ❌ 不要使用系統 Python
- ❌ 不要使用 PowerShell 特有語法
- ❌ 不要使用 CMD 特有語法
