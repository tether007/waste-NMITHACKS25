"""
Format and clean Gemini AI output for better display in the application.
This module removes HTML tags, numbering, and other formatting that
makes the AI output less readable in the UI.
"""

import re
from bs4 import BeautifulSoup

def clean_text(text):
    """
    Remove HTML tags and clean text for better readability
    
    Args:
        text: Text string that might contain HTML tags
        
    Returns:
        Clean text without HTML tags
    """
    if not text:
        return ""
        
    # Use BeautifulSoup to remove HTML
    soup = BeautifulSoup(text, 'html.parser')
    clean = soup.get_text()
    
    # Remove numbered list patterns (1., 2., etc.)
    clean = re.sub(r'^\s*\d+\.\s*', '', clean, flags=re.MULTILINE)
    
    # Remove extra whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    return clean

def convert_to_bullet_points(text, keep_headings=True):
    """
    Convert a paragraph of text into bullet points
    
    Args:
        text: Text string to convert
        keep_headings: Whether to keep section headings
        
    Returns:
        Text formatted as bullet points
    """
    if not text:
        return ""
    
    # Split the text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Filter out empty sentences and very short ones
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    # Extract heading if present (assume it's the first line if it ends with a colon)
    heading = ""
    if keep_headings and sentences and ':' in sentences[0]:
        heading_parts = sentences[0].split(':', 1)
        if len(heading_parts) == 2:
            heading = heading_parts[0] + ":\n"
            sentences[0] = heading_parts[1].strip()
    
    # Convert each sentence to a bullet point with HTML formatting
    bullet_points = [f'<div class="bullet-point">{s}</div>' for s in sentences]
    
    # Join with no extra newlines (the CSS will handle spacing)
    return heading + "".join(bullet_points)

def get_material_type(response_dict, raw_text=""):
    """
    Determine the material type based on response dictionary or raw text
    
    Args:
        response_dict: Dictionary containing the Gemini AI response
        raw_text: Optional raw text to analyze if response_dict doesn't have material info
        
    Returns:
        String with the determined material type
    """
    # First check if material is explicitly provided
    if response_dict.get('material'):
        return response_dict.get('material')
    
    # Next check if material detection info is available
    if 'material_detection' in response_dict and response_dict['material_detection'].get('primary_material'):
        return response_dict['material_detection']['primary_material'].capitalize()
    
    # If UI indicates a specific material was selected, use that
    if response_dict.get('ui_selected_material'):
        return response_dict.get('ui_selected_material')
    
    # If not, try to infer from text
    text_to_analyze = raw_text.lower() if raw_text else (response_dict.get('full_analysis', '')).lower()
    
    # Check for material mentions in priority order
    if "paper" in text_to_analyze:
        return "Paper"
    elif "plastic" in text_to_analyze:
        return "Plastic"
    elif "metal" in text_to_analyze:
        return "Metal"
    elif "glass" in text_to_analyze:
        return "Glass"
    elif "fabric" in text_to_analyze or "textile" in text_to_analyze:
        return "Textile"
    elif "electronic" in text_to_analyze or "e-waste" in text_to_analyze:
        return "Electronic"
    else:
        return "Mixed materials"

def get_item_description(response_dict, material_type, raw_text=""):
    """
    Get the appropriate item description based on the response dict, determined material type, and raw text
    
    Args:
        response_dict: Dictionary containing the Gemini AI response
        material_type: Already determined material type
        raw_text: Optional raw text to analyze
        
    Returns:
        String with appropriate item description
    """
    # If there's an explicit item type, use it
    if response_dict.get('item_type'):
        return response_dict.get('item_type')
    
    # Otherwise analyze the text
    text_to_analyze = raw_text.lower() if raw_text else (response_dict.get('full_analysis', '')).lower()
    
    # Handle material-specific items based on determined material type
    if material_type == "Paper":
        if "document" in text_to_analyze or "sheet" in text_to_analyze:
            return "Paper document"
        elif "box" in text_to_analyze or "cardboard" in text_to_analyze:
            return "Paper box"
        elif "notebook" in text_to_analyze:
            return "Notebook"
        elif "newspaper" in text_to_analyze or "magazine" in text_to_analyze:
            return "Publication"
        else:
            return "Paper item"
    
    # Only if specifically identified as electronic AND material is electronic
    if material_type == "Electronic" and ("device" in text_to_analyze or "electronic" in text_to_analyze):
        return "Electronic device"
    
    # Other common items by frequency in text
    if "bottle" in text_to_analyze:
        return f"{material_type} bottle"
    elif "container" in text_to_analyze:
        return f"{material_type} container"
    elif "packaging" in text_to_analyze:
        return f"{material_type} packaging"
    elif "bag" in text_to_analyze:
        return f"{material_type} bag"
    elif "cup" in text_to_analyze:
        return f"{material_type} cup"
    elif "box" in text_to_analyze:
        return f"{material_type} box"
    
    # Default to material-based description
    return f"{material_type} item"

def is_item_recyclable(response_dict, raw_text=""):
    """
    Determine if the item is recyclable based on response dictionary, material type, or raw text.
    
    Args:
        response_dict: Dictionary containing the Gemini AI response
        raw_text: Optional raw text to analyze
        
    Returns:
        String indicating recyclability status
    """
    # Check if UI explicitly indicates recyclability
    if response_dict.get('is_recyclable') == True or response_dict.get('recyclable') == "Yes":
        return "Recyclable"
    
    if response_dict.get('is_recyclable') == False or response_dict.get('recyclable') == "No":
        return "Not recyclable"
    
    # Determine material type
    material_type = get_material_type(response_dict, raw_text).lower()
    
    # Automatically mark certain materials as recyclable
    if material_type in ["plastic", "paper", "metal", "electronic", "e-waste"]:
        return "Recyclable"
    
    # Check text for recyclability indicators
    text_to_analyze = raw_text.lower() if raw_text else (response_dict.get('full_analysis', '')).lower()
    
    if "recyclable: yes" in text_to_analyze or "is recyclable" in text_to_analyze or "can be recycled" in text_to_analyze:
        return "Recyclable"
    elif "not recyclable" in text_to_analyze or "cannot be recycled" in text_to_analyze or "non-recyclable" in text_to_analyze:
        return "Not recyclable"
    
    return "Check local recycling guidelines"


def is_e_waste(response_dict, material_type, raw_text=""):
    """
    Determine if the item is e-waste based on response dict, material type, and text
    
    Args:
        response_dict: Dictionary containing the Gemini AI response
        material_type: Already determined material type
        raw_text: Optional raw text to analyze
    
    Returns:
        Boolean indicating e-waste status
    """
    # Check if UI explicitly indicates e-waste
    if response_dict.get('e_waste') == "Yes" or response_dict.get('is_e_waste') == True:
        return True
    
    # If material is electronic, likely e-waste
    if material_type == "Electronic":
        return True
    
    # Check text for e-waste indicators
    text_to_analyze = raw_text.lower() if raw_text else (response_dict.get('full_analysis', '')).lower()
    
    if "e-waste" in text_to_analyze or "electronic waste" in text_to_analyze:
        return True
    
    return False

def format_gemini_response(response_dict):
    """
    Format the response from Gemini AI to clean up sections
    and remove unwanted elements.
    
    Args:
        response_dict: Dictionary containing the Gemini AI response
        
    Returns:
        Updated dictionary with cleaned and formatted text
    """
    formatted = {}
    
    # Copy original fields
    formatted.update(response_dict)
    
    # Clean specific text fields and convert to bullet points
    if 'full_analysis' in response_dict:
        clean_analysis = clean_text(response_dict['full_analysis'])
        formatted['full_analysis'] = convert_to_bullet_points(clean_analysis, keep_headings=True)
    
    if 'recycling_instructions' in response_dict:
        # Remove headings like "How to recycle:" 
        text = clean_text(response_dict['recycling_instructions'])
        text = re.sub(r'^(How to recycle:|Recycling Instructions:)\s*', '', text, flags=re.IGNORECASE)
        formatted['recycling_instructions'] = "Recycling preparation instructions:\n" + convert_to_bullet_points(text, keep_headings=False)
    
    if 'environmental_impact' in response_dict:
        # Remove headings like "Environmental Impact:"
        text = clean_text(response_dict['environmental_impact'])
        text = re.sub(r'^(Environmental Impact:|Impact:)\s*', '', text, flags=re.IGNORECASE)
        formatted['environmental_impact'] = "Environmental impact:\n" + convert_to_bullet_points(text, keep_headings=False)
    
    if 'disposal_recommendations' in response_dict:
        # Remove headings and numbering
        text = clean_text(response_dict['disposal_recommendations'])
        text = re.sub(r'^(Disposal Recommendations:|Best Disposal Method:)\s*', '', text, flags=re.IGNORECASE)
        formatted['disposal_recommendations'] = "Disposal recommendations:\n" + convert_to_bullet_points(text, keep_headings=False)
    
    # Generate summary based on available information if not already there
    if not response_dict.get('summary'):
        # Get material information using the dedicated function
        material_type = get_material_type(response_dict)
            
        # Get item description using the dedicated function
        item_description = get_item_description(response_dict, material_type)
        
        # Determine recyclability using dedicated function
        recyclable = is_item_recyclable(response_dict)
        
        # Create bullet point summary with HTML formatting
        formatted['summary'] = f'<div class="bullet-point">The image shows a {item_description}.</div><div class="bullet-point">It is primarily made of {material_type}.</div><div class="bullet-point">This item is {recyclable}.</div>'
    elif 'summary' in response_dict:
        # If summary exists, keep it as is
        formatted['summary'] = response_dict['summary']
    
    return formatted

def extract_sections_from_raw_text(raw_text):
    """
    Extract different sections from a single raw text response.
    Useful when Gemini returns a single block of text that needs
    to be split into appropriate sections.
    
    Args:
        raw_text: The full text response from Gemini
        
    Returns:
        Dictionary with extracted sections
    """
    result = {
        "full_analysis": raw_text,
        "recycling_instructions": "",
        "environmental_impact": "",
        "disposal_recommendations": "",
        "summary": ""
    }
    
    # Extract recycling instructions
    recycling_match = re.search(
        r'(?:recycling instructions:|how to recycle:)(.*?)(?=environmental impact:|$)', 
        raw_text, 
        re.IGNORECASE | re.DOTALL
    )
    if recycling_match:
        text = recycling_match.group(1).strip()
        result["recycling_instructions"] = "Recycling preparation instructions:\n" + convert_to_bullet_points(text, keep_headings=False)
    
    # Extract environmental impact
    impact_match = re.search(
        r'(?:environmental impact:|impact:)(.*?)(?=disposal|best disposal method|$)', 
        raw_text, 
        re.IGNORECASE | re.DOTALL
    )
    if impact_match:
        text = impact_match.group(1).strip()
        result["environmental_impact"] = "Environmental impact:\n" + convert_to_bullet_points(text, keep_headings=False)
    
    # Extract disposal recommendations
    disposal_match = re.search(
        r'(?:disposal recommendations:|best disposal method:)(.*?)(?=\Z)', 
        raw_text, 
        re.IGNORECASE | re.DOTALL
    )
    if disposal_match:
        text = disposal_match.group(1).strip()
        result["disposal_recommendations"] = "Disposal recommendations:\n" + convert_to_bullet_points(text, keep_headings=False)
    
    # Use dedicated functions for material, description, and recyclability
    material_type = get_material_type({}, raw_text)
    item_description = get_item_description({}, material_type, raw_text)
    recyclable = is_item_recyclable({}, raw_text)
    
    # Create bullet point summary with HTML formatting
    result["summary"] = f'<div class="bullet-point">The image shows a {item_description}.</div><div class="bullet-point">It is primarily made of {material_type}.</div><div class="bullet-point">This item is {recyclable}.</div>'
    
    # Set e-waste flag based on analysis
    result["is_e_waste"] = is_e_waste({}, material_type, raw_text)
    
    return result
