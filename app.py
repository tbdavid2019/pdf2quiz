import gradio as gr
from openai import OpenAI
import os
import tempfile
from dotenv import load_dotenv
from markitdown import MarkItDown

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")
client = OpenAI(api_key=api_key, base_url=api_base)

# ✅ 合併多檔案文字

def extract_text_from_files(files):
    md = MarkItDown()
    merged_text = ""
    for f in files:
        result = md.convert(f.name)
        merged_text += result.text_content + "\n"
    return merged_text

# ✅ 產出題目與答案（根據語言與題型）

def generate_questions(files, question_types, num_questions, lang):
    try:
        text = extract_text_from_files(files)
        trimmed_text = text[:20000]

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

        prompt_map = {
            "繁體中文": "你是一位專業的出題者，請根據以下內容，設計 {n} 題以下類型的題目：{types}。每題後面請標註【答案】。內容如下：\n{text}",
            "簡體中文": "你是一位专业的出题者，请根据以下内容，设计 {n} 题以下类型的题目：{types}。每题后面请标注【答案】。内容如下：\n{text}",
            "English": "You are a professional exam writer. Based on the following content, generate {n} questions of types: {types}. Please mark the answer after each question using [Answer:]. Content:\n{text}",
            "日本語": "あなたはプロの出題者です。以下の内容に基づいて、{types}を含む{n}問の問題を作成してください。各問題の後に【答え】を付けてください。内容：\n{text}"
        }

        lang_key_map = {
            "繁體中文": "zh-Hant",
            "簡體中文": "zh-Hans",
            "English": "en",
            "日本語": "ja"
        }

        lang_key = lang_key_map[lang]
        types_str = "、".join([type_map[t][lang_key] for t in question_types])
        prompt = prompt_map[lang].format(n=num_questions, types=types_str, text=trimmed_text)

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content

        questions, answers = [], []
        for line in content.strip().split("\n"):
            if not line.strip():
                continue
            try:
                if "【答案】" in line:
                    q, a = line.split("【答案】", 1)
                elif "[Answer:" in line:
                    q, a = line.split("[Answer:", 1)
                    a = a.rstrip("]")
                elif "【答え】" in line:
                    q, a = line.split("【答え】", 1)
                else:
                    questions.append(line.strip())
                    answers.append("")
                    continue
                questions.append(q.strip())
                answers.append(a.strip())
            except Exception:
                questions.append(line.strip())
                answers.append("")

        if not questions:
            return "⚠️ 無法解析 AI 回傳內容，請檢查輸入內容或稍後再試。", ""

        return "\n\n".join(questions), "\n\n".join(answers)
    except Exception as e:
        return f"⚠️ 發生錯誤：{str(e)}", ""

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

def main():
    with gr.Blocks() as demo:
        gr.Markdown("# 📄 通用 AI 出題系統（支援多檔、多語、匯出格式）")

        with gr.Row():
            with gr.Column():
                file_input = gr.File(label="上傳文件（可多檔）", file_types=[".pdf", ".docx", ".pptx", ".xlsx"], file_count="multiple")
                lang = gr.Dropdown(["繁體中文", "簡體中文", "English", "日本語"], value="繁體中文", label="語言 Language")
                question_types = gr.CheckboxGroup(["單選選擇題", "多選選擇題", "問答題", "申論題"],
                                                  label="選擇題型（可複選）",
                                                  value=["單選選擇題"])
                num_questions = gr.Slider(1, 10, value=3, step=1, label="題目數量")
                generate_btn = gr.Button("✏️ 開始出題")

            with gr.Column():
                qbox = gr.Textbox(label="📘 題目 Questions", lines=15)
                abox = gr.Textbox(label="✅ 解答 Answers", lines=15)
                export_btn = gr.Button("📤 匯出 Markdown / Quizlet")
                md_out = gr.File(label="📝 Markdown 檔下載")
                quizlet_out = gr.File(label="📋 Quizlet (TSV) 檔下載")

        generate_btn.click(fn=generate_questions,
                           inputs=[file_input, question_types, num_questions, lang],
                           outputs=[qbox, abox])

        export_btn.click(fn=export_files,
                         inputs=[qbox, abox],
                         outputs=[md_out, quizlet_out])

    demo.launch()

if __name__ == "__main__":
    main()