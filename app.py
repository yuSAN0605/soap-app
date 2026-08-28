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

        # 生のJSONボディを辞書として安全に取得（型チェックによる422を完全に防ぐ）
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

        promptText = """あなたは理学療法士向けのカルテ記録生成AIです。入力された情報を解析し、JSONオブジェクト形式で出力してください。

■ 出力形式（JSONのみ）:
{
  "progress": "【現病歴】内容\\n【画像所見】X線：...",
  "notice": "既往歴・体重・仕事",
  "s": "主訴（患者の生の訴えのみ）",
  "o": "客観的所見（ROM, MMT, NRS等）",
  "a": "評価・考察",
  "p": "#1 関節可動域訓練 #2 筋力強化訓練 #3 バランス訓練 #4 自主トレーニング指導"
}"""

        partsArr = [{"text": promptText}]

        if input_text:
            partsArr.append({"text": f"【入力テキスト】\n{input_text}"})

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

        model = genai.GenerativeModel('gemini-1.5-flash')
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