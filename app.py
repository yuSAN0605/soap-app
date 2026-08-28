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
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# バリデーションエラーが起きた場合にログへ詳細を出力
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

class SoapResponse(BaseModel):
    progress: str = ""
    notice: str = ""
    s: str = ""
    o: str = ""
    a: str = ""
    p: str = ""

@app.post("/api/generate-soap")
async def generate_soap(request: Request):
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Gemini API Key is not configured."
            )

        # 生のJSONボディを辞書として安全に取得
        body = await request.json()
        input_text = body.get("inputText", "")
        karte_image = body.get("karteImage")
        memo_image = body.get("memoImage")
        attached_files = body.get("attachedFiles", [])

        if not input_text and not karte_image and not memo_image and not attached_files:
            raise HTTPException(
                status_code=400,
                detail="At least one input (text, image, or file) must be provided."
            )

        # 入力テキストからの構造化テンプレート解析処理
        template_context = ""
        if "S (Subjective)" in input_text or "O (Objective)" in input_text or "A (Assessment)" in input_text:
            sub_match = re.search(r'S \(Subjective\)([\s\S]*?)(?=O \(Objective\)|$)', input_text)
            obj_match = re.search(r'O \(Objective\)([\s\S]*?)(?=A \(Assessment\)|$)', input_text)
            ass_match = re.search(r'A \(Assessment\)([\s\S]*?)$', input_text)

            parsed_s = sub_match.group(1).strip() if sub_match else ""
            parsed_o = obj_match.group(1).strip() if obj_match else ""
            parsed_a = ass_match.group(1).strip() if ass_match else ""

            template_context = f"""【検出された構造化テンプレート情報】
主訴情報: {parsed_s[:200]}...
所見情報: {parsed_o[:200]}...
評価情報: {parsed_a[:200]}...

これらの構造化データを優先的に参照して、以下の指示に従ってください。
"""

        prompt_text = f"""あなたは理学療法士向けのカルテ記録生成AIです。入力された情報（評価テンプレート項目、院内カルテ画像、臨床メモ画像、その他ファイル、テキストメモ）を総合的に解析し、指定条件を厳格に守ってJSONオブジェクト形式で出力してください。

{template_context}

■ 情報の優先度ルール（矛盾がある場合）:
1. 院内カルテ画像（最も信頼度が高い医療記録）
2. テンプレート入力内容（構造化データ）
3. 臨床メモ画像
4. フリーテキスト入力

■ 画像解析の重点参照ガイドライン:
【院内カルテ画像から優先的に読み取る項目】
- 経過（現病歴・検査結果）
- 画像所見（X線・MRI等）
- 注意点（既往歴・体重・仕事）
- A（評価・診断的考察）

【臨床メモ画像から優先的に読み取る項目】
- O（客観的所見：ROM, MMT, 触診, 誘発テスト結果等）
- A（臨床評価・病態考察）

■ SOAP各項目の厳格な定義（重複・誤混入防止）:

【s（S）】※純粋な患者の発言・主訴・要望のみを記載してください
- 患者自身の生の声、症状の訴え、治療に対する希望や目標（ニード）のみを記載してください。
- 鍵カッコ「 」を用いて患者の発言として整理してください。
- ❌ **絶対に入れないでください**:
  - 「現病歴・症状」という見出しや、時系列の説明文章（→ これらは【progress（＊経過）】にのみ記載）
  - 疼痛スケール数値（→ これらは評価データのため【o（O）】にのみ記載）

【o（O）】※客観的測定数値・検査所見・評価データ
- 理学療法士が測定・観察した数値・所見のみを記載してください（主観的な推測は除外）
- ROM（可動域度数・制限因子）
- MMT（徒手筋力検査）
- 誘発テスト（陽性/陰性、誘発部位）
- 触診（圧痛点・筋緊張）
- 疼痛スケール評価は必ず「NRS」表記を用いて記載してください（例: NRS: 安静時 2/10, 動作時 5/10。「NPRS」表記は不可）。

【a（A）】※評価・病態解釈
- SとOの所見から導き出される推定病態・解釈・鑑別理由を記載

【p（P）】※治療計画
＊以下の項目で記載してください。
  #1 関節可動域訓練
  #2 筋力強化訓練
  #3 バランス訓練
  #4 自主トレーニング指導

■ 誤混入を防ぐための境界例（厳守してください）:
[悪い例]
s: 「腰が痛いと言っている。1ヶ月前から徐々に悪化。NRS 6/10。」（← 現病歴や数値評価が混入しているため不可）
o: 「前屈時に痛みを訴える」（← 主観的ニュアンス。評価数値ではないため不適切）

[正しい例]
s: 「痛みのせいで、朝かがんで顔を洗うのが一番つらい。早く普通に顔を洗えるようになりたい。」
o: 「腰椎可動域：屈曲 30°（制限因子：腰部疼痛）、NRS：動作時 6/10、安静時 0/10」
progress: 「【現病歴】1ヶ月前より徐々に腰痛が悪化。\\n【画像所見】X線：L4/5椎間板狭小化（他院受診時）」

■ 項目別記載ルール:

【progress（＊経過）】
- 「【現病歴】内容」の形式で必ず記載してください（例: 【現病歴】約1年前より両手のしびれを自覚...）。「現病歴：」や「年月日：」などの表記は絶対に用いないでください。必ず隅付き括弧で【現病歴】と記載してください。
- 現病歴（受傷機転、発症からの経過、増悪動作など）はこちらに集約して整理してください。
- 【画像所見】について、入力データ内に記載がある場合は**必ず直前で改行して別行とし**、以下のように記載してください：
  
  【現病歴】[現病歴の内容]
  【画像所見】X線：[所見内容](撮影日) MRI：[所見内容](撮影日)

  ※【画像所見】の直前は必ず改行 (\\n) を入れてください。
  ※撮影日がない場合は(撮影日)を省略し、所見内容のみを記載してください。
  ※画像所見自体の情報がなければ、【画像所見】の行ごと完全に無記載としてください。

【notice（＊注意点）】
- 入力情報内に記載がある場合のみ、以下の形式で記載：
  既往歴：
  体重：
  仕事：
- 入力情報内に特に記載がない項目は、項目名も含めて完全に無記載

■ 入力テキストメモ:
{input_text}

【出力形式（JSONのみ。他の説明や前置きは不要です）】
{{
  "progress": "【現病歴】内容\\n【画像所見】X線：...",
  "notice": "既往歴・体重・仕事（記載のない項目は完全に除外）",
  "s": "主訴：「患者の生の訴えや希望・目標のみ」（現病歴文章やNRSなどの数値は一切含めない）",
  "o": "客観的所見（ROM, MMT, 触診, 誘発テスト, NRS等の評価数値）",
  "a": "評価・考察（A：病態解釈・鑑別理由）",
  "p": "#1 関節可動域訓練 #2 筋力強化訓練 #3 バランス訓練 #4 自主トレーニング指導"
}}"""

        partsArr = [{"text": prompt_text}]

        if karte_image:
            partsArr.append({
                "inline_data": {"mime_type": "image/jpeg", "data": karte_image}
            })

        if memo_image:
            partsArr.append({
                "inline_data": {"mime_type": "image/jpeg", "data": memo_image}
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

        model = genai.GenerativeModel('gemini-3.6-flash')
        response = model.generate_content(partsArr)

        if not response.text:
            raise HTTPException(status_code=500, detail="Failed to generate response from Gemini API.")

        jsonMatch = re.search(r'\{[\s\S]*\}', response.text)
        if not jsonMatch:
            raise HTTPException(status_code=500, detail="Invalid JSON response from Gemini API.")

        result = json.loads(jsonMatch.group(0))
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