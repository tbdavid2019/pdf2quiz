from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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

class QuestionItem(BaseModel):
    number: str = Field(..., description="題號")
    content: str = Field(..., description="題目內容")

class AnswerItem(BaseModel):
    number: str = Field(..., description="題號")
    content: str = Field(..., description="答案內容")

class GenerateResponse(BaseModel):
    questions: List[QuestionItem] = Field(..., description="題目列表，每個項目包含題號和內容")
    answers: List[AnswerItem] = Field(..., description="答案列表，每個項目包含題號和內容")
    raw_text: str = Field(..., description="原始文本格式（向後兼容）")

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
- `questions`：題目列表，每個項目包含題號（number）和內容（content）
- `answers`：答案列表，每個項目包含題號（number）和內容（content）
- `raw_text`：原始文本格式（向後兼容）
""",
    version="1.0.0"
)

# 添加 CORS 中間件
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允許所有來源，生產環境中應該限制為特定來源
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有 HTTP 標頭
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

    result, raw_text = generate_questions(
        temp_files, question_types, num_questions, lang, llm_key, baseurl
    )

    for temp in temp_files:
        temp.close()
    
    # 檢查是否有錯誤
    if isinstance(result, dict) and "error" in result:
        return JSONResponse(
            status_code=400,
            content={"detail": result["error"]}
        )
    
    # 將結果轉換為 API 回傳格式
    questions_list = []
    answers_list = []
    
    for q in result["questions"]:
        questions_list.append(QuestionItem(
            number=q["number"],
            content=q["content"]
        ))
    
    for a in result["answers"]:
        answers_list.append(AnswerItem(
            number=a["number"],
            content=a["content"]
        ))
    
    return GenerateResponse(
        questions=questions_list,
        answers=answers_list,
        raw_text=raw_text
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:api_app", host="0.0.0.0", port=7861, reload=True)