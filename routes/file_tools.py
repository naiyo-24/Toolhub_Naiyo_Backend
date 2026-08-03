from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
import io
import zipfile
import uuid
import os
import hashlib
import socket
from typing import List, Optional
from PIL import Image
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

try:
    import pillow_avif
except ImportError:
    pass

from pypdf import PdfReader, PdfWriter
import requests

router = APIRouter(prefix="/file-tools", tags=["File Tools"])

# Helper for in-memory file streaming
import urllib.parse

def stream_file(buffer, filename, media_type):
    buffer.seek(0)
    encoded_filename = urllib.parse.quote(filename)
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )

@router.post("/zip/extract")
async def extract_zip(file: UploadFile = File(...), target_file: Optional[str] = Form(None)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "File must be a ZIP archive.")
    
    try:
        content = await file.read()
        zip_buf = io.BytesIO(content)
        
        with zipfile.ZipFile(zip_buf, "r") as zip_ref:
            # If a specific file is requested, extract and return it
            if target_file:
                if target_file not in zip_ref.namelist():
                    raise ValueError(f"File '{target_file}' not found in ZIP.")
                
                extracted_data = zip_ref.read(target_file)
                out_buf = io.BytesIO(extracted_data)
                return stream_file(out_buf, target_file.split("/")[-1], "application/octet-stream")
            
            # Otherwise, just list the contents
            file_list = []
            for zip_info in zip_ref.infolist():
                if not zip_info.is_dir():
                    file_list.append({
                        "filename": zip_info.filename,
                        "size_bytes": zip_info.file_size
                    })
            return {"extracted_files": file_list, "count": len(file_list)}
    except Exception as e:
        raise HTTPException(400, f"Invalid ZIP file: {str(e)}")

@router.post("/zip/create")
async def create_zip(files: List[UploadFile] = File(...)):
    try:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zip_ref:
            for f in files:
                content = await f.read()
                zip_ref.writestr(f.filename, content)
                
        return stream_file(zip_buf, "archive.zip", "application/zip")
    except Exception as e:
        raise HTTPException(400, f"Failed to create ZIP: {str(e)}")

@router.post("/image/compress")
async def compress_image(file: UploadFile = File(...), quality: int = Form(50), target_size_kb: int | None = Form(None)):
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        
        # Convert to RGB if it's RGBA (JPEG doesn't support alpha)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
            
        if target_size_kb is not None and target_size_kb > 0:
            target_bytes = target_size_kb * 1024
            best_out = None
            low, high = 1, 95
            
            # Images are cheap to compress, binary search works well here
            for _ in range(7):
                if low > high:
                    break
                mid = (low + high) // 2
                temp_buf = io.BytesIO()
                img.save(temp_buf, format="JPEG", optimize=True, quality=mid)
                size = temp_buf.getbuffer().nbytes
                best_out = temp_buf
                
                if size <= target_bytes:
                    low = mid + 1
                else:
                    high = mid - 1
                    
            out_buf = best_out if best_out else io.BytesIO()
            if out_buf.getbuffer().nbytes == 0:
                img.save(out_buf, format="JPEG", optimize=True, quality=1)
        else:
            out_buf = io.BytesIO()
            img.save(out_buf, format="JPEG", optimize=True, quality=quality)
        
        if out_buf.getbuffer().nbytes >= len(content):
            # If compression makes it larger, return original
            out_buf = io.BytesIO(content)
            return stream_file(out_buf, file.filename, file.content_type)
            
        return stream_file(out_buf, f"compressed_{file.filename.split('.')[0]}.jpg", "image/jpeg")
    except Exception as e:
        raise HTTPException(400, f"Failed to compress image: {str(e)}")

@router.post("/image-convert")
async def image_convert(file: UploadFile = File(...), target_format: str = Form(...)):
    try:
        content = await file.read()
        filename = file.filename.lower()
        target_format = target_format.lower()
        
        format_map = {
            "jpg": "JPEG",
            "jpeg": "JPEG",
            "png": "PNG",
            "webp": "WEBP",
            "bmp": "BMP",
            "tiff": "TIFF",
            "gif": "GIF"
        }
        
        if target_format not in format_map:
            raise HTTPException(400, f"Unsupported target format: {target_format}")
            
        pil_format = format_map[target_format]
        out_buf = io.BytesIO()
        
        if filename.endswith(".svg"):
            try:
                import cairosvg
            except ImportError:
                raise HTTPException(400, "SVG conversion not supported on this server.")
            
            png_data = cairosvg.svg2png(bytestring=content)
            if target_format == "png":
                out_buf.write(png_data)
            else:
                img = Image.open(io.BytesIO(png_data))
                if img.mode in ("RGBA", "P") and pil_format == "JPEG":
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = bg
                img.save(out_buf, format=pil_format)
        else:
            img = Image.open(io.BytesIO(content))
            
            if img.mode in ("RGBA", "P", "LA") and pil_format == "JPEG":
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode in ("RGBA", "LA"):
                    bg.paste(img, mask=img.split()[-1])
                else:
                    bg.paste(img)
                img = bg
            elif img.mode != "RGB" and pil_format == "JPEG":
                img = img.convert("RGB")
                
            save_kwargs = {}
            if pil_format == "JPEG":
                save_kwargs["quality"] = 90
            elif pil_format == "WEBP":
                save_kwargs["quality"] = 90
                
            img.save(out_buf, format=pil_format, **save_kwargs)
            
        out_buf.seek(0)
        ext = target_format
        if target_format == "jpeg":
            ext = "jpg"
            
        base_name = file.filename.rsplit(".", 1)[0]
        mime_type = f"image/{target_format}"
        if target_format == "jpg":
            mime_type = "image/jpeg"
            
        return stream_file(out_buf, f"{base_name}.{ext}", mime_type)
    except Exception as e:
        raise HTTPException(400, f"Conversion failed: {str(e)}")

import asyncio

@router.post("/pdf/compress")
async def compress_pdf(file: UploadFile = File(...), quality: int = Form(50), target_size_kb: int | None = Form(None), extreme_mode: bool = Form(False)):
    try:
        content = await file.read()
        
        def compress_with_quality(q, file_content, extreme):
            if extreme:
                import fitz
                doc = fitz.open(stream=file_content, filetype="pdf")
                new_doc = fitz.open()
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    # Lower DPI for extreme compression (72 DPI)
                    zoom = 1.0
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    
                    # Convert to PIL to save as heavily compressed JPEG
                    img_data = pix.tobytes("ppm")
                    pil_img = Image.open(io.BytesIO(img_data))
                    
                    temp_buf = io.BytesIO()
                    pil_img.save(temp_buf, format="JPEG", optimize=True, quality=q)
                    temp_buf.seek(0)
                    
                    rect = page.rect
                    new_page = new_doc.new_page(width=rect.width, height=rect.height)
                    new_page.insert_image(rect, stream=temp_buf.read())
                    
                out = io.BytesIO()
                new_doc.save(out, garbage=4, deflate=True)
                out.seek(0)
                return out
            else:
                reader = PdfReader(io.BytesIO(file_content))
                writer = PdfWriter(clone_from=reader)
                
                for page in writer.pages:
                    page.compress_content_streams()
                    for img in page.images:
                        try:
                            pil_img = img.image
                            if pil_img.mode in ("RGBA", "P", "LA"):
                                pil_img = pil_img.convert("RGB")
                                
                            # Downscale very large images to guarantee size reduction
                            max_dim = 2000 if q > 75 else (1200 if q > 40 else 800)
                            if pil_img.width > max_dim or pil_img.height > max_dim:
                                pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                                
                            img.replace(pil_img, quality=q)
                        except Exception as e:
                            print(f"Failed to compress image: {e}")
                            pass
                
                out = io.BytesIO()
                writer.write(out)
                out.seek(0)
                return out

        if target_size_kb is not None and target_size_kb > 0:
            target_bytes = target_size_kb * 1024
            original_size = len(content)
            if target_bytes < original_size:
                ratio = target_bytes / original_size
                quality = max(1, int(100 * ratio))
            else:
                quality = 100
                
        # Run CPU-bound compression in a separate thread
        out_buf = await asyncio.to_thread(compress_with_quality, quality, content, extreme_mode)
        
        if not extreme_mode and out_buf.getbuffer().nbytes >= len(content):
            out_buf = io.BytesIO(content)
            
        return stream_file(out_buf, f"compressed_{file.filename}", "application/pdf")
    except Exception as e:
        raise HTTPException(400, f"Failed to compress PDF: {str(e)}")

@router.post("/pdf/protect")
async def protect_pdf(file: UploadFile = File(...), password: str = Form(...)):
    try:
        content = await file.read()
        reader = PdfReader(io.BytesIO(content))
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
            
        writer.encrypt(password)
        
        out_buf = io.BytesIO()
        writer.write(out_buf)
        return stream_file(out_buf, f"protected_{file.filename}", "application/pdf")
    except Exception as e:
        raise HTTPException(400, f"Failed to protect PDF: {str(e)}")

@router.post("/pdf/merge")
async def merge_pdf(files: List[UploadFile] = File(...)):
    try:
        writer = PdfWriter()
        
        for f in files:
            content = await f.read()
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                writer.add_page(page)
                
        out_buf = io.BytesIO()
        writer.write(out_buf)
        return stream_file(out_buf, "merged_document.pdf", "application/pdf")
    except Exception as e:
        raise HTTPException(400, f"Failed to merge PDFs: {str(e)}")

import pytesseract

@router.post("/ocr")
async def extract_text_ocr(file: UploadFile = File(...)):
    try:
        content = await file.read()
        
        # Convert any image format to RGB for Tesseract
        img = Image.open(io.BytesIO(content))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Run Tesseract locally
        extracted_text = pytesseract.image_to_string(img)
        
        if not extracted_text.strip():
            raise Exception("No text could be extracted or image is unreadable.")
            
        return {"extracted_text": extracted_text.strip()}
    except Exception as e:
        raise HTTPException(400, f"OCR Failed: {str(e)}")

easyocr_reader = None

@router.post("/ocr/handwriting")
async def extract_handwriting(file: UploadFile = File(...)):
    global easyocr_reader
    try:
        import easyocr
        import numpy as np
        
        if easyocr_reader is None:
            # Initialize the model only once to save memory and time
            easyocr_reader = easyocr.Reader(['en'])
            
        content = await file.read()
        
        img = Image.open(io.BytesIO(content))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Convert PIL image to numpy array for EasyOCR
        img_np = np.array(img)
        
        # detail=0 returns just the text list
        result = easyocr_reader.readtext(img_np, detail=0, paragraph=True)
        extracted_text = "\n".join(result)
        
        if not extracted_text.strip():
            raise Exception("No handwriting could be extracted or image is unreadable.")
            
        return {"extracted_text": extracted_text.strip()}
    except Exception as e:
        raise HTTPException(400, f"Handwriting OCR Failed: {str(e)}")

@router.post("/analyze/duplicates")
async def find_duplicates(files: List[UploadFile] = File(...)):
    try:
        hashes = {}
        duplicates = []
        
        for f in files:
            content = await f.read()
            file_hash = hashlib.md5(content).hexdigest()
            if file_hash in hashes:
                duplicates.append({
                    "duplicate_file": f.filename,
                    "original_file": hashes[file_hash]
                })
            else:
                hashes[file_hash] = f.filename
                
        return {
            "total_files": len(files),
            "duplicates_found": len(duplicates),
            "duplicates": duplicates
        }
    except Exception as e:
        raise HTTPException(400, f"Analysis failed: {str(e)}")

@router.post("/analyze/storage")
async def analyze_storage(files: List[UploadFile] = File(...)):
    try:
        total_size = 0
        file_types = {}
        
        for f in files:
            content = await f.read()
            size = len(content)
            total_size += size
            
            ext = f.filename.split(".")[-1].lower() if "." in f.filename else "unknown"
            if ext not in file_types:
                file_types[ext] = {"count": 0, "size_bytes": 0}
            
            file_types[ext]["count"] += 1
            file_types[ext]["size_bytes"] += size
            
        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "breakdown": file_types
        }
    except Exception as e:
        raise HTTPException(400, f"Analysis failed: {str(e)}")

@router.post("/share/upload")
async def share_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        
        file_id = str(uuid.uuid4())
        # keep original extension
        ext = file.filename.split(".")[-1] if "." in file.filename else ""
        save_filename = f"{file_id}.{ext}" if ext else file_id
        
        save_path = os.path.join("uploads", save_filename)
        
        with open(save_path, "wb") as f:
            f.write(content)
            
        # Get the actual local network IP so it can be opened on other devices
        def get_local_ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return '127.0.0.1'
                
        local_ip = get_local_ip()
        full_url = f"http://{local_ip}:8000/uploads/{save_filename}"
        
        return {
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": file.filename,
            "download_path": f"/uploads/{save_filename}", # Original path for mobile app
            "absolute_url": full_url # New full URL for web app
        }
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")
