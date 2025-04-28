import gradio as gr
from openai import OpenAI
import os
import tempfile
import logging
from dotenv import load_dotenv
from markitdown import MarkItDown

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 輸出到控制台
        logging.FileHandler('pdf2quiz.log')  # 輸出到文件
    ]
)
logger = logging.getLogger('pdf2quiz')

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")
# 刪除全域 client，改由 generate_questions 動態初始化

# ✅ 合併多檔案文字

def extract_text_from_files(files, llm_key=None, baseurl=None, model_name=None):
    from openai import OpenAI
    import os

    # 優先使用 UI 傳入值，否則用 .env，最後才用默認值
    api_key = llm_key if llm_key else os.getenv("OPENAI_API_KEY")
    api_base = baseurl if baseurl else os.getenv("OPENAI_API_BASE")
    model = model_name if model_name else os.getenv("OPENAI_MODEL", "gpt-4.1")
    client = OpenAI(api_key=api_key, base_url=api_base)
    
    logger.info(f"extract_text_from_files 使用的 API 設定 - Base URL: {api_base[:10] if api_base else 'None'}..., Model: {model}")

    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    merged_text = ""
    for f in files:
        ext = os.path.splitext(f.name)[1].lower()
        filename = os.path.basename(f.name)
        logger.info(f"處理文件: {filename} (類型: {ext})")
        
        # 圖片文件直接使用 AI 處理
        if ext in image_exts:
            logger.info(f"使用 AI 處理圖片文件: {filename}")
            md = MarkItDown(llm_client=client, llm_model=model)
            result = md.convert(f.name)
            merged_text += result.text_content + "\n"
            logger.info(f"圖片文件處理完成: {filename}, 提取文本長度: {len(result.text_content)}")
        # PDF 文件先嘗試普通處理，如果提取不到足夠文本再使用 AI
        elif ext.lower() == ".pdf":
            # 先嘗試普通方式處理
            logger.info(f"嘗試普通方式處理 PDF 文件: {filename}")
            md = MarkItDown()
            result = md.convert(f.name)
            
            # 檢查提取的文本是否足夠
            text_length = len(result.text_content.strip()) if result.text_content else 0
            logger.info(f"普通處理提取文本長度: {text_length}")
            
            # 如果文本太少（少於 100 個字符），可能是掃描版 PDF，需要 AI 處理
            if result.text_content and text_length > 100:
                logger.info(f"普通處理成功，文本足夠: {filename}")
                merged_text += result.text_content + "\n"
            else:
                # 文本太少，可能是掃描版 PDF，使用 AI 處理
                logger.info(f"普通處理提取文本不足，切換到 AI 處理: {filename}")
                md = MarkItDown(llm_client=client, llm_model=model)
                result = md.convert(f.name)
                merged_text += result.text_content + "\n"
                logger.info(f"AI 處理完成: {filename}, 提取文本長度: {len(result.text_content)}")
        # 其他文件類型使用普通處理
        else:
            logger.info(f"使用普通方式處理文件: {filename}")
            md = MarkItDown()
            result = md.convert(f.name)
            merged_text += result.text_content + "\n"
            logger.info(f"文件處理完成: {filename}, 提取文本長度: {len(result.text_content)}")
    return merged_text

# ✅ 產出題目與答案（根據語言與題型）

