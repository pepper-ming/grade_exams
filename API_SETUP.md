# API設定說明

## 設定步驟

1. **編輯config.json文件**，替換API密鑰：

```json
"api": {
    "openai_api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "anthropic_api_key": "sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "preferred_provider": "anthropic"
}
```

## API密鑰獲取

### OpenAI API Key
1. 訪問 https://platform.openai.com/
2. 登入或註冊帳號
3. 前往 API Keys 頁面
4. 點擊 "Create new secret key"
5. 複製生成的API密鑰

### Anthropic API Key  
1. 訪問 https://console.anthropic.com/
2. 登入或註冊帳號
3. 前往 API Keys 頁面
4. 點擊 "Create Key"
5. 複製生成的API密鑰

## 建議設定

- **preferred_provider**: 建議使用 "anthropic"，Claude在圖片識別方面表現較佳
- 兩個API都設定可作為備援，當主要API失敗時會自動切換

## 注意事項

- **保護您的API密鑰**：不要將包含真實API密鑰的config.json上傳到公開代碼庫
- **API費用**：使用API會產生費用，建議設定使用限制
- **網路連線**：確保程式執行環境可以訪問API服務