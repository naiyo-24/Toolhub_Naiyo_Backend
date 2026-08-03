from fastapi import APIRouter, HTTPException, UploadFile, File, Form
import requests
import os
import mimetypes
import yt_dlp
import uuid
from schemas.ai_tools import *

router = APIRouter(prefix="/ai-tools", tags=["AI Tools"])

import time

def upload_to_gemini(file_bytes: bytes, filename: str, mime_type: str) -> str:
    config = dotenv_values(".env")
    api_key = config.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key is not configured")
        
    start_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}"
    headers = {
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(len(file_bytes)),
        "X-Goog-Upload-Header-Content-Type": mime_type,
        "Content-Type": "application/json"
    }
    res = requests.post(start_url, headers=headers, json={"file": {"display_name": filename}})
    if res.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Failed to start Gemini upload: {res.text}")
        
    upload_url = res.headers.get("X-Goog-Upload-URL")
    if not upload_url:
        raise HTTPException(status_code=500, detail="Gemini did not return an upload URL")
        
    upload_res = requests.post(upload_url, headers={
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "upload, finalize",
        "X-Goog-Upload-Offset": "0"
    }, data=file_bytes)
    
    if upload_res.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Failed to upload media to Gemini: {upload_res.text}")
        
    file_info = upload_res.json()["file"]
    file_name = file_info["name"]
    file_uri = file_info["uri"]
    
    # Wait for the file to be processed by Google's media pipeline
    for _ in range(30):
        get_res = requests.get(f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={api_key}")
        if get_res.status_code == 200:
            state = get_res.json().get("state")
            if state == "ACTIVE":
                return file_uri
            elif state == "FAILED":
                raise HTTPException(status_code=500, detail="Gemini failed to process the media file.")
        time.sleep(2)
        
    raise HTTPException(status_code=500, detail="Timeout: Gemini took too long to process the media.")

from dotenv import dotenv_values

def generate_ai_response(prompt: str, file_uri: str = None, json_mode: bool = False) -> str:
    config = dotenv_values(".env")
    api_key = config.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key is not configured")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    parts = []
    if file_uri:
        parts.append({"fileData": {"fileUri": file_uri}})
    parts.append({"text": prompt})
    
    payload = {
        "contents": [{"parts": parts}]
    }
    
    if json_mode:
        payload["generationConfig"] = {"responseMimeType": "application/json"}
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 429:
        # Fallback Mock Response so testing can continue
        if json_mode:
            return '{"error": "AI Quota Exceeded (Mock Fallback Active)"}'
        else:
            return "Mock AI Response: You have exceeded your free tier Gemini quota. This is a mock response so you can keep testing your app without crashing."
            
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Gemini API Error: {response.text}")
        
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=500, detail="Failed to parse AI response")

@router.post("/meeting-summarizer")
async def summarize_meeting(file: UploadFile = File(None), transcript: str = Form(None), youtube_url: str = Form(None)):
    if not file and not transcript and not youtube_url:
        raise HTTPException(status_code=400, detail="You must provide either a media file, a text transcript, or a YouTube URL")
        
    prompt = "Summarize the following meeting. Provide key takeaways and action items."
    file_uri = None
    
    if youtube_url:
        # Fetch YouTube transcript instantly instead of downloading heavy video/audio
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from urllib.parse import urlparse, parse_qs
            
            def extract_video_id(url):
                parsed = urlparse(url)
                if parsed.hostname == 'youtu.be': return parsed.path[1:]
                if parsed.hostname in ('www.youtube.com', 'youtube.com'):
                    if parsed.path == '/watch': return parse_qs(parsed.query)['v'][0]
                    if parsed.path.startswith('/embed/'): return parsed.path.split('/')[2]
                    if parsed.path.startswith('/v/'): return parsed.path.split('/')[2]
                    if parsed.path.startswith('/shorts/'): return parsed.path.split('/')[2]
                    if parsed.path.startswith('/live/'): return parsed.path.split('/')[2]
                return None
                
            video_id = extract_video_id(youtube_url)
            if not video_id:
                raise ValueError("Invalid YouTube URL")
                
            api = YouTubeTranscriptApi()
            fetched = api.fetch(video_id)
            yt_text = " ".join([t.text for t in fetched])
            
            prompt += f"\n\nYouTube Video Transcript:\n{yt_text}"
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch YouTube transcript: {str(e)}")
            
        if transcript:
            prompt += f"\n\nAdditional Notes:\n{transcript}"
    elif file:
        file_bytes = await file.read()
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime_type)
        if transcript:
            prompt += f"\n\nAdditional Transcript/Notes:\n{transcript}"
    else:
        prompt += f"\n\nTranscript:\n{transcript}"
        
    text = generate_ai_response(prompt, file_uri=file_uri)
    return {"summary": text}

@router.post("/notes-generator")
async def generate_notes(file: UploadFile = File(None), topic: str = Form(None), context: str = Form(None)):
    if not file and not topic:
        raise HTTPException(status_code=400, detail="You must provide either a file or a topic")
        
    prompt = f"Create comprehensive, well-structured study notes"
    if topic:
        prompt += f" on the topic of {topic}"
    
    file_uri = None
    if file:
        file_bytes = await file.read()
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime_type)
        if context:
            prompt += f". Include the following context:\n\n{context}"
    else:
        ctx = f". Use the following context:\n\n{context}" if context else "."
        prompt += ctx
        
    text = generate_ai_response(prompt, file_uri=file_uri)
    return {"notes": text}

@router.post("/translator")
async def translate_text(file: UploadFile = File(None), text: str = Form(None), target_language: str = Form(...)):
    if not file and not text:
        raise HTTPException(status_code=400, detail="You must provide either a file or text to translate")
        
    prompt = f"Translate the following into {target_language}. Only return the translation."
    file_uri = None
    
    if file:
        file_bytes = await file.read()
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime_type)
        if text:
            prompt += f"\n\nAdditional text:\n{text}"
    else:
        prompt += f"\n\nText:\n{text}"
        
    translation = generate_ai_response(prompt, file_uri=file_uri)
    return {"translation": translation}

@router.post("/email-writer")
async def write_email(file: UploadFile = File(None), context: str = Form(None), tone: str = Form("Professional"), recipient: str = Form(None)):
    if not file and not context:
        raise HTTPException(status_code=400, detail="You must provide either a file or context for the email")
        
    rec = f" for {recipient}" if recipient else ""
    prompt = f"Write a {tone.lower()} email{rec} regarding the provided context."
    file_uri = None
    
    if file:
        file_bytes = await file.read()
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime_type)
        if context:
            prompt += f"\n\nAdditional context:\n{context}"
    else:
        prompt += f"\n\nContext:\n{context}"
        
    text = generate_ai_response(prompt, file_uri=file_uri)
    return {"email_draft": text}

@router.post("/grammar-checker")
async def check_grammar(file: UploadFile = File(None), text: str = Form(None)):
    if not file and not text:
        raise HTTPException(status_code=400, detail="You must provide either a file or text to check")
        
    prompt = "Fix all grammatical and spelling errors in the following text. Only return the corrected text without any extra explanation."
    file_uri = None
    
    if file:
        file_bytes = await file.read()
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime_type)
        if text:
            prompt += f"\n\nAdditional text:\n{text}"
    else:
        prompt += f"\n\nText:\n{text}"
        
    corrected = generate_ai_response(prompt, file_uri=file_uri)
    return {"corrected_text": corrected}

@router.post("/resume-reviewer")
async def review_resume(file: UploadFile = File(None), resume_text: str = Form(None)):
    if not file and not resume_text:
        raise HTTPException(status_code=400, detail="You must provide either a PDF file or resume text")
        
    prompt = "Act as an expert recruiter. Review the provided resume and provide 3 strong bullet points for improvements, and an overall rating out of 10."
    file_uri = None
    
    if file:
        file_bytes = await file.read()
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/pdf"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime_type)
        if resume_text:
            prompt += f"\n\nAdditional Notes/Text:\n{resume_text}"
    else:
        prompt += f"\n\nResume Text:\n{resume_text}"
        
    text = generate_ai_response(prompt, file_uri=file_uri)
    return {"review": text}

@router.post("/interview-prep")
async def prepare_interview(file: UploadFile = File(None), job_role: str = Form(None), experience_level: str = Form("Entry-level")):
    if not file and not job_role:
        raise HTTPException(status_code=400, detail="You must provide either a job description file or a job role")
        
    prompt = f"Generate 5 common interview questions and ideal answer tips for an {experience_level} position."
    file_uri = None
    
    if file:
        file_bytes = await file.read()
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime_type)
        if job_role:
            prompt += f" The role is {job_role}."
    else:
        prompt += f" The role is {job_role}."
        
    text = generate_ai_response(prompt, file_uri=file_uri)
    return {"prep_guide": text}

@router.post("/homework-helper")
async def homework_help(file: UploadFile = File(None), question: str = Form(None), subject: str = Form(None)):
    if not file and not question:
        raise HTTPException(status_code=400, detail="You must provide either an image/file of the homework or a text question")
        
    sub = f" in the subject of {subject}" if subject else ""
    prompt = f"Provide a clear, educational, step-by-step explanation to solve this question{sub}."
    file_uri = None
    
    if file:
        file_bytes = await file.read()
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime_type)
        if question:
            prompt += f"\n\nQuestion text:\n{question}"
    else:
        prompt += f"\n\nQuestion:\n{question}"
        
    text = generate_ai_response(prompt, file_uri=file_uri)
    return {"explanation": text}

@router.post("/code-explainer")
async def explain_code(file: UploadFile = File(None), code: str = Form(None), language: str = Form(None)):
    if not file and not code:
        raise HTTPException(status_code=400, detail="You must provide either a code file or raw code text")
        
    lang = f" ({language})" if language else ""
    prompt = f"Explain what the following code{lang} does in simple terms."
    file_uri = None
    
    if file:
        file_bytes = await file.read()
        mime_type = mimetypes.guess_type(file.filename)[0] or "text/plain"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime_type)
        if code:
            prompt += f"\n\nAdditional Code snippet:\n{code}"
    else:
        prompt += f"\n\nCode:\n{code}"
        
    text = generate_ai_response(prompt, file_uri=file_uri)
    return {"explanation": text}

@router.post("/prompt-generator")
async def generate_prompt(file: UploadFile = File(None), idea: str = Form(None)):
    if not file and not idea:
        raise HTTPException(status_code=400, detail="You must provide either a file or a text idea")
        
    prompt = "Take the following basic idea and turn it into a highly detailed, professional prompt that can be fed into an AI system (like ChatGPT or Midjourney) to get the best result."
    file_uri = None
    
    if file:
        file_bytes = await file.read()
        mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        file_uri = upload_to_gemini(file_bytes, file.filename, mime_type)
        if idea:
            prompt += f"\n\nAdditional Idea text:\n{idea}"
    else:
        prompt += f"\n\nIdea:\n{idea}"
        
    text = generate_ai_response(prompt, file_uri=file_uri)
    return {"advanced_prompt": text}
