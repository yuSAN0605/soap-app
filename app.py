import os
import json
import re
import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

class GenerateSoapRequest(BaseModel):
    inputText: str = ""
    karteImage: Optional[str] = None
    karteImages: Optional[List[str]] = Field(default_factory=list)
    memoImage: Optional[str] = None
    memoImages: Optional[List[str]] = Field(default_factory=list)
    attachedFiles: List[dict] = Field(default_factory=list)

class SoapResponse(BaseModel):
    progress: str = ""
    notice: str = ""
    s: str = ""
    o: str = ""
    a: str = ""
    p: str = ""

# 3️⃣ 最適化：コンパイル済み正規表現の事前定義（毎回コンパイルするコストを削減）
CLEAN_MARKDOWN_REGEX = re.compile(r'^```(?:json)?\s*|\s*```$', re.MULTILINE)
EXTRACT_JSON_REGEX = re.compile(r'\{.*\}', re.DOTALL)

@app.post("/api/generate-soap", response_model=SoapResponse)
async def generate_soap(request: GenerateSoapRequest):
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="Gemini API Key is not configured.")
        
        input_text = request.inputText or ""
        
        karte_images = request.karteImages or []
        if not karte_images and request.karteImage:
            karte_images = [request.karteImage]

        memo_images = request.memoImages or []
        if not memo_images and request.memoImage:
            memo_images = [request.memoImage]

        attached_files = request.attachedFiles or []
        
        if not input_text and not karte_images and not memo_images and not attached_files:
            raise HTTPException(status_code=400, detail="At least one input must be provided.")

        # 2️⃣ 最適化：テンプレート情報の事前チェック（なければ正規表現を実行せず即スキップ）
        template_context = ""
        if any(keyword in input_text for keyword in ["S (Subjective)", "O (Objective)", "A (Assessment)"]):
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
"""

        promptText = f"""あなたは理学療法士向けの専門カルテ（SOAP）記録生成AIです。提供された情報（テキスト、画像、ファイル）を分析し、理学療法記録として正確かつ厳格に構造化したJSONデータを作成してください。

{template_context}

■ 情報の優先順位（情報に矛盾がある場合）:
1. 院内カルテ画像（最優先・公式記録）
2. 構造化テンプレート入力
3. 臨床メモ画像
4. フリーテキスト入力

■ 各項目の厳格な記載ルール:
【progress（経過）】
- 必ず「【現病歴】」で始めてください。「現病歴：」などの表記は不可。
- 画像所見が存在する場合は必ず直前で改行し、以下のように別行で記載：
  【現病歴】[現病歴の内容]
  【画像所見】
  X線：[所見内容]（撮影日）
  MRI：[所見内容]（撮影日）
- ない場合は【画像所見】の行を出力しない。

【notice（注意点）】
- 入力情報内に存在する項目のみ「既往歴：」「体重：」「仕事：」の形式で記載。ない場合は空文字。

【s（Subjective）】
- 患者自身の言葉(疼痛部位・疼痛動作・疼痛時間・疼痛の性質・疼痛範囲・疼痛寛解動作など)のみ。
- 鍵カッコ「 」を使用。

【o（Objective）】
- ROM、MMT、圧痛(Td)、疼痛誘発テスト・疼痛寛解テスト、立位（CSLの左右差・骨盤前方回旋側）・動作観察(片足立ち骨盤スウェイ側)などのデータを記載。
※参考: CSL（Center Sacral Line）評価：仙骨中央からの垂線（CSL）に対する第7頸椎の位置や、体幹の横へのシフト（偏位）右シフト左シフトと表現
蹴り出し側または踏み出し側の予測：
特徴：踏みだし側は反対の脚より接地の衝撃が大きくなり、特に足や膝に痛みがでやすい。骨盤の前への回旋量が大きくなるため、腰への負担が大きくなりやすい。
蹴り出し側は脚が後ろにある時間が長いため、股関節・膝関節・足部の可動性がより求められ、各関節に負担が大きくなりやすい。
骨盤前方回旋テスト：左右差がある場合はそちらが踏み出し側になりやすい。
骨盤スウェイテスト：側方swayが大きい側が股関節内転位傾向・能動制御ができていない（受動支持）

