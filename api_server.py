from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel, Field
import tempfile
import re
from app import generate_questions

# 定義有效的題型
type_map = {
    "單選選擇題": {
        "zh-Hant": "單選選擇題（每題四個選項）",
        "zh-Hans": "单选选择题（每题四个选项）",
        "en": "single choice question (4 options)",
        "ja": "四択問題"
    },
    "多選選擇題": {
        "zh-Hant": "多選選擇題（每題四到五個選項）",
        "zh-Hans": "多选选择题（每题四到五个选项）",
        "en": "multiple choice question (4-5 options)",
        "ja": "複数選択問題"
    },
    "問答題": {
        "zh-Hant": "簡答題",
        "zh-Hans": "简答题",
        "en": "short answer",
        "ja": "短答式問題"
    },
    "申論題": {
        "zh-Hant": "申論題",
        "zh-Hans": "申论题",
        "en": "essay question",
        "ja": "記述式問題"
    }
}

class GenerateResponse(BaseModel):
    questions: str = Field(..., description="題目卷內容（多題合併，格式為純文字）")
    answers: str = Field(..., description="答案內容（與題目順序對應，格式為純文字）")
    json_data: dict = Field(..., description="JSON格式的題目與答案，方便前端處理")

api_app = FastAPI(
    title="AI 出題系統 API",
    description="""
API 會根據上傳的文件自動產生題目與答案，支援多檔、多語、各種格式。
- `files`：上傳檔案（可多檔，支援 PDF, Word, PPT, Excel, 圖片, 音訊, ZIP, EPUB 等）
- `question_types`：題型（如 "單選選擇題,多選選擇題,問答題,申論題" 或 "單選選擇題、多選選擇題"，可用逗號或頓號分隔）
- `num_questions`：題目數量（整數）
- `lang`：語言（"繁體中文"、"簡體中文"、"English"、"日本語"）
- `llm_key`：LLM 金鑰（可選，未填則用 .env）
- `baseurl`：API Base URL（可選，未填則用 .env）

回傳內容：
- `questions`：題目卷內容（多題合併，格式為純文字）
- `answers`：答案內容（與題目順序對應，格式為純文字）
- `json_data`：JSON格式的題目與答案，包含 `items` 陣列，每個項目有 `question` 和 `answer` 欄位
""",
    version="1.0.0"
)

@api_app.post(
    "/api/generate",
    response_model=GenerateResponse,
    summary="產生題目與答案",
    description="根據上傳的文件自動產生題目卷與答案，支援多檔、多語、各種格式。"
)
async def api_generate(
    files: List[UploadFile] = File(..., description="上傳檔案（可多檔，支援 PDF, Word, PPT, Excel, 圖片, 音訊, ZIP, EPUB 等）"),
    question_types: str = Form(..., description="題型（如 單選選擇題,多選選擇題,問答題,申論題，用逗號或頓號分隔）"),
    num_questions: int = Form(..., description="題目數量"),
    lang: str = Form(..., description="語言（繁體中文,簡體中文,English,日本語）"),
    llm_key: Optional[str] = Form(None, description="LLM 金鑰（可選，未填則用 .env）"),
    baseurl: Optional[str] = Form(None, description="API Base URL（可選，未填則用 .env）")
):
    temp_files = []
    import os
    for f in files:
        ext = os.path.splitext(f.filename)[1]
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        temp.write(await f.read())
        temp.flush()
        temp_files.append(temp)
        temp.name = temp.name

    questions, answers = generate_questions(
        temp_files, question_types, num_questions, lang, llm_key, baseurl
    )

    for temp in temp_files:
        temp.close()

    # 將問題和答案分割成列表
    question_list = [q.strip() for q in questions.split("\n\n") if q.strip()]
    answer_list = [a.strip() for a in answers.split("\n\n") if a.strip()]
    
    # 過濾和重組題目與答案
    filtered_items = []
    current_question = ""
    current_answer = ""
    question_pattern = re.compile(r"^\d+\.\s+")
    
    
    # 尋找題號開頭的題目和對應答案
    for i, q in enumerate(question_list):
        # 如果是題號開頭的題目
        if question_pattern.match(q) or (i < len(question_list) - 1 and question_pattern.match(question_list[i+1])):
            # 如果已經有收集到的題目，先加入結果
            if current_question and current_answer:
                filtered_items.append({"question": current_question, "answer": current_answer})
            
            # 開始收集新題目
            current_question = q
            if i < len(answer_list):
                current_answer = answer_list[i]
            else:
                current_answer = ""
    
    # 加入最後一題
    if current_question and current_answer:
        filtered_items.append({"question": current_question, "answer": current_answer})
    
    # 如果沒有找到符合格式的題目，使用原始資料
    if not filtered_items:
        filtered_items = [{"question": q, "answer": a} for q, a in zip(question_list, answer_list)]
    
    # 組合成 JSON 格式
    json_data = {
        "items": filtered_items
    }
    
    return GenerateResponse(questions=questions, answers=answers, json_data=json_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:api_app", host="0.0.0.0", port=7861, reload=True)