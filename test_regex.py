import re

def extract_between(text, start_label, end_labels):
    def make_regex(label):
        chars = [re.escape(c) for c in label if c.strip()]
        return r'\s*'.join(chars)
        
    start_pattern = make_regex(start_label)
    start_match = re.search(start_pattern, text, re.IGNORECASE)
    if not start_match: return None
    
    start_idx = start_match.end()
    end_idx = len(text)
    
    for end_label in end_labels:
        end_pattern = make_regex(end_label)
        end_match = re.search(end_pattern, text[start_idx:], re.IGNORECASE)
        if end_match:
            match_pos = start_idx + end_match.start()
            if match_pos < end_idx:
                end_idx = match_pos
                
    extracted = text[start_idx:end_idx].strip()
    extracted = re.sub(r'^[\s:\-,|]+', '', extracted)
    extracted = re.sub(r'\s*\d+[\.,]?\s*$', '', extracted)
    extracted = re.sub(r'\s*de\s*$', '', extracted)
    extracted = re.sub(r'[\s.,|]+$', '', extracted)
    
    return extracted.strip() if extracted else None

text = """
            GSTIN          19ASEPR2246P1Z3                                          
            LegalName      BIPLABKUMARROY                                           
                                                                                    
            TradeName,ifany R.B.ENTERPRISE                                          
                                                                                    
                                                                                    
            DetailsofAdditionalPlacesofBusiness                                     
"""
print(extract_between(text, "Legal Name", ["Trade Name", "Constitution of Business", "Address"]))
print(extract_between(text, "Trade Name, if any", ["Constitution of Business", "Details of Additional", "Address"]))
