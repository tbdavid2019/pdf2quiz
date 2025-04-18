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
- 📤 匯出為 Markdown 與 Quizlet 格式（TSV）

---

## 🛠 安裝與執行方式

### 1️⃣ 安裝必要套件

```bash
pip install -r requirements.txt

2️⃣ 建立 .env 檔案

OPENAI_API_KEY=sk-你的金鑰
OPENAI_API_BASE=https://api.openai.com/v1

若使用 Azure OpenAI，請另外加上：

OPENAI_API_TYPE=azure
OPENAI_API_VERSION=2024-04-01-preview



⸻

▶️ 執行方式

python app.py

啟動後將開啟本地 Gradio 網頁介面，讓你自由上傳檔案、選擇題型與語言，自動產生考題與答案。

⸻

📂 專案檔案結構

.
├── app.py               # 主程式：Gradio UI 與出題邏輯
├── requirements.txt     # 所需套件清單
├── .env                 # API 金鑰與設定（請自行建立）
└── README.md            # 專案說明



⸻

📌 注意事項
	•	每次請求僅使用前 20,000 字元的文字進行出題（避免超過 token 限制）
	•	題目與答案格式由 GPT 模型產生，請確保回傳中含有【答案】、[Answer:]、【答え】等標記
	•	請確保你的 OpenAI API 金鑰已啟用 GPT-4.1 權限（或對應的 Azure 模型）

⸻

🧠 延伸功能建議（可未來開發）
	•	✅ 答題互動模式（點選選項答題）
	•	✅ 題庫匯出為 Google Sheet / CSV / SQLite
	•	✅ 難度標記與知識點分類
	•	✅ 支援圖像 OCR、語音轉文字與 EPUB、ZIP 解壓