def generate_questions(files, question_types, num_questions, lang, llm_key, baseurl, model=None):
    try:
        # 優先使用 UI 傳入值，否則用 .env，最後才用默認值
        key = llm_key if llm_key else os.getenv("OPENAI_API_KEY")
        base = baseurl if baseurl else os.getenv("OPENAI_API_BASE")
        model_name = model if model else os.getenv("OPENAI_MODEL", "gpt-4.1")
        
        logger.info(f"generate_questions 使用的 API 設定 - Base URL: {base[:10] if base else 'None'}..., Model: {model_name}")
        
        # 將 UI 傳入的值傳遞給 extract_text_from_files 函數
        text = extract_text_from_files(files, llm_key=key, baseurl=base, model_name=model_name)
        trimmed_text = text[:200000]

        # 這裡不需要再次設置 key, base 和 model_name，因為已經在上面設置過了
        if not key or not base:
            return {"error": "⚠️ 請輸入 LLM key 與 baseurl"}, ""
        client = OpenAI(api_key=key, base_url=base)

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

        # 修改提示詞，要求 LLM 直接產出結構化的題目和答案
        prompt_map = {
            "繁體中文": """你是一位專業的出題者，請根據以下內容，設計 {n} 題以下類型的題目：{types}。

請注意：你必須嚴格遵循指定的題型，如果要求是「單選選擇題」，就必須生成單選題，每題有四個選項(A,B,C,D)，而且只有一個正確答案。
如果要求是「多選選擇題」，就必須生成多選題，每題有四到五個選項，可以有多個正確答案。
如果要求是「問答題」，就必須生成簡答題，需要簡短的文字回答。
如果要求是「申論題」，就必須生成需要較長篇幅回答的開放式問題。

請嚴格按照以下格式輸出每個題目和答案：

題目1：[題目內容]
答案1：[答案內容]

題目2：[題目內容]
答案2：[答案內容]

...以此類推

請確保題號和答案號一一對應，不要使用其他格式。內容如下：
{text}""",
            "簡體中文": """你是一位专业的出题者，请根据以下内容，设计 {n} 题以下类型的题目：{types}。

请注意：你必须严格遵循指定的题型，如果要求是「单选选择题」，就必须生成单选题，每题有四个选项(A,B,C,D)，而且只有一个正确答案。
如果要求是「多选选择题」，就必须生成多选题，每题有四到五个选项，可以有多个正确答案。
如果要求是「问答题」，就必须生成简答题，需要简短的文字回答。
如果要求是「申论题」，就必须生成需要较长篇幅回答的开放式问题。

请严格按照以下格式输出每个题目和答案：

题目1：[题目内容]
答案1：[答案内容]

题目2：[题目内容]
答案2：[答案内容]

...以此类推

请确保题号和答案号一一对应，不要使用其他格式。内容如下：
{text}""",
            "English": """You are a professional exam writer. Based on the following content, generate {n} questions of types: {types}.

IMPORTANT: You must strictly follow the specified question types:
- If "single choice question" is requested, create multiple choice questions with four options (A,B,C,D) and only ONE correct answer.
- If "multiple choice question" is requested, create questions with 4-5 options where MORE THAN ONE option can be correct.
- If "short answer" is requested, create questions requiring brief text responses.
- If "essay question" is requested, create open-ended questions requiring longer responses.

Please strictly follow this format for each question and answer:

Question1: [question content]
Answer1: [answer content]

Question2: [question content]
Answer2: [answer content]

...and so on

Ensure that question numbers and answer numbers correspond exactly. Do not use any other format. Content:
{text}""",
            "日本語": """あなたはプロの出題者です。以下の内容に基づいて、{types}を含む{n}問の問題を作成してください。

重要：指定された問題タイプを厳守してください：
- 「四択問題」が要求された場合、4つの選択肢（A,B,C,D）があり、正解が1つだけの選択問題を作成してください。
- 「複数選択問題」が要求された場合、4〜5つの選択肢があり、複数の正解がある問題を作成してください。
- 「短答式問題」が要求された場合、簡潔な文章での回答が必要な問題を作成してください。
- 「記述式問題」が要求された場合、より長い回答が必要な開放型の問題を作成してください。

以下の形式で各問題と回答を出力してください：

問題1：[問題内容]
回答1：[回答内容]

問題2：[問題内容]
回答2：[回答内容]

...など

問題番号と回答番号が正確に対応していることを確認してください。他の形式は使用しないでください。内容：
{text}"""
        }

        lang_key_map = {
            "繁體中文": "zh-Hant",
            "簡體中文": "zh-Hans",
            "English": "en",
            "日本語": "ja"
        }

        lang_key = lang_key_map[lang]
        
        # 處理字串形式的 question_types（來自 API）
        if isinstance(question_types, str):
            # 先用逗號分隔，再用頓號分隔
            qt_list = []
            for part in question_types.split(","):
                for subpart in part.split("、"):
                    if subpart.strip():
                        qt_list.append(subpart.strip())
            question_types = qt_list
        
        # 檢查每個題型是否有效
        valid_types = list(type_map.keys())
        for t in question_types:
            if t not in valid_types:
                return {"error": f"⚠️ 無效的題型：{t}。有效題型為：{', '.join(valid_types)}"}, ""
        
        try:
            types_str = "、".join([type_map[t][lang_key] for t in question_types])
            prompt = prompt_map[lang].format(n=num_questions, types=types_str, text=trimmed_text)
        except Exception as e:
            return {"error": f"⚠️ 處理題型時發生錯誤：{str(e)}。question_types={question_types}"}, ""

        logger.info(f"發送請求到 LLM 模型: {model_name}")
        logger.info(f"使用語言: {lang}, 題型: {types_str}, 題目數量: {num_questions}")
        logger.info(f"選擇的題型: {question_types}")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        logger.info("LLM 回應成功，開始解析回應內容")

        # 解析 LLM 回傳的結構化內容
        import re
        
        # 初始化結果
        result = {
            "questions": [],
            "answers": []
        }
        
        # 根據語言選擇正則表達式模式
        if lang == "English":
            question_pattern = r"Question(\d+):\s*(.*?)(?=\nAnswer\d+:|$)"
            answer_pattern = r"Answer(\d+):\s*(.*?)(?=\nQuestion\d+:|$)"
        elif lang == "日本語":
            question_pattern = r"問題(\d+)：\s*(.*?)(?=\n回答\d+：|$)"
            answer_pattern = r"回答(\d+)：\s*(.*?)(?=\n問題\d+：|$)"
        else:  # 繁體中文 or 簡體中文
            question_pattern = r"題目(\d+)：\s*(.*?)(?=\n答案\d+：|$)"
            answer_pattern = r"答案(\d+)：\s*(.*?)(?=\n題目\d+：|$)"
        
        # 提取題目和答案
        questions_matches = re.findall(question_pattern, content, re.DOTALL)
        answers_matches = re.findall(answer_pattern, content, re.DOTALL)
        
        # 組織題目和答案
        questions_dict = {num: text.strip() for num, text in questions_matches}
        answers_dict = {num: text.strip() for num, text in answers_matches}
        
        # 確保題目和答案一一對應
        all_numbers = sorted(set(list(questions_dict.keys()) + list(answers_dict.keys())), key=int)
        
        for num in all_numbers:
            question = questions_dict.get(num, f"題目 {num} 缺失")
            answer = answers_dict.get(num, f"答案 {num} 缺失")
            
            result["questions"].append({
                "number": num,
                "content": question
            })
            
            result["answers"].append({
                "number": num,
                "content": answer
            })
        
        # 記錄提取的題目和答案
        if result["questions"]:
            logger.info(f"成功提取題目和答案: {len(result['questions'])} 題")
            for q in result["questions"]:
                logger.info(f"題目 {q['number']}: {q['content'][:50]}...")
            for a in result["answers"]:
                logger.info(f"答案 {a['number']}: {a['content'][:50]}...")
        
        # 如果沒有成功提取題目和答案，使用備用方法
        if not result["questions"]:
            logger.warning("主要解析方法失敗，嘗試備用方法")
            # 備用方法：按行分析
            lines = content.strip().split("\n")
            current_number = ""
            current_question = ""
            current_answer = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 嘗試匹配題目行
                q_match = None
                if lang == "English":
                    q_match = re.match(r"Question\s*(\d+):\s*(.*)", line)
                elif lang == "日本語":
                    q_match = re.match(r"問題\s*(\d+)：\s*(.*)", line)
                else:
                    q_match = re.match(r"題目\s*(\d+)：\s*(.*)", line)
                
                if q_match:
                    # 保存前一個題目和答案
                    if current_number and current_question:
                        result["questions"].append({
                            "number": current_number,
                            "content": current_question
                        })
                        result["answers"].append({
                            "number": current_number,
                            "content": current_answer
                        })
                    
                    # 開始新題目
                    current_number = q_match.group(1)
                    current_question = q_match.group(2)
                    current_answer = ""
                    continue
                
                # 嘗試匹配答案行
                a_match = None
                if lang == "English":
                    a_match = re.match(r"Answer\s*(\d+):\s*(.*)", line)
                elif lang == "日本語":
                    a_match = re.match(r"回答\s*(\d+)：\s*(.*)", line)
                else:
                    a_match = re.match(r"答案\s*(\d+)：\s*(.*)", line)
                
                if a_match and a_match.group(1) == current_number:
                    current_answer = a_match.group(2)
            
            # 保存最後一個題目和答案
            if current_number and current_question:
                result["questions"].append({
                    "number": current_number,
                    "content": current_question
                })
                result["answers"].append({
                    "number": current_number,
                    "content": current_answer
                })
        
        # 如果仍然沒有提取到題目和答案，返回錯誤
        if not result["questions"]:
            logger.error("無法解析 AI 回傳內容，所有解析方法都失敗")
            return {"error": "⚠️ 無法解析 AI 回傳內容，請檢查輸入內容或稍後再試。"}, ""
        
        logger.info(f"題目生成完成，共 {len(result['questions'])} 題")
        
        # 為了向後兼容，同時返回原始文本格式
        questions_text = "\n\n".join([f"題目{q['number']}：{q['content']}" for q in result["questions"]])
        answers_text = "\n\n".join([f"答案{a['number']}：{a['content']}" for a in result["answers"]])
        
        return result, questions_text + "\n\n" + answers_text
    except Exception as e:
        logger.exception(f"生成題目時發生錯誤: {str(e)}")
        return {"error": f"⚠️ 發生錯誤：{str(e)}"}, ""

# ✅ 匯出 Markdown, Quizlet（TSV）

def export_files(questions_text, answers_text):
    md_path = tempfile.NamedTemporaryFile(delete=False, suffix=".md").name
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 📘 題目 Questions\n\n" + questions_text + "\n\n# ✅ 解答 Answers\n\n" + answers_text)

    quizlet_path = tempfile.NamedTemporaryFile(delete=False, suffix=".tsv").name
    with open(quizlet_path, "w", encoding="utf-8") as f:
        for q, a in zip(questions_text.split("\n\n"), answers_text.split("\n\n")):
            q_clean = q.replace("\n", " ").replace("\r", " ")
            a_clean = a.replace("\n", " ").replace("\r", " ")
            f.write(f"{q_clean}\t{a_clean}\n")

    return md_path, quizlet_path

# ✅ Gradio UI

# --- FastAPI + Gradio 整合 ---
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import uvicorn

def build_gradio_blocks():
    with gr.Blocks() as demo:
        gr.Markdown("# 📄 通用 AI 出題系統（支援多檔、多語、匯出格式）- DAVID888 ")

        with gr.Row():
            with gr.Column():
                file_input = gr.File(
                    label="上傳文件（可多檔）",
                    file_types=[
                        ".pdf", ".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx", ".csv",
                        ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp",
                        ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".amr", ".wma", ".opus",
                        ".html", ".htm", ".json", ".xml", ".txt", ".md", ".rtf", ".log",
                        ".zip", ".epub"
                    ],
                    file_count="multiple"
                )
                lang = gr.Dropdown(["繁體中文", "簡體中文", "English", "日本語"], value="繁體中文", label="語言 Language")
                question_types = gr.CheckboxGroup(["單選選擇題", "多選選擇題", "問答題", "申論題"],
                                                  label="選擇題型（可複選）",
                                                  value=["單選選擇題"])
                num_questions = gr.Slider(1, 20, value=10, step=1, label="題目數量")
                llm_key = gr.Textbox(label="LLM Key (不會儲存)", type="password", placeholder="請輸入你的 LLM API Key，留空則使用 .env 設定")
                baseurl = gr.Textbox(label="Base URL (如 https://api.groq.com/openai/v1 )", placeholder="請輸入 API Base URL，留空則使用 .env 設定")
                model_box = gr.Textbox(label="Model 名稱", placeholder="如 gpt-4.1, qwen-qwq-32b, ...，留空則使用 .env 設定")
                generate_btn = gr.Button("✏️ 開始出題 quiz")

            with gr.Column():
                qbox = gr.Textbox(label="📘 題目 Questions", lines=15)
                abox = gr.Textbox(label="✅ 解答 Answers", lines=15)
                export_btn = gr.Button("📤 匯出 Markdown / Quizlet")
                md_out = gr.File(label="📝 Markdown 檔下載")
                quizlet_out = gr.File(label="📋 Quizlet (TSV) 檔下載")


        # 包裝函數，將 generate_questions 的回傳值轉換為 Gradio UI 需要的格式
        def generate_questions_for_gradio(files, question_types, num_questions, lang, llm_key, baseurl, model):
            result, raw_text = generate_questions(files, question_types, num_questions, lang, llm_key, baseurl, model)
            
            # 檢查是否有錯誤
            if isinstance(result, dict) and "error" in result:
                return result["error"], ""
            
            # 分割原始文本為題目和答案
            parts = raw_text.split("\n\n")
            questions_part = ""
            answers_part = ""
            
            for part in parts:
                if part.startswith("題目") or part.startswith("Question") or part.startswith("問題"):
                    questions_part += part + "\n\n"
                elif part.startswith("答案") or part.startswith("Answer") or part.startswith("回答"):
                    answers_part += part + "\n\n"
            
            return questions_part.strip(), answers_part.strip()
        
        generate_btn.click(fn=generate_questions_for_gradio,
                           inputs=[file_input, question_types, num_questions, lang, llm_key, baseurl, model_box],
                           outputs=[qbox, abox])

        export_btn.click(fn=export_files,
                         inputs=[qbox, abox],
                         outputs=[md_out, quizlet_out])
    return demo

if __name__ == "__main__":
    demo = build_gradio_blocks()
    demo.launch()

# --- FastAPI API 介面 ---
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import uvicorn

api_app = FastAPI(title="AI 出題系統 API")

@api_app.post("/api/generate")
async def api_generate(
    files: List[UploadFile] = File(...),
    question_types: List[str] = Form(...),
    num_questions: int = Form(...),
    lang: str = Form(...),
    llm_key: Optional[str] = Form(None),
    baseurl: Optional[str] = Form(None),
    model: Optional[str] = Form(None)
):
    # 將 UploadFile 轉為臨時檔案物件，與 Gradio 行為一致
    temp_files = []
    for f in files:
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(await f.read())
        temp.flush()
        temp_files.append(temp)
        temp.name = temp.name  # 保持介面一致

    # 呼叫原本的出題邏輯
    questions, answers = generate_questions(
        temp_files, question_types, num_questions, lang, llm_key, baseurl, model
    )

    # 關閉臨時檔案
    for temp in temp_files:
        temp.close()

    return JSONResponse({"questions": questions, "answers": answers})

# 若要啟動 API 伺服器，請執行：
# uvicorn app:api_app --host 0.0.0.0 --port 7861
