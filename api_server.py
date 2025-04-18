from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import tempfile
from app import generate_questions

api_app = FastAPI(title="AI 出題系統 API")

@api_app.post("/api/generate")
async def api_generate(
    files: List[UploadFile] = File(...),
    question_types: List[str] = Form(...),
    num_questions: int = Form(...),
    lang: str = Form(...),
    llm_key: Optional[str] = Form(None),
    baseurl: Optional[str] = Form(None)
):
    temp_files = []
    for f in files:
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(await f.read())
        temp.flush()
        temp_files.append(temp)
        temp.name = temp.name

    questions, answers = generate_questions(
        temp_files, question_types, num_questions, lang, llm_key, baseurl
    )

    for temp in temp_files:
        temp.close()

    return JSONResponse({"questions": questions, "answers": answers})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:api_app", host="0.0.0.0", port=7861, reload=True)