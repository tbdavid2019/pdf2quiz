from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel, Field
import tempfile
from app import generate_questions

class GenerateResponse(BaseModel):
    questions: str = Field(..., description="題目卷內容（多題合併，格式為純文字）")
    answers: str = Field(..., description="答案內容（與題目順序對應，格式為純文字）")

api_app = FastAPI(
    title="AI 出題系統 API",
    description="""
API 會根據上傳的文件自動產生題目與答案，支援多檔、多語、各種格式。
- `files`：上傳檔案（可多檔，支援 PDF, Word, PPT, Excel, 圖片, 音訊, ZIP, EPUB 等）
- `question_types`：題型（如 ["單選選擇題", "多選選擇題", "問答題", "申論題"]）
- `num_questions`：題目數量（整數）
- `lang`：語言（"繁體中文"、"簡體中文"、"English"、"日本語"）
- `llm_key`：LLM 金鑰（可選，未填則用 .env）
- `baseurl`：API Base URL（可選，未填則用 .env）

回傳內容：
- `questions`：題目卷內容（多題合併，格式為純文字）
- `answers`：答案內容（與題目順序對應，格式為純文字）
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
    question_types: List[str] = Form(..., description="題型（如 單選選擇題、多選選擇題、問答題、申論題，可複選）"),
    num_questions: int = Form(..., description="題目數量"),
    lang: str = Form(..., description="語言（繁體中文、簡體中文、English、日本語）"),
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

    return GenerateResponse(questions=questions, answers=answers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:api_app", host="0.0.0.0", port=7861, reload=True)