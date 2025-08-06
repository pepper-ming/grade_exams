# 安全說明

## 敏感資訊管理

本專案採用環境變數（`.env` 檔案）來管理敏感資訊，確保安全性：

### 🔒 敏感檔案

以下檔案包含敏感資訊，**絕對不應該**提交到版本控制系統：

- `.env` - 包含實際的API密鑰和登入憑證
- `config.json.bak` - 備份檔案（可能包含敏感資訊）
- `captcha_images/` - 驗證碼圖片目錄

這些檔案已加入 `.gitignore` 中。

### ✅ 安全檔案

以下檔案是安全的，可以提交到版本控制：

- `config.json` - 基本配置（不包含敏感資訊）
- `.env.example` - 環境變數範例（不包含真實密鑰）
- 所有程式碼檔案

### 🔧 設定指南

1. **複製範例檔案**：
   ```bash
   cp .env.example .env
   ```

2. **編輯 .env 檔案**，填入真實的值：
   ```env
   LOGIN_USERNAME=your_actual_username
   LOGIN_PASSWORD=your_actual_password
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

3. **確認 .gitignore**：
   確保 `.env` 已加入 `.gitignore`，避免意外提交。

### ⚠️ 注意事項

- 絕不要在程式碼中硬編碼密鑰
- 不要在聊天或郵件中分享 `.env` 檔案內容  
- 定期更換API密鑰
- 如果意外提交了敏感資訊，立即更換相關密鑰

### 🔍 檢查清單

提交程式碼前，請確認：

- [ ] `.env` 檔案未被追蹤
- [ ] 沒有硬編碼的密鑰在程式碼中
- [ ] `.gitignore` 包含所有敏感檔案
- [ ] README.md 有正確的設定說明