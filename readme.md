# 📄 通用 AI 出題系統（多檔、多語、Markdown / Quizlet 匯出）

本專案使用 OpenAI GPT 模型，從上傳的各種文件（PDF、Word、PPT、Excel 等）自動產生考題與答案！  
支援多語系、多種題型、多檔合併出題與 Markdown / Quizlet 格式匯出，適合教育工作者、出版社或個人練習出題使用。

---

## 🚀 功能特色

- 📎 **上傳多檔**（PDF、DOCX、PPTX、XLSX）並自動解析
- ✅ **選擇題型**（單選、多選、問答、申論）
- 🌐 **多語系支援**（繁體中文／簡體中文／English／日本語）
- 🔢 **題目數量可調整**
- 📘 題目與 ✅ 答案分欄顯示
- 🧠 使用 GPT-4.1 模型出題（支援自訂 API Base）
- 🔐 支援 Huggingface Space 使用者自行輸入 LLM Key 與 Base URL（不會儲存金鑰）
- � 匯出為 Markdown 與 Quizlet 格式（TSV）

---

## 🛠 安裝與執行方式

### 1️⃣ 安裝必要套件

```bash
pip install -r requirements.txt
```

### 2️⃣ 金鑰設定方式

- **本地開發**：請建立 `.env` 檔案，內容如下，程式會自動讀取金鑰與 baseurl。
  ```
  OPENAI_API_KEY=sk-你的金鑰
  OPENAI_API_BASE=https://api.openai.com/v1
  ```
- **Huggingface Space 或未設 .env 時**：Gradio 介面會出現「LLM Key」與「Base URL」欄位，請手動輸入你的 API 金鑰與 baseurl（不會被儲存，僅用於本次請求）。

---

▶️ 執行方式

只需啟動一次 FastAPI 伺服器，UI 與 API 共用同一個 port：

```bash
uvicorn app:api_app --host 0.0.0.0 --port 7860
```

- 啟動後，瀏覽器開啟 `http://localhost:7860/` 可使用 Gradio 出題 UI
- 其他應用可呼叫 `http://localhost:7860/api/generate` 取得題目與答案

（如需單純本地開發測試，也可用 `python app.py`，但建議用 uvicorn 方式）

---
📂 專案檔案結構
```
.
├── app.py               # 主程式：Gradio UI 與出題邏輯
├── requirements.txt     # 所需套件清單
├── .env                 # API 金鑰與設定（請自行建立）
└── README.md            # 專案說明
```


⸻

📌 注意事項
- 每次請求僅使用前 200,000 字元的文字進行出題（避免超過 token 限制）
- 題目與答案格式由 GPT 模型產生，請確保回傳中含有【答案】、[Answer:]、【答え】等標記
- 請確保你的 OpenAI API 金鑰已啟用 GPT-4.1 權限（或對應的 Azure 模型）
- 若於 Huggingface Space 使用，請自行輸入 LLM Key 與 Base URL，金鑰不會被儲存，僅用於本次請求

---

## 🌐 API 使用方式

本專案同時支援 HTTP API，方便其他應用程式直接呼叫產生題目。UI 與 API 共用同一個伺服器與 port。

### 路徑說明

- Gradio UI：`/`（例如 http://localhost:7860/）
- API：`/api/generate`（例如 http://localhost:7860/api/generate）

### API 路由

- `POST /api/generate`
- Content-Type: `multipart/form-data`
- 參數：
  - `files`：上傳檔案（可多檔）
  - `question_types`：題型（可多值，如 ["單選選擇題", "問答題"]）
  - `num_questions`：題目數量（整數）
  - `lang`：語言（"繁體中文"、"簡體中文"、"English"、"日本語"）
  - `llm_key`：LLM 金鑰（可選，未填則用 .env）
  - `baseurl`：API Base URL（可選，未填則用 .env）

#### 回傳格式

```json
{
  "questions": "題目內容...",
  "answers": "答案內容..."
}
```

---

🧠 延伸功能建議（可未來開發）
	•	✅ 答題互動模式（點選選項答題）
	•	✅ 題庫匯出為 Google Sheet / CSV / SQLite
	•	✅ 難度標記與知識點分類
	•	✅ 支援圖像 OCR、語音轉文字與 EPUB、ZIP 解壓
