import os

endpoint = """
import rembg
from fastapi.responses import StreamingResponse

@router.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    try:
        content = await file.read()
        output_bytes = rembg.remove(content)
        
        out_buf = io.BytesIO(output_bytes)
        return StreamingResponse(out_buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(400, f"Background removal failed: {str(e)}")
"""

with open("routes/file_tools.py", "a") as f:
    f.write(endpoint)

print("Endpoint added.")
