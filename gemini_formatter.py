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
    if not response_dict.get('summary') and response_dict.get('full_analysis'):
        # Get material information
        material_type = "Unknown"
        if response_dict.get('material'):
            material_type = response_dict.get('material')
        elif 'material_detection' in response_dict and response_dict['material_detection'].get('primary_material'):
            material_type = response_dict['material_detection']['primary_material'].capitalize()
            
        # Determine item description from full analysis
        full_analysis_lower = response_dict.get('full_analysis', '').lower()
        item_description = "Waste item"
        if "bottle" in full_analysis_lower:
            item_description = "Plastic bottle"
        elif "container" in full_analysis_lower:
            item_description = "Container"
        elif "packaging" in full_analysis_lower:
            item_description = "Packaging material"
        elif "bag" in full_analysis_lower:
            item_description = "Bag"
        elif "cup" in full_analysis_lower:
            item_description = "Cup"
        elif "box" in full_analysis_lower:
            item_description = "Box"
        elif "device" in full_analysis_lower or "electronic" in full_analysis_lower:
            item_description = "Electronic device"
        
        # Determine recyclability
        recyclable = "Not recyclable"
        if response_dict.get('is_recyclable'):
            recyclable = "Recyclable"
            
        # Create bullet point summary with HTML formatting
        formatted['summary'] = f'<div class="bullet-point">The image shows a {item_description}.</div><div class="bullet-point">It is primarily made of {material_type}.</div><div class="bullet-point">This item is {recyclable}.</div>'
    elif 'summary' in response_dict:
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
    
    # Create a concise summary in bullet points
    material_type = ""
    if "plastic" in raw_text.lower():
        material_type = "Plastic"
    elif "paper" in raw_text.lower():
        material_type = "Paper"
    elif "metal" in raw_text.lower():
        material_type = "Metal"
    elif "glass" in raw_text.lower():
        material_type = "Glass"
    elif "fabric" in raw_text.lower() or "textile" in raw_text.lower():
        material_type = "Textile"
    elif "electronic" in raw_text.lower() or "e-waste" in raw_text.lower():
        material_type = "Electronic"
    else:
        material_type = "Mixed materials"
    
    # Extract an item description
    item_description = "Waste item"
    if "bottle" in raw_text.lower():
        item_description = "Plastic bottle"
    elif "container" in raw_text.lower():
        item_description = "Container"
    elif "packaging" in raw_text.lower():
        item_description = "Packaging material"
    elif "bag" in raw_text.lower():
        item_description = "Bag"
    elif "cup" in raw_text.lower():
        item_description = "Cup"
    elif "box" in raw_text.lower():
        item_description = "Box"
    elif "device" in raw_text.lower() or "electronic" in raw_text.lower():
        item_description = "Electronic device"
    
    # Determine recyclability
    recyclable = "Not recyclable"
    if "recyclable: yes" in raw_text.lower() or "is recyclable" in raw_text.lower():
        recyclable = "Recyclable"
    
    # Format the bullet point summary with HTML formatting
    result["summary"] = f'<div class="bullet-point">The image shows a {item_description}.</div><div class="bullet-point">It is primarily made of {material_type}.</div><div class="bullet-point">This item is {recyclable}.</div>'
    
    return result