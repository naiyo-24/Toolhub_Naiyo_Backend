from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Response
import mimetypes
from schemas.docuforge import ResumeBuilderRequest, IDCardRequest
from routes.ai_tools import generate_ai_response, upload_to_gemini
from routes.student_tools import clean_json_string
import json

router = APIRouter()

@router.post("/resume-builder")
def resume_builder(req: ResumeBuilderRequest):
    prompt = f"Generate a professional ATS-friendly resume for {req.full_name} ({req.email}, {req.phone}). Target role: {req.target_role}. Education: {req.education}. Experience: {req.experience}. Skills: {', '.join(req.skills)}. Return a JSON object with keys: 'summary', 'experience_bullets', 'education_bullets', 'skills'."
    raw_json = clean_json_string(generate_ai_response(prompt, json_mode=True))
    try:
        return {"resume": json.loads(raw_json)}
    except json.JSONDecodeError:
        return {"resume": raw_json}

import re
from pypdf import PdfReader
from io import BytesIO

@router.post("/ats-checker")
async def ats_checker(resume: UploadFile = File(...), job_description: str = Form(...)):
    try:
        reader = PdfReader(BytesIO(await resume.read()))
        resume_text = " ".join([page.extract_text() or "" for page in reader.pages]).lower()
        
        # Heuristic to fix PDF kerning issues (where letters are separated by spaces)
        # e.g., "h t m l   d e v e l o p e r"
        words_split = resume_text.split()
        if words_split:
            single_char_count = sum(1 for w in words_split if len(w) == 1 and w.isalpha())
            if single_char_count / len(words_split) > 0.4:
                # Replace double spaces or newlines with a placeholder
                resume_text = resume_text.replace("  ", " _W_ ").replace("\n", " _W_ ")
                # Remove single spaces
                resume_text = resume_text.replace(" ", "")
                # Restore boundaries
                resume_text = resume_text.replace("_W_", " ").replace(",", ", ")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")

    jd_text = job_description.lower()

    def get_words(text):
        words = re.findall(r'\b[a-z]{3,}\b', text)
        stop_words = {"the", "and", "for", "with", "from", "that", "this", "are", "you", "your", "will", "can", "have", "has", "not", "but", "our", "all", "any", "how"}
        return set([w for w in words if w not in stop_words])

    resume_words = get_words(resume_text)
    jd_words = get_words(jd_text)

    if len(jd_words) == 0:
        jd_words = {"experience"} # fallback

    matched = jd_words.intersection(resume_words)
    missing = jd_words.difference(resume_words)
    
    # JDs are full of fluff. Matching 25% of unique non-stop words is practically a perfect match.
    effective_total = max(1, int(len(jd_words) * 0.25))
    score = int((len(matched) / effective_total) * 100)
    score = min(100, score)
    
    formatting_issues = []
    improvement_tips = []
    
    word_count = len(resume_text.split())
    if word_count < 250:
        formatting_issues.append("Resume is too short (under 250 words).")
        improvement_tips.append("Add more details to your bullet points to show impact.")
    elif word_count > 1000:
        formatting_issues.append("Resume is a bit long (over 1000 words).")
        improvement_tips.append("Consider trimming older or less relevant experience.")

    if "education" not in resume_text:
        formatting_issues.append("Could not find an 'Education' section.")
        improvement_tips.append("Add a clearly labeled 'Education' section.")
        
    if "experience" not in resume_text and "employment" not in resume_text and "work history" not in resume_text:
        formatting_issues.append("Could not find an 'Experience' section.")
        improvement_tips.append("Add a clearly labeled 'Experience' or 'Employment' section.")

    missing_list = list(missing)[:12]

    return {
        "ats_analysis": {
            "ats_score": score,
            "missing_keywords": missing_list,
            "formatting_issues": formatting_issues,
            "improvement_tips": improvement_tips
        }
    }

@router.post("/cover-letter")
async def cover_letter(resume: UploadFile = File(...), job_description: str = Form(...), tone: str = Form("Professional")):
    resume_bytes = await resume.read()
    mime = mimetypes.guess_type(resume.filename)[0] or "application/pdf"
    file_uri = upload_to_gemini(resume_bytes, resume.filename, mime)
    
    prompt = f"Write a highly persuasive {tone} cover letter for the following job description:\n{job_description}\nBase the cover letter on the candidate's uploaded resume."
    return {"cover_letter": generate_ai_response(prompt, file_uri=file_uri)}

@router.post("/ocr-scanner")
async def ocr_scanner(image: UploadFile = File(...)):
    image_bytes = await image.read()
    mime = mimetypes.guess_type(image.filename)[0] or "image/jpeg"
    file_uri = upload_to_gemini(image_bytes, image.filename, mime)
    
    prompt = "Extract all the text from this image precisely as it appears. Preserve the formatting as best as possible."
    return {"extracted_text": generate_ai_response(prompt, file_uri=file_uri)}

from fastapi.responses import StreamingResponse
from pypdf import PdfReader, PdfWriter
from io import BytesIO
from PIL import Image, ImageEnhance
from typing import List

@router.post("/merge-pdf")
async def merge_pdf(files: List[UploadFile] = File(...)):
    merger = PdfWriter()
    for file in files:
        try:
            merger.append(BytesIO(await file.read()))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid PDF file '{file.filename}': {str(e)}")
    
    out_stream = BytesIO()
    merger.write(out_stream)
    out_stream.seek(0)
    return StreamingResponse(out_stream, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=merged.pdf"})

@router.post("/split-pdf")
async def split_pdf(file: UploadFile = File(...), page_numbers: str = Form(...)):
    reader = PdfReader(BytesIO(await file.read()))
    writer = PdfWriter()
    
    pages = [int(p.strip()) - 1 for p in page_numbers.split(",") if p.strip().isdigit()]
    for p in pages:
        if 0 <= p < len(reader.pages):
            writer.add_page(reader.pages[p])
            
    out_stream = BytesIO()
    writer.write(out_stream)
    out_stream.seek(0)
    return StreamingResponse(out_stream, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=split.pdf"})

@router.post("/compress-pdf")
async def compress_pdf(
    file: UploadFile = File(...), 
    quality: int = Form(50), 
    target_size_kb: int = Form(None)
):
    try:
        content = await file.read()
        
        if target_size_kb is not None and target_size_kb > 0:
            target_bytes = target_size_kb * 1024
            current_quality = 80
            best_out_stream = None
            
            while current_quality >= 10:
                reader = PdfReader(BytesIO(content))
                writer = PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)
                
                if reader.metadata is not None:
                    writer.add_metadata(reader.metadata)
                    
                for page in writer.pages:
                    page.compress_content_streams()
                    if hasattr(page, "images"):
                        for img in page.images:
                            try:
                                img.replace(img.image, quality=current_quality)
                            except Exception:
                                pass
                
                out_stream = BytesIO()
                writer.write(out_stream)
                
                if out_stream.getbuffer().nbytes <= target_bytes:
                    best_out_stream = out_stream
                    break
                
                # If quality is 10 and we still haven't met target, just keep it
                if current_quality == 10:
                    best_out_stream = out_stream
                    
                current_quality -= 10
                
            best_out_stream.seek(0)
            return StreamingResponse(best_out_stream, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=compressed.pdf"})
            
        else:
            reader = PdfReader(BytesIO(content))
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            
            if reader.metadata is not None:
                writer.add_metadata(reader.metadata)
                
            for page in writer.pages:
                page.compress_content_streams()
                
                # Compress images to actually reduce file size
                if hasattr(page, "images"):
                    for img in page.images:
                        try:
                            img.replace(img.image, quality=quality)
                        except Exception:
                            pass
                
            out_stream = BytesIO()
            writer.write(out_stream)
            out_stream.seek(0)
            return StreamingResponse(out_stream, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=compressed.pdf"})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to compress PDF: {str(e)}")

@router.post("/document-scan")
async def document_scan(
    images: List[UploadFile] = File(...),
    scan_type: str = Form("magic_color")
):
    enhanced_imgs = []
    
    for img_file in images:
        img_bytes = await img_file.read()
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        
        if scan_type == "magic_color":
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.8)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.5)
        elif scan_type == "black_white":
            # Convert to Grayscale then threshold
            img = img.convert("L")
            img = img.point(lambda x: 0 if x < 128 else 255, '1')
            # Convert back to RGB for consistency in saving
            img = img.convert("RGB")
        elif scan_type == "grayscale":
            img = img.convert("L")
            img = img.convert("RGB")
        # original does nothing
        
        enhanced_imgs.append(img)
        
    out_stream = BytesIO()
    
    if len(enhanced_imgs) == 1:
        enhanced_imgs[0].save(out_stream, format="PDF")
    else:
        enhanced_imgs[0].save(out_stream, format="PDF", save_all=True, append_images=enhanced_imgs[1:])
        
    out_stream.seek(0)
    return Response(content=out_stream.getvalue(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=scanned_document.pdf"})

@router.post("/image-to-pdf")
async def image_to_pdf(images: List[UploadFile] = File(...)):
    image_objs = []
    for img_file in images:
        img_bytes = await img_file.read()
        img = Image.open(BytesIO(img_bytes)).convert("RGB")
        image_objs.append(img)
        
    if not image_objs:
        raise HTTPException(status_code=400, detail="No images provided")
        
    out_stream = BytesIO()
    image_objs[0].save(out_stream, format="PDF", save_all=True, append_images=image_objs[1:])
    out_stream.seek(0)
    return StreamingResponse(out_stream, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=converted.pdf"})

import subprocess
import tempfile
import os
import uuid

def convert_with_libreoffice(input_path: str, output_dir: str):
    # Mac LibreOffice binary path
    libreoffice_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if not os.path.exists(libreoffice_path):
        # Fallback to standard linux/brew path if they symlinked it
        libreoffice_path = "libreoffice"
        
    env_dir = f"file:///tmp/LibreOffice_Conversion_{uuid.uuid4().hex}"
        
    cmd = [
        libreoffice_path,
        f"-env:UserInstallation={env_dir}",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        output_dir,
        input_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

@router.post("/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        with open(input_path, "wb") as f:
            f.write(await file.read())
            
        try:
            convert_with_libreoffice(input_path, tmpdir)
            
            # The output filename will be the same but with .pdf extension
            base_name = os.path.splitext(file.filename)[0]
            output_path = os.path.join(tmpdir, f"{base_name}.pdf")
            
            if os.path.exists(output_path):
                # Read into memory so we can return it after tempdir is destroyed
                with open(output_path, "rb") as f:
                    pdf_data = f.read()
                return StreamingResponse(BytesIO(pdf_data), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={base_name}.pdf"})
            else:
                raise HTTPException(status_code=500, detail="Conversion failed: Output file not found.")
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"LibreOffice error: {e.stderr.decode()}")

from pdf2docx import Converter

@router.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        base_name = os.path.splitext(file.filename)[0]
        output_path = os.path.join(tmpdir, f"{base_name}.docx")
        
        with open(input_path, "wb") as f:
            f.write(await file.read())
            
        try:
            cv = Converter(input_path)
            cv.convert(output_path, start=0, end=None)
            cv.close()
            
            with open(output_path, "rb") as f:
                docx_data = f.read()
            return StreamingResponse(BytesIO(docx_data), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename={base_name}.docx"})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"pdf2docx error: {str(e)}")

@router.post("/excel-to-pdf")
async def excel_to_pdf(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        with open(input_path, "wb") as f:
            f.write(await file.read())
            
        try:
            convert_with_libreoffice(input_path, tmpdir)
            base_name = os.path.splitext(file.filename)[0]
            output_path = os.path.join(tmpdir, f"{base_name}.pdf")
            
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    pdf_data = f.read()
                return StreamingResponse(BytesIO(pdf_data), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={base_name}.pdf"})
            else:
                raise HTTPException(status_code=500, detail="Conversion failed: Output file not found.")
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"LibreOffice error: {e.stderr.decode()}")

@router.post("/ppt-to-pdf")
async def ppt_to_pdf(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        with open(input_path, "wb") as f:
            f.write(await file.read())
            
        try:
            convert_with_libreoffice(input_path, tmpdir)
            base_name = os.path.splitext(file.filename)[0]
            output_path = os.path.join(tmpdir, f"{base_name}.pdf")
            
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    pdf_data = f.read()
                return StreamingResponse(BytesIO(pdf_data), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={base_name}.pdf"})
            else:
                raise HTTPException(status_code=500, detail="Conversion failed: Output file not found.")
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"LibreOffice error: {e.stderr.decode()}")
@router.post("/id-card-gen")
def id_card_gen(req: IDCardRequest):
    prompt = f"Generate JSON data for a professional {req.card_type} ID card. Name: {req.name}, Role: {req.role}, Org: {req.organization}, ID: {req.id_number}, Blood Group: {req.blood_group}. Return a JSON object with keys: 'front_details', 'back_details', 'barcode_value'."
    raw_json = clean_json_string(generate_ai_response(prompt, json_mode=True))
    try:
        return {"id_card": json.loads(raw_json)}
    except json.JSONDecodeError:
        return {"id_card": raw_json}

import zipfile

@router.post("/pdf-to-image")
async def pdf_to_image(file: UploadFile = File(...), output_format: str = Form("jpeg")):
    # Convert PDF pages directly to images using pdf2image
    pdf_bytes = await file.read()
    output_format = output_format.lower()
    
    if output_format not in ["jpeg", "jpg", "png", "webp"]:
        output_format = "jpeg"
        
    pil_format = "JPEG"
    ext = "jpg"
    if output_format == "png":
        pil_format = "PNG"
        ext = "png"
    elif output_format == "webp":
        pil_format = "WEBP"
        ext = "webp"
    
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to convert PDF to images: {str(e)}")
        
    out_zip = BytesIO()
    with zipfile.ZipFile(out_zip, "w") as zf:
        for i, page_img in enumerate(pages):
            img_bytes = BytesIO()
            save_kwargs = {}
            if pil_format == "JPEG" or pil_format == "WEBP":
                save_kwargs["quality"] = 85
            page_img.save(img_bytes, format=pil_format, **save_kwargs)
            zf.writestr(f"page_{i+1}.{ext}", img_bytes.getvalue())
                
    if len(pages) == 0:
        raise HTTPException(status_code=404, detail="No pages found in this PDF.")
        
    out_zip.seek(0)
    return StreamingResponse(out_zip, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=extracted_images.zip"})

from pdf2image import convert_from_bytes
import tempfile
import os
import rembg
from typing import Optional
from fastapi import Form
from PIL import ImageDraw, ImageFont

@router.post("/watermark-pdf")
async def watermark_pdf(
    file: UploadFile = File(...), 
    watermark_image: Optional[UploadFile] = File(None),
    watermark_text: Optional[str] = Form(None)
):
    # Read files
    pdf_bytes = await file.read()
    
    wm_img = None
    if watermark_image and watermark_image.filename:
        wm_bytes = await watermark_image.read()
        try:
            no_bg_bytes = rembg.remove(wm_bytes)
            wm_img = Image.open(BytesIO(no_bg_bytes)).convert("RGBA")
        except Exception as e:
            wm_img = Image.open(BytesIO(wm_bytes)).convert("RGBA")
    elif watermark_text:
        # Create a text watermark image
        txt_img = Image.new("RGBA", (3000, 3000), (255, 255, 255, 0))
        d_txt = ImageDraw.Draw(txt_img)
        
        font = None
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        for path in font_paths:
            try:
                font = ImageFont.truetype(path, 200)
                break
            except:
                continue
                
        if font is None:
            font = ImageFont.load_default()
                
        # Draw text center
        d_txt.text((1500, 1500), watermark_text, fill=(100, 100, 100, 255), font=font, anchor="mm")
        
        # Crop to the actual text bounding box so it scales properly
        bbox = txt_img.getbbox()
        if bbox:
            txt_img = txt_img.crop(bbox)
            
        # Rotate text diagonally (45 degrees) and expand
        wm_img = txt_img.rotate(45, expand=True)
    else:
        raise HTTPException(status_code=400, detail="Must provide either watermark_image or watermark_text")
    
    # We will use pdf2image to rasterize the PDF, allowing true transparent overlays!
    try:
        pages = convert_from_bytes(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid PDF file (make sure you uploaded a .pdf and not a .docx): {str(e)}")
        
    watermarked_pages = []
    
    for page_img in pages:
        page_img = page_img.convert("RGBA")
        page_width, page_height = page_img.size
        
        # Resize watermark to 80% of page width
        wm_ratio = wm_img.width / wm_img.height
        new_width = int(page_width * 0.8)
        new_height = int(new_width / wm_ratio)
        wm_resized = wm_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Apply opacity (e.g. 30% visible)
        alpha = wm_resized.split()[3]
        alpha = alpha.point(lambda p: p * 0.3)
        wm_resized.putalpha(alpha)
        
        # Calculate center
        x = int((page_width - new_width) / 2)
        y = int((page_height - new_height) / 2)
        
        # Paste with true transparency mask!
        page_img.paste(wm_resized, (x, y), wm_resized)
        
        # Convert back to RGB for PDF saving
        watermarked_pages.append(page_img.convert("RGB"))
        
    if not watermarked_pages:
        raise HTTPException(status_code=400, detail="PDF has no pages.")
        
    out_stream = BytesIO()
    # Save the first page, append the rest
    watermarked_pages[0].save(out_stream, format="PDF", save_all=True, append_images=watermarked_pages[1:])
    out_stream.seek(0)
    
    return StreamingResponse(out_stream, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=watermarked.pdf"})

@router.post("/pdf-to-text")
async def pdf_to_text(file: UploadFile = File(...)):
    try:
        reader = PdfReader(BytesIO(await file.read()))
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return {"extracted_text": text.strip()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")

import docx

@router.post("/word-to-text")
async def word_to_text(file: UploadFile = File(...)):
    try:
        doc = docx.Document(BytesIO(await file.read()))
        text = "\n".join([p.text for p in doc.paragraphs])
        return {"extracted_text": text.strip()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Word document: {str(e)}")

@router.post("/digital-sign")
async def digital_sign(file: UploadFile = File(...), signature_image: UploadFile = File(...), position: str = Form("bottom_right")):
    # Very similar to watermark, but we place it at the selected position
    pdf_bytes = await file.read()
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    
    sig_bytes = await signature_image.read()
    sig_img = Image.open(BytesIO(sig_bytes)).convert("RGBA")
    
    # We only sign the LAST page
    last_page_idx = len(reader.pages) - 1
    
    for i, page in enumerate(reader.pages):
        if i == last_page_idx:
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            # Make signature 25% of page width
            sig_ratio = sig_img.width / sig_img.height
            new_width = int(page_width * 0.25)
            new_height = int(new_width / sig_ratio)
            sig_resized = sig_img.resize((new_width, new_height), Image.LANCZOS)
            
            padding = 40
            # If we save RGBA as PDF, PIL might complain or drop transparency. Let's create a white page with the signature, 
            # wait, if we merge a white page, it will hide the PDF content!
            # We must use transparency. PIL saving to PDF doesn't support transparency masks easily for merging in pypdf.
            # Let's just create a small PDF of exactly the signature size, and use PyPDF's merge_translated_page!
            
            # Save the signature itself as a PDF
            sig_pdf_bytes = BytesIO()
            # Convert to RGB with white background (transparency lost, but typically signatures are black on white)
            bg = Image.new("RGB", sig_resized.size, (255, 255, 255))
            bg.paste(sig_resized, mask=sig_resized.split()[3]) # Use alpha channel as mask
            bg.save(sig_pdf_bytes, format="PDF")
            sig_pdf_bytes.seek(0)
            
            sig_reader = PdfReader(sig_pdf_bytes)
            
            # In PDF coordinates, (0,0) is bottom-left
            if position == "bottom_right":
                pdf_x = float(page_width - new_width - padding)
                pdf_y = float(padding)
            elif position == "bottom_left":
                pdf_x = float(padding)
                pdf_y = float(padding)
            elif position == "top_right":
                pdf_x = float(page_width - new_width - padding)
                pdf_y = float(page_height - new_height - padding)
            elif position == "top_left":
                pdf_x = float(padding)
                pdf_y = float(page_height - new_height - padding)
            elif position == "center":
                pdf_x = float((page_width - new_width) / 2)
                pdf_y = float((page_height - new_height) / 2)
            else:
                pdf_x = float(page_width - new_width - padding)
                pdf_y = float(padding) 
            
            # We need to translate the signature page and merge it
            page.merge_translated_page(sig_reader.pages[0], tx=pdf_x, ty=pdf_y)
            writer.add_page(page)
        else:
            writer.add_page(page)
            
    out_stream = BytesIO()
    writer.write(out_stream)
    out_stream.seek(0)
    return StreamingResponse(out_stream, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=signed.pdf"})
