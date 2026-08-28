import os
import json
import re
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("Validation error detail:", exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Pydanticモデル（response_schemaとしてGeminiに渡すクラス）
class SoapResponse(BaseModel):
    progress: str = Field(
        description="【現病歴】内容\n【画像所見】X線：...\nの形式で記述。情報がない場合は空文字"
    )
    notice: str = Field(
        description="既往歴・体重・仕事に関する情報。存在しない項目は含めず、情報がない場合は空文字"
    )
    s: str = Field(
        description="患者自身の言葉(疼痛部位・疼痛動作・疼痛時間・疼痛の性質・疼痛範囲・疼痛寛解動作など)のみ。鍵カッコ「」を使用"
    )
    o: str = Field(
        description="ROM、MMT、圧痛(Td)、疼痛誘発・寛解テスト、立位(CSL・骨盤前方回旋・体幹回旋)、動作観察(片足立ちスウェイ)などの客観的データ"
    )
    a: str = Field(
        description="評価・病態解釈・鑑別理由"
    )
    p: str = Field(
        description="#1 関節可動域訓練 #2 筋力強化訓練 #3 バランス訓練 #4 自主トレーニング指導"
    )

# システムインストラクション（AIに対する絶対規則）
SYSTEM_INSTRUCTION = """あなたは理学療法士向けの専門カルテ（SOAP）記録生成AIです。提供された情報（テキスト、画像、ファイル）を分析し、理学療法記録として正確かつ厳格に構造化したデータを作成してください。

■ 情報の優先順位（情報に矛盾がある場合）:
1. 院内カルテ画像（最優先・公式記録）
2. 構造化テンプレート入力
3. 臨床メモ画像
4. フリーテキスト入力
※ 優先度が高い情報源の内容を採用し、低い情報源の矛盾する内容は出力に含めないでください。

■ 各項目の厳格な記載ルール:

【progress（経過）】
- 必ず「【現病歴】」で始めてください。「現病歴：」などの表記は不可です。
- 画像所見が存在する場合は、必ず直前で改行し、以下のように別行で記載してください：
  【現病歴】[現病歴の内容]
  【画像所見】
  X線：[所見内容]（撮影日）
  MRI：[所見内容]（撮影日）
- 画像所見の情報が存在しない場合は【画像所見】の行自体を出力しないでください。

【notice（注意点）】
- 入力情報内に存在する項目のみ「既往歴：」「体重：」「仕事：」の形式で記載してください。
- 該当する情報が一切ない場合は空文字 ("") としてください。

【s（Subjective）】
- 患者自身の言葉(疼痛部位・疼痛動作・疼痛時間・疼痛の性質・疼痛範囲・疼痛寛解動作など)のみを記載してください。
- 鍵カッコ「 」を用いて表現してください。推測での加筆・言い換えは禁止です。

【o（Objective）】
- ROM、MMT、圧痛(Td)、疼痛誘発テスト・疼痛寛解テスト、立位（CSLの左右差・骨盤前方回旋側・体幹回旋）・動作観察(片足立ちのスウェイ側)などの客観的データを記載してください。
※参考定義:
- CSL（Center Sacral Line）評価：仙骨中央からの垂線に対する第7頸椎の位置や、体幹の横へのシフト（右シフト/左シフト）
- 踏み出し側/蹴り出し側の予測・特徴をふまえた評価所見を抽出してください。
- 骨盤前方回旋テスト：左右差がある場合はそちらが踏み出し側になりやすい。
- 骨盤スウェイテスト：側方swayが大きい側が股関節内転位傾向・能動制御ができていない（受動支持）。

【a（Assessment）】
- SおよびOのデータに基づく臨床的解釈、病態の推測、機能障害の根拠を記載してください。

【p（Plan）】
- 以下の項目だけを必ず転記してください：
  #1 関節可動域訓練
  #2 筋力強化訓練
  #3 バランス訓練
  #4 自主トレーニング指導

■ 出力必須ルール:
- 6つのキー（progress, notice, s, o, a, p）は必ずすべて出力してください。
- 該当する情報が入力に一切存在しない項目は、キーを残したまま値を空文字列 "" にしてください。
- 存在しない情報を推測・創作しないでください（ハルシネーション禁止）。
"""

@app.post("/api/generate-soap")
async def generate_soap(request: Request):
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Gemini API Key is not configured."
            )

        body = await request.json()
        input_text = body.get("inputText", "")
        karte_images = body.get("karteImages", [])
        memo_images = body.get("memoImages", [])
        attached_files = body.get("attachedFiles", [])

        if not input_text and not karte_images and not memo_images and not attached_files:
            raise HTTPException(
                status_code=400,
                detail="At least one input (text, image, or file) must be provided."
            )

        template_context = ""
        if "S (Subjective)" in input_text or "O (Objective)" in input_text or "A (Assessment)" in input_text:
            sub_match = re.search(r'S \(Subjective\)([\s\S]*?)(?=O \(Objective\)|$)', input_text)
            obj_match = re.search(r'O \(Objective\)([\s\S]*?)(?=A \(Assessment\)|$)', input_text)
            ass_match = re.search(r'A \(Assessment\)([\s\S]*?)$', input_text)

            def safe_truncate(text, limit=200):
                if not text:
                    return ""
                t = text.strip()
                return t if len(t) <= limit else t[:limit] + "（以下省略）"

            parsed_s = safe_truncate(sub_match.group(1) if sub_match else "")
            parsed_o = safe_truncate(obj_match.group(1) if obj_match else "")
            parsed_a = safe_truncate(ass_match.group(1) if ass_match else "")

            template_context = f"""【検出された構造化テンプレート情報】
主訴情報: {parsed_s}
所見情報: {parsed_o}
評価情報: {parsed_a}

これらの構造化データを優先的に参照してください。
"""

        user_prompt = f"""以下の入力データを解析し、指定されたルールに従ってSOAPカルテを生成してください。

{template_context}

■ 入力テキストメモ:
{input_text}
"""

        partsArr = [{"text": user_prompt}]

        if karte_images and isinstance(karte_images, list):
            for img_data in karte_images:
                if img_data:
                    partsArr.append({
                        "inline_data": {"mime_type": "image/jpeg", "data": img_data}
                    })

        if memo_images and isinstance(memo_images, list):
            for img_data in memo_images:
                if img_data:
                    partsArr.append({
                        "inline_data": {"mime_type": "image/jpeg", "data": img_data}
                    })

        if attached_files and isinstance(attached_files, list):
            for fileObj in attached_files:
                if isinstance(fileObj, dict) and fileObj.get("data"):
                    partsArr.append({
                        "inline_data": {
                            "mime_type": fileObj.get("mimeType", "application/octet-stream"),
                            "data": fileObj.get("data")
                        }
                    })

        model = genai.GenerativeModel(
            model_name='gemini-3.6-flash',
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        response = model.generate_content(
            partsArr,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=SoapResponse,
                temperature=0.1,
                max_output_tokens=2048
            )
        )

        if not response.text:
            raise HTTPException(status_code=500, detail="Failed to generate response from Gemini API.")

        # AIの出力テキストを安全にクリーニングしてパース
        raw_text = response.text.strip()
        raw_text = re.sub(r'^```json\s*', '', raw_text)
        raw_text = re.sub(r'^```\s*', '', raw_text)
        raw_text = re.sub(r'\s*```$', '', raw_text)

        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            def extract_field(field_name):
                match = re.search(rf'"{field_name}"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', raw_text, re.DOTALL)
                return match.group(1).encode().decode('unicode-escape') if match else ""

            result = {
                "progress": extract_field("progress"),
                "notice": extract_field("notice"),
                "s": extract_field("s"),
                "o": extract_field("o"),
                "a": extract_field("a"),
                "p": extract_field("p")
            }
        
        return SoapResponse(
            progress=result.get("progress", ""),
            notice=result.get("notice", ""),
            s=result.get("s", ""),
            o=result.get("o", ""),
            a=result.get("a", ""),
            p=result.get("p", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "gemini_api_key_configured": bool(GEMINI_API_KEY),
        "static_dir_exists": STATIC_DIR.exists(),
        "index_html_exists": (STATIC_DIR / "index.html").exists()
    }

@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail=f"index.html not found at {index_file}")
    return FileResponse(str(index_file), media_type="text/html")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")