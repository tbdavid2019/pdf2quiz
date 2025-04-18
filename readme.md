# 📄 PDF AI 出題系統

使用 OpenAI GPT 模型，從上傳的 PDF 內容中自動產生考題與答案！  
支援多種題型，包括單選、多選、問答與申論題。提供直觀的 Gradio UI 介面，適合教育工作者、出版社或個人練習出題使用。

---

## 🚀 功能介紹

- 📎 上傳 PDF 並自動解析文字內容
- ✅ 選擇題型（單選、多選、問答、申論）
- 🔢 自訂題目數量
- 📘 題目與 ✅ 答案分開顯示
- 🧠 使用 GPT-4.1 模型進行智慧出題（可搭配自訂 API 端點）

---

## 🛠 安裝方式

1. 安裝必要套件：

```bash
pip install -r requirements.txt

	2.	建立 .env 檔案，並填入你的 OpenAI 設定：

OPENAI_API_KEY=sk-你的金鑰
OPENAI_API_BASE=https://api.openai.com/v1

若使用 Azure OpenAI，請加上：

OPENAI_API_TYPE=azure
OPENAI_API_VERSION=2024-04-01-preview



⸻

▶️ 執行方式

python app.py

開啟後會啟動 Gradio 網頁介面，讓你上傳 PDF、選擇題型、產生題目與答案。

⸻

📂 檔案結構

.
├── app.py               # 主程式：Gradio 介面與出題邏輯
├── requirements.txt     # 所需套件
├── .env                 # API 金鑰與設定（請自行建立）
└── README.md            # 專案說明



⸻

📌 注意事項
	•	每次請求會送出 PDF 前段內容（預設最多 20,000 字元）給 OpenAI。
	•	題目與答案格式由 GPT 模型回傳結果解析，請確保回應格式清楚標註【答案】。
	•	若使用 GPT-4.1，請確認你的帳號與 API Key 有啟用相應權限。

⸻

🧠 延伸功能建議（可未來開發）
	•	答題互動模式（點選選項作答）
	•	題庫匯出（CSV / Word / Quizlet 格式）
	•	自動難度分級與知識點標記
	•	支援 DOCX、圖像 OCR（手寫試卷）

⸻