【a（Assessment）】
- SおよびOのデータ（疼痛動作、ROM制限、圧痛、テスト結果など）に基づき、なぜその症状や障害が起きているのかの病態解釈、機能障害の根拠に記述してください。

【p（Plan）】
- 以下の項目だけを必ず転記：
  #1 関節可動域訓練
  #2 筋力強化訓練
  #3 バランス訓練
  #4 自主トレーニング指導

【重要】以下のJSON形式で**必ず**レスポンスしてください。他の説明やマークダウンコードブロック（```json など）は一切含めず、純粋なJSON文字列のみを出力してください。

{{
  "progress": "...",
  "notice": "...",
  "s": "...",
  "o": "...",
  "a": "...",
  "p": "#1 関節可動域訓練 #2 筋力強化訓練 #3 バランス訓練 #4 自主トレーニング指導"
}}"""

        partsArr = [{"text": promptText}]
        
        if input_text:
            partsArr.append({"text": f"■ 入力テキストメモ:\n{input_text}"})
        
        for img_data in karte_images:
            if img_data:
                partsArr.append({
                    "inline_data": {"mime_type": "image/jpeg", "data": img_data}
                })
        
        for img_data in memo_images:
            if img_data:
                partsArr.append({
                    "inline_data": {"mime_type": "image/jpeg", "data": img_data}
                })
        
        for fileObj in attached_files:
            if isinstance(fileObj, dict) and fileObj.get("data"):
                partsArr.append({
                    "inline_data": {
                        "mime_type": fileObj.get("mimeType", "application/octet-stream"),
                        "data": fileObj.get("data")
                    }
                })
        
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        # 1️⃣ 最適化：非同期スレッド実行（サーバーのブロッキングを防ぎ、複数リクエストに対応）
        def _call_gemini():
            return model.generate_content(
                partsArr,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=4096
                )
            )

        response = await asyncio.to_thread(_call_gemini)
        
        raw_text = response.text.strip() if response.text else ""
        
        if not raw_text:
            raise ValueError("Empty response from Gemini API")
        
        # 3️⃣ 最適化：事前コンパイルされた正規表現でマークダウンを高速除去
        raw_text = CLEAN_MARKDOWN_REGEX.sub('', raw_text).strip()
        
        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError:
            # 3️⃣ 最適化：事前コンパイルされた抽出正規表現を使用
            match = EXTRACT_JSON_REGEX.search(raw_text)
            if match:
                try:
                    result = json.loads(match.group(0))
                except json.JSONDecodeError:
                    result = repair_json(raw_text)
            else:
                result = repair_json(raw_text)
        
        # ✅ ここで確実に p_text を定義する
        p_text = result.get("p", "")
        if not p_text or not p_text.strip():
            p_text = "#1 関節可動域訓練 #2 筋力強化訓練 #3 バランス訓練 #4 自主トレーニング指導"

        return SoapResponse(
            progress=result.get("progress", ""),
            notice=result.get("notice", ""),
            s=result.get("s", ""),
            o=result.get("o", ""),
            a=result.get("a", ""),
            p=p_text
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

def repair_json(broken_json: str) -> dict:
    for suffix in ["}", "}}", "\"}", "\"}}]"]:
        try:
            return json.loads(broken_json + suffix)
        except:
            pass
    return {
        "progress": "",
        "notice": "",
        "s": "",
        "o": "",
        "a": "",
        "p": "#1 関節可動域訓練 #2 筋力強化訓練 #3 バランス訓練 #4 自主トレーニング指導"
    }

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