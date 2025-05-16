import google.generativeai as genai
import PIL.Image
import os
import logging
from gemini_formatter import format_gemini_response, extract_sections_from_raw_text
import material_detection

# Configure Google Gemini AI with API key
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyC7NpSGRRDmacS1iwOd24Vu_5oMYr1oeSA")
genai.configure(api_key=api_key)

# Flag to enable/disable material detection
ENABLE_MATERIAL_DETECTION = True

def analyze_waste(image_path):
    """
    Analyze waste image using Google Gemini AI and material detection
    
    Args:
        image_path: Path to the uploaded image
        
    Returns:
        Dictionary containing analysis results
    """
    try:
        # Open image using PIL
        image = PIL.Image.open(image_path)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Run material detection if enabled
        material_detection_result = None
        if ENABLE_MATERIAL_DETECTION:
            try:
                material_detection_result = material_detection.detect_material(image_path)
                logging.info(f"Material detection result: {material_detection_result}")
            except Exception as e:
                logging.error(f"Error in material detection: {e}")
                material_detection_result = None
        
        # Configure the model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Add detected material information to the prompt if available
        material_info = ""
        if material_detection_result and not material_detection_result.get('error'):
            # Extract dominant colors for additional color analysis
            dominant_colors = []
            try:
                dominant_colors = material_detection.extract_dominant_colors(image_path, 3)
            except Exception as e:
                logging.error(f"Error extracting dominant colors: {e}")
            
            primary_material = material_detection_result.get('primary_material', 'unknown')
            recyclability = material_detection_result.get('recyclability_score', 0)
            is_recyclable = recyclability > 50
            is_ewaste = material_detection_result.get('is_ewaste', False)
            
            # Format material composition information
            composition_info = ""
            if 'composition' in material_detection_result:
                for material, data in material_detection_result['composition'].items():
                    composition_info += f"  - {material.capitalize()}: {data['percentage']}% (confidence: {data['confidence']:.2f})\n"
            
            # Format color information
            color_info = ""
            if dominant_colors:
                for i, color in enumerate(dominant_colors[:3], 1):
                    color_info += f"  - Color {i}: RGB({color[0]}, {color[1]}, {color[2]})\n"
            
            material_info = f"""
            I've performed an initial computer vision analysis of the image and detected the following:
            - Primary material: {primary_material.capitalize()}
            - Material composition:\n{composition_info}
            - Is recyclable: {'Likely' if is_recyclable else 'Unlikely'} (score: {recyclability}%)
            - Is electronic waste: {'Yes' if is_ewaste else 'No'}
            - Dominant colors:\n{color_info}
            - Analysis method: {material_detection_result.get('analysis_method', 'unknown')}
            
            Please consider this information in your analysis, but use your own judgment if you disagree.
            """
        
        # Generate content with a detailed prompt
        prompt = (
            "You are WasteWorks AI Assistant, a specialized waste management analysis expert with deep knowledge of recycling processes, material science, and environmental impacts.\n\n"
            f"{material_info}\n\n"
            "Analyze this waste image in detail and provide the following information in a well-structured, clear format with HTML formatting:\n\n"
            "1. Is it recyclable? (Yes/No) - Provide a confident answer and explain your reasoning in detail. Consider regional variation in recyclability.\n"
            "2. Is it e-waste? (Yes/No) - Provide a confident answer and explain why it is or isn't electronic waste. Include information about hazardous components if present.\n"
            "3. Primary material composition - Specifically identify as one of: Plastic, Paper, Metal, Glass, Organic, Textile, Electronic, Mixed/Other. Choose the most dominant material and include specific subcategories (e.g., PET plastic, corrugated cardboard).\n"
            "4. Recycling preparation instructions - Provide detailed steps on how to prepare this item for recycling (cleaning, disassembly, separating components, removing labels/caps, etc.). Format this as an ordered list with clear steps.\n"
            "5. Environmental impact - Explain the environmental consequences if this item is improperly disposed of. Include decomposition time, pollution potential, and resource loss. Format this with bullet points.\n"
            "6. Disposal recommendations - Recommend the most eco-friendly disposal method based on the item's composition. Suggest specific facilities or programs when applicable. Use bold formatting for key recommendations.\n\n"
            "Format each section with HTML for better readability. Use <h4> for section headings, <ul> and <ol> for lists, <strong> for emphasis, and <p> for paragraphs. Keep responses concise but informative.\n\n"
            "Respond with a confident analysis even with partial visibility or unclear images. Format your response as clearly labeled sections with detailed explanations for each point."
        )
        
        response = model.generate_content(
            [prompt, image],
            generation_config={
                "max_output_tokens": 1000,
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 40
            }
        )
        
        # Parse the response text
        analysis_text = response.text
        
        # Extract key information more robustly
        is_recyclable = False
        is_ewaste = False
        material = "Unknown"
        recycling_instructions = ""
        environmental_impact = ""
        disposal_recommendations = ""
        
        # More robust parsing strategy that's less dependent on specific formatting
        analysis_lower = analysis_text.lower()
        
        # Check for recyclability
        recyclable_indicators = ["1. is it recyclable", "recyclable:", "recyclability:"]
        for indicator in recyclable_indicators:
            if indicator in analysis_lower:
                # Look for a Yes/No response within 100 characters after the indicator
                segment = analysis_lower[analysis_lower.find(indicator):analysis_lower.find(indicator) + 100]
                is_recyclable = "yes" in segment and not ("no" in segment and segment.find("no") < segment.find("yes"))
                break
        
        # Check for e-waste
        ewaste_indicators = ["2. is it e-waste", "e-waste:", "electronic waste:"]
        for indicator in ewaste_indicators:
            if indicator in analysis_lower:
                # Look for a Yes/No response within 100 characters after the indicator
                segment = analysis_lower[analysis_lower.find(indicator):analysis_lower.find(indicator) + 100]
                is_ewaste = "yes" in segment and not ("no" in segment and segment.find("no") < segment.find("yes"))
                break
        
        # Extract material using a more flexible approach
        material_indicators = ["3. primary material", "material composition:", "primary material:"]
        for indicator in material_indicators:
            if indicator in analysis_lower:
                # Get the 150 characters after the indicator to find material
                material_section = analysis_lower[analysis_lower.find(indicator):analysis_lower.find(indicator) + 150]
                
                # Look for specific materials
                materials = {
                    "plastic": "Plastic",
                    "paper": "Paper",
                    "cardboard": "Paper",
                    "metal": "Metal",
                    "aluminum": "Metal",
                    "steel": "Metal",
                    "glass": "Glass",
                    "organic": "Organic",
                    "food": "Organic",
                    "textile": "Textile",
                    "fabric": "Textile",
                    "clothing": "Textile",
                    "electronic": "Electronic",
                    "battery": "Electronic"
                }
                
                # Find the first material mentioned
                for key, value in materials.items():
                    if key in material_section:
                        material = value
                        break
                
                break
        
        # Extract recycling instructions
        try:
            if "4. recycling preparation" in analysis_lower:
                start = analysis_lower.find("4. recycling preparation")
                next_section = analysis_lower.find("5.", start)
                if next_section == -1:  # If there's no next section
                    next_section = len(analysis_lower)
                recycling_instructions = analysis_text[start:next_section].strip()
            elif "preparation" in analysis_lower:
                start = analysis_lower.find("preparation")
                end = analysis_lower.find("\n\n", start)
                if end == -1:
                    end = len(analysis_lower)
                recycling_instructions = analysis_text[start:end].strip()
        except:
            recycling_instructions = "No specific preparation instructions available."
            
        # Extract environmental impact
        try:
            if "5. environmental impact" in analysis_lower:
                start = analysis_lower.find("5. environmental impact")
                next_section = analysis_lower.find("6.", start)
                if next_section == -1:
                    next_section = len(analysis_lower)
                environmental_impact = analysis_text[start:next_section].strip()
        except:
            environmental_impact = "Environmental impact analysis not available."
            
        # Extract disposal recommendations
        try:
            if "6. disposal" in analysis_lower:
                start = analysis_lower.find("6. disposal")
                next_section = analysis_lower.find("\n\n", start + 15)
                if next_section == -1:
                    next_section = len(analysis_lower)
                disposal_recommendations = analysis_text[start:next_section].strip()
        except:
            disposal_recommendations = "Specific disposal recommendations not available."
        
        # Format the result with additional information
        result = {
            "full_analysis": analysis_text,
            "is_recyclable": is_recyclable,
            "is_ewaste": is_ewaste,
            "material": material,
            "recycling_instructions": recycling_instructions,
            "environmental_impact": environmental_impact,
            "disposal_recommendations": disposal_recommendations
        }
        
        # Include material detection results if available
        if material_detection_result and not material_detection_result.get('error'):
            result["material_detection"] = material_detection_result
        
        # Use our formatter to clean up the text and improve presentation
        formatted_result = format_gemini_response(result)
        
        # If we have a full analysis but missing section data, try to extract it
        if (not recycling_instructions or not environmental_impact or not disposal_recommendations) and analysis_text:
            extracted_sections = extract_sections_from_raw_text(analysis_text)
            
            # Only update missing sections
            if not formatted_result["recycling_instructions"] and extracted_sections["recycling_instructions"]:
                formatted_result["recycling_instructions"] = extracted_sections["recycling_instructions"]
                
            if not formatted_result["environmental_impact"] and extracted_sections["environmental_impact"]:
                formatted_result["environmental_impact"] = extracted_sections["environmental_impact"]
                
            if not formatted_result["disposal_recommendations"] and extracted_sections["disposal_recommendations"]:
                formatted_result["disposal_recommendations"] = extracted_sections["disposal_recommendations"]
        
        return formatted_result
    
    except Exception as e:
        logging.error(f"Error in image analysis: {e}")
        error_result = {
            "error": str(e),
            "full_analysis": "Analysis failed",
            "is_recyclable": False,
            "is_ewaste": False,
            "material": "Unknown",
            "recycling_instructions": "Could not analyze the image.",
            "environmental_impact": "Could not analyze the image.",
            "disposal_recommendations": "Could not analyze the image."
        }
        
        # Format the error result to ensure consistent output format
        return format_gemini_response(error_result)
