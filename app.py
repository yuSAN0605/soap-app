import os
import json
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ✅ 絶対パスを指定
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

class GenerateSoapRequest(BaseModel):
    inputText: str
    karteImage: str = None
    memoImage: str = None
    attachedFiles: list = []

class SoapResponse(BaseModel):
    progress: str
    notice: str
    s: str
    o: str
    a: str
    p: str

@app.post("/api/generate-soap", response_model=SoapResponse)
async def generate_soap(request: GenerateSoapRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key is not configured.")
    
    if not request.inputText and not request.karteImage and not request.memoImage and not request.attachedFiles:
        raise HTTPException(status_code=400, detail="At least one input must be provided.")
    
    try:
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
        
        if request.inputText:
            partsArr.append({"text": f"【入力テキスト】\n{request.inputText}"})
        
        if request.karteImage:
            partsArr.append({
                "inline_data": {"mime_type": "image/jpeg", "data": request.karteImage}
            })
        
        if request.memoImage:
            partsArr.append({
                "inline_data": {"mime_type": "image/jpeg", "data": request.memoImage}
            })
        
        if request.attachedFiles:
            for fileObj in request.attachedFiles:
                partsArr.append({
                    "inline_data": {
                        "mime_type": fileObj.get("mimeType", "application/octet-stream"),
                        "data": fileObj.get("data")
                    }
                })
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(partsArr)
        
        if not response.text:
            raise HTTPException(status_code=500, detail="Failed to generate response.")
        
        jsonMatch = re.search(r'\{[\s\S]*\}', response.text)
        if not jsonMatch:
            raise HTTPException(status_code=500, detail="Invalid JSON response.")
        
        result = json.loads(jsonMatch.group(0))
        return SoapResponse(
            progress=result.get("progress", ""),
            notice=result.get("notice", ""),
            s=result.get("s", ""),
            o=result.get("o", ""),
            a=result.get("a", ""),
            p=result.get("p", "")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ✅ 絶対パス使用
@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail=f"index.html not found at {index_file}")
    return FileResponse(str(index_file), media_type="text/html")

# ✅ 絶対パス使用
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "gemini_api_key_configured": bool(GEMINI_API_KEY),
        "static_dir_exists": STATIC_DIR.exists(),
        "index_html_exists": (STATIC_DIR / "index.html").exists()
    }