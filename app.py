import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# ✅ CORS ミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Gemini API キー設定（環境変数から取得）
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ============================================
# リクエスト/レスポンスモデル
# ============================================
class GenerateRequest(BaseModel):
    contents: list

class GenerateResponse(BaseModel):
    text: str

# ============================================
# API エンドポイント
# ============================================

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_soap(request: GenerateRequest):
    """
    Gemini APIを使用してコンテンツを生成するエンドポイント
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="Gemini API Key is not configured."
        )
    
    if not request.contents:
        raise HTTPException(
            status_code=400,
            detail="contents field cannot be empty."
        )
    
    try:
        # ✅ モデル指定：実在する最新モデルを使用
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(request.contents)
        
        if not response.text:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate response from Gemini API."
            )
        
        return GenerateResponse(text=response.text)
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating content: {str(e)}"
        )

# ============================================
# 静的ファイル配信（index.html など）
# ============================================

@app.get("/")
async def serve_index():
    """
    ルートパス（/）にアクセスした際、直下の index.html を返す
    """
    return FileResponse("index.html", media_type="text/html")

# ============================================
# ヘルスチェック
# ============================================

@app.get("/health")
async def health_check():
    """
    デプロイ環境のヘルスチェック用エンドポイント
    """
    return {
        "status": "ok",
        "gemini_api_key_configured": bool(GEMINI_API_KEY)
    }