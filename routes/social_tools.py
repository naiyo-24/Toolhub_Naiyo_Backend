from fastapi import APIRouter, HTTPException
import json
from schemas.social_tools import (
    BioGeneratorRequest, UsernameGeneratorRequest, CaptionGeneratorRequest,
    HashtagGeneratorRequest, TextRequest, FancyTextRequest
)
from routes.ai_tools import generate_ai_response

router = APIRouter()

# -----------------------------
# 🤖 AI-POWERED TOOLS (GEMINI)
# -----------------------------

@router.post("/bio-generator")
def generate_bio(req: BioGeneratorRequest):
    details = f" Incorporate these details: {req.key_details}" if req.key_details else ""
    prompt = f"Write 3 creative social media bios for a {req.niche}. The tone should be {req.tone}.{details} Format the output as a JSON list of strings (no markdown blocks, just raw JSON array). Use emojis where appropriate."
    
    try:
        res = generate_ai_response(prompt, json_mode=True)
        try:
            bios = json.loads(res.strip('` \n').replace('json', '', 1))
            if isinstance(bios, dict):
                bios = bios.get("bios", list(bios.values())[0] if bios else [])
        except json.JSONDecodeError:
            import re
            match = re.search(r'\[.*\]', res, re.DOTALL)
            bios = json.loads(match.group(0)) if match else [res]
        return {"bios": bios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate bios: {str(e)}")

@router.post("/username-gen")
def generate_usernames(req: UsernameGeneratorRequest):
    interests = f" Their interests are: {req.niche_or_interests}." if req.niche_or_interests else ""
    prompt = f"Generate 5 unique, catchy social media username ideas based on the name/word '{req.base_name}'.{interests} The vibe should be {req.vibe}. Format the output as a JSON list of strings."
    
    try:
        res = generate_ai_response(prompt, json_mode=True)
        try:
            usernames = json.loads(res.strip('` \n').replace('json', '', 1))
            if isinstance(usernames, dict):
                usernames = usernames.get("usernames", list(usernames.values())[0] if usernames else [])
        except json.JSONDecodeError:
            import re
            match = re.search(r'\[.*\]', res, re.DOTALL)
            usernames = json.loads(match.group(0)) if match else [res]
        return {"usernames": usernames}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate usernames: {str(e)}")

@router.post("/caption-gen")
def generate_caption(req: CaptionGeneratorRequest):
    emojis = "Include relevant emojis." if req.include_emojis else "Do not include any emojis."
    prompt = f"Write a highly engaging social media caption for a post about: '{req.post_description}'. The tone should be {req.tone}. {emojis} Return only the caption text."
    
    try:
        res = generate_ai_response(prompt)
        return {"caption": res.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hashtag-gen")
def generate_hashtags(req: HashtagGeneratorRequest):
    count = min(req.count, 30)
    prompt = f"Generate exactly {count} highly relevant and trending social media hashtags for the topic: '{req.topic}'. Return them as a JSON list of strings. Do not include the # symbol in the strings."
    
    try:
        res = generate_ai_response(prompt, json_mode=True)
        try:
            tags = json.loads(res.strip('` \n').replace('json', '', 1))
            if isinstance(tags, dict):
                tags = tags.get("hashtags", list(tags.values())[0] if tags else [])
        except json.JSONDecodeError:
            import re
            match = re.search(r'\[.*\]', res, re.DOTALL)
            tags = json.loads(match.group(0)) if match else [res]
            
        formatted_tags = [f"#{t.replace('#', '').strip()}" for t in tags if isinstance(t, str)]
        return {"hashtags": formatted_tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# ⚙️ LOGIC-BASED TOOLS
# -----------------------------

EMOJI_DICT = {
    "love": "❤️", "happy": "😊", "sad": "😢", "angry": "😠", "fire": "🔥",
    "cool": "😎", "pizza": "🍕", "cat": "🐱", "dog": "🐶", "sun": "☀️",
    "moon": "🌙", "star": "⭐", "money": "💰", "car": "🚗", "house": "🏠",
    "book": "📖", "music": "🎵", "food": "🍔", "coffee": "☕", "time": "⏰",
    "world": "🌍", "party": "🎉", "gift": "🎁", "heart": "💖", "laugh": "😂",
    "hello": "👋", "hi": "👋", "bye": "👋", "smile": "😃", "cry": "😭",
    "sleep": "😴", "hot": "🥵", "cold": "🥶", "yes": "👍", "no": "👎",
    "ok": "👌", "good": "👍", "bad": "👎", "work": "💼", "gym": "🏋️‍♂️",
    "game": "🎮", "movie": "🍿", "idea": "💡", "win": "🏆", "boom": "💥",
    "rocket": "🚀", "magic": "✨", "poop": "💩", "ghost": "👻", "alien": "👽",
    "beautiful": "🌸", "rose": "🌹", "flower": "🌺", "pretty": "🦋", 
    "handsome": "😎", "cute": "🥺", "brain": "🧠", "eye": "👁️",
    "water": "💧", "fireworks": "🎆", "cake": "🎂", "tree": "🌳",
    "computer": "💻", "phone": "📱", "shoes": "👟", "clothes": "👕"
}

@router.post("/emoji-converter")
def emoji_converter(req: TextRequest):
    words = req.text.split()
    converted = []
    for word in words:
        clean_word = "".join(c for c in word.lower() if c.isalnum())
        if clean_word in EMOJI_DICT:
            # Replace word with emoji or append it
            converted.append(f"{word} {EMOJI_DICT[clean_word]}")
        else:
            converted.append(word)
    
    return {"converted_text": " ".join(converted)}

@router.post("/fancy-text")
def fancy_text(req: FancyTextRequest):
    text = req.text
    
    def translate(text, normal_chars, fancy_chars):
        return "".join(fancy_chars[normal_chars.index(c)] if c in normal_chars else c for c in text)
        
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    # Mathematical bold Fraktur (Gothic)
    gothic = "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷𝔄𝔅┋𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ"
    # Actually, proper mapping:
    gothic = "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ"
    # Mathematical double-struck
    double = "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"
    # Mathematical script
    script = "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵"
    # Fullwidth
    fullwidth = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
    
    styles = {
        "gothic": translate(text, normal, gothic),
        "double_struck": translate(text, normal, double),
        "script": translate(text, normal, script),
        "fullwidth": translate(text, normal, fullwidth),
        "strikethrough": "".join(c + "\u0336" for c in text),
        "underline": "".join(c + "\u0332" for c in text)
    }
    
    return {"styles": styles}

@router.post("/text-to-emoji")
def text_to_emoji(req: TextRequest):
    # Converts standard text into regional indicator letters (e.g. A -> 🇦)
    result = ""
    for char in req.text.lower():
        if 'a' <= char <= 'z':
            # 🇦 is U+1F1E6. 'a' is 97. 
            # So offset is 127397 (127462 - 97 = 127365)
            result += chr(ord(char) + 127365) + " "
        elif char == " ":
            result += "   "
        else:
            result += char + " "
            
    return {"emoji_text": result.strip()}

@router.post("/char-counter")
def char_counter(req: TextRequest):
    text = req.text
    char_count = len(text)
    char_no_space = len(text.replace(" ", "").replace("\n", ""))
    word_count = len(text.split())
    # Splitting by newline and ignoring empty lines
    para_count = len([p for p in text.split('\n') if p.strip()])
    
    return {
        "character_count_with_spaces": char_count,
        "character_count_without_spaces": char_no_space,
        "word_count": word_count,
        "paragraph_count": para_count
    }
