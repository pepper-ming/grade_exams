# 自動化改考卷程式

這是一個用Python寫的自動化改考卷程式，使用Selenium操作瀏覽器進行登入，整合LLM API自動識別驗證碼。

## 文件說明

- `config.json` - 基本配置文件（不包含敏感資訊）
- `.env.example` - 環境變數範例文件
- `.env` - 實際環境變數文件（需自行創建，已在.gitignore中）
- `auto_grader.py` - **主程式**（支援完全自動化登入）
- `requirements.txt` - Python依賴套件
- `API_SETUP.md` - API密鑰設定說明

## 功能特色

✅ **完全自動化登入** - 無需人工干預  
✅ **智能驗證碼識別** - 支援Claude和GPT-4視覺模型  
✅ **多重備援機制** - API失敗時自動切換  
✅ **自動重試登入** - 失敗時自動重試多次  

## 快速開始

### 1. 安裝依賴套件
```bash
pip install -r requirements.txt
```

### 2. 設定環境變數
```bash
# 複製環境變數範例文件
cp .env.example .env
```
然後編輯 `.env` 文件，填入您的：
- `LOGIN_USERNAME` - 登入帳號
- `LOGIN_PASSWORD` - 登入密碼  
- `OPENAI_API_KEY` - OpenAI API密鑰
- `ANTHROPIC_API_KEY` - Anthropic API密鑰

參考 `API_SETUP.md` 了解如何取得API密鑰。

### 3. 執行程式
```bash
python auto_grader.py
```

## 程式流程

1. 🌐 開啟Chrome瀏覽器並訪問登入頁面
2. ✏️ 自動填寫帳號和密碼
3. 📷 抓取驗證碼圖片
4. 🤖 使用LLM API識別驗證碼
5. ✅ 自動完成登入
6. 🔄 失敗時自動重試（最多3次）

## 系統要求

- Python 3.8+
- Chrome瀏覽器
- 穩定的網路連線
- OpenAI或Anthropic API密鑰

## 注意事項

- 🔑 **API費用**：使用LLM API會產生少量費用
- 🔒 **密鑰安全**：請妥善保管您的API密鑰
- 🌐 **網路環境**：確保可正常訪問API服務

## 疑難排解

如遇問題，請檢查：
1. Chrome瀏覽器是否正確安裝
2. API密鑰是否正確設定
3. 網路連線是否正常
4. config.json格式是否正確