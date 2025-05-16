import os
import uuid
import base64
import re
from io import BytesIO
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from app import db
from models import WasteItem, DropLocation
from gemini_service import analyze_waste
from rewards import award_points_for_drop_off, check_achievements
import logging
from PIL import Image
from datetime import datetime

# Import the route modules for our new features
from tracking import register_tracking_routes
from infrastructure import register_infrastructure_routes

def register_routes(app):
    """Register all application routes"""
    
    @app.route("/", methods=["GET", "POST"])
    def index():
        """Handle home page and waste image uploads from file or webcam"""
        result = None
        image_path = None
        waste_item = None
        
        if request.method == "POST":
            # Check if we have a file upload or webcam image
            file_upload = "file" in request.files and request.files["file"].filename != ""
            webcam_upload = "webcam_image" in request.form and request.form["webcam_image"] and request.form["webcam_image"] != ""
            
            if not file_upload and not webcam_upload:
                flash("No image provided. Please upload an image or use the webcam.", "danger")
                return redirect(request.url)
            
            try:
                # Generate a unique filename
                filename = f"{uuid.uuid4()}.jpg"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                
                # Process either file upload or webcam image
                if file_upload:
                    # Regular file upload
                    file = request.files["file"]
                    file.save(file_path)
                    
                elif webcam_upload:
                    # Process webcam image (data URL)
                    webcam_data = request.form["webcam_image"]
                    # Extract the base64 data from the data URL
                    # Format typically: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...
                    image_data = re.sub('^data:image/.+;base64,', '', webcam_data)
                    
                    # Decode and save as image file
                    decoded_image = base64.b64decode(image_data)
                    with open(file_path, "wb") as f:
                        f.write(decoded_image)
                    
                    # For some browsers, we might need to rotate the image based on EXIF data
                    try:
                        with Image.open(file_path) as img:
                            img.save(file_path)
                    except Exception as img_e:
                        logging.warning(f"Error processing webcam image: {img_e}")
                
                # Analyze the image using Gemini AI
                analysis_result = analyze_waste(file_path)
                
                if "error" in analysis_result:
                    flash(f"Analysis error: {analysis_result['error']}", "danger")
                    return render_template("index.html")
                
                # Create a new waste item record in the database with additional fields
                waste_item = WasteItem(
                    image_path=file_path.replace("static/", ""),
                    is_recyclable=analysis_result["is_recyclable"],
                    is_ewaste=analysis_result["is_ewaste"],
                    material=analysis_result["material"],
                    summary=analysis_result.get("summary", ""),
                    full_analysis=analysis_result["full_analysis"],
                    recycling_instructions=analysis_result.get("recycling_instructions", ""),
                    environmental_impact=analysis_result.get("environmental_impact", ""),
                    disposal_recommendations=analysis_result.get("disposal_recommendations", "")
                )
                
                # Add material detection results if available
                if "material_detection" in analysis_result:
                    waste_item.material_detection = analysis_result["material_detection"]
                db.session.add(waste_item)
                db.session.commit()
                
                # Store the waste item ID in session for listing form
                session["last_analyzed_item_id"] = waste_item.id
                
                # Set display paths
                image_path = "/" + file_path
                result = analysis_result
                
            except Exception as e:
                logging.error(f"Error processing image: {e}")
                flash(f"Error processing image: {str(e)}", "danger")
        
        return render_template("index.html", result=result, image_path=image_path, waste_item=waste_item)
    
    @app.route("/marketplace")
    def marketplace():
        """Display marketplace listings"""
        items = WasteItem.query.filter_by(is_listed=True).order_by(WasteItem.created_at.desc()).all()
        return render_template("marketplace.html", items=items)
    
    @app.route("/municipality")
    def municipality():
        """Display items routed to municipality"""
        items = WasteItem.query.filter_by(sent_to_municipality=True).order_by(WasteItem.created_at.desc()).all()
        return render_template("municipality.html", items=items)
    
    @app.route("/item/<int:item_id>")
    def item_details(item_id):
        """Display details for a specific item"""
        item = WasteItem.query.get_or_404(item_id)
        return render_template("item_details.html", item=item)
    
    @app.route("/list-item", methods=["GET", "POST"])
    def list_item():
        """Handle marketplace listing form"""
        if "last_analyzed_item_id" not in session:
            flash("No recently analyzed item to list", "warning")
            return redirect(url_for("index"))
        
        item_id = session["last_analyzed_item_id"]
        item = WasteItem.query.get_or_404(item_id)
        
        if request.method == "POST":
            item.title = request.form.get("title")
            item.description = request.form.get("description")
            item.contact_email = request.form.get("contact_email")
            item.contact_phone = request.form.get("contact_phone")
            item.location = request.form.get("location")
            item.is_listed = True
            
            # If item is plastic, automatically route to municipality
            if item.material.lower() == "plastic":
                item.sent_to_municipality = True
                item.municipality_status = "Pending"
                flash("This plastic item has been automatically sent to the municipality", "info")
            
            db.session.commit()
            flash("Item listed successfully", "success")
            
            # Clear the session variable
            session.pop("last_analyzed_item_id", None)
            
            return redirect(url_for("marketplace"))
        
        return render_template("listing_form.html", item=item)
    
    @app.route("/send-to-municipality/<int:item_id>", methods=["POST"])
    def send_to_municipality(item_id):
        """Route an item to municipality and award rewards for contributing to recycling"""
        item = WasteItem.query.get_or_404(item_id)
        item.sent_to_municipality = True
        item.municipality_status = "Pending"
        db.session.commit()
        
        # Award points to the logged-in user if authenticated
        if current_user.is_authenticated:
            try:
                # Give rewards based on material type
                points = 0
                reward_desc = ""
                
                if item.material.lower() == 'plastic':
                    points = 100
                    reward_desc = "Sending plastic waste for municipal recycling"
                elif item.material.lower() == 'paper':
                    points = 75
                    reward_desc = "Sending paper waste for municipal recycling"
                elif item.material.lower() == 'glass':
                    points = 90
                    reward_desc = "Sending glass waste for municipal recycling"
                elif item.material.lower() == 'metal':
                    points = 120
                    reward_desc = "Sending metal waste for municipal recycling"
                elif item.material.lower() == 'electronic':
                    points = 150
                    reward_desc = "Properly disposing of electronic waste"
                else:
                    points = 50
                    reward_desc = "Sending waste for municipal recycling"
                
                # Create a reward record
                from models import Reward
                reward = Reward(
                    user_id=current_user.id,
                    points=points,
                    description=reward_desc,
                    reward_type="municipality"
                )
                db.session.add(reward)
                
                # Update user's eco points
                current_user.eco_points += points
                db.session.commit()
                
                # Check if the user has earned any achievements
                check_achievements(current_user.id)
                
                flash(f"Item sent to municipality successfully! You earned {points} eco-points.", "success")
            except Exception as e:
                logging.error(f"Error awarding points: {e}")
                flash("Item sent to municipality successfully, but there was an error awarding points.", "warning")
        else:
            flash("Item sent to municipality successfully. Log in to earn eco-points for your contributions!", "info")
            
        return redirect(url_for("item_details", item_id=item_id))
    
    @app.route("/update-municipality-status/<int:item_id>", methods=["POST"])
    def update_municipality_status(item_id):
        """Update municipality status (for demo purposes)"""
        item = WasteItem.query.get_or_404(item_id)
        status = request.form.get("status")
        if status in ["Pending", "Accepted", "Rejected"]:
            item.municipality_status = status
            db.session.commit()
            flash(f"Status updated to {status}", "success")
        return redirect(url_for("municipality"))
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("error.html", error="Page not found"), 404
    
    @app.route("/drop-points")
    def drop_points():
        """Display map with waste drop points in Bangalore"""
        # Predefined drop points in Bangalore
        drop_points = [
            {
                "name": "Dry Waste Collection Center - Koramangala",
                "lat": 12.9352,
                "lon": 77.6245,
                "address": "Koramangala 3rd Block, Bengaluru",
                "types": ["Plastic", "Paper", "Glass"]
            },
            {
                "name": "E-Waste Collection Center - Indiranagar",
                "lat": 12.9784,
                "lon": 77.6408,
                "address": "100 Feet Road, Indiranagar, Bengaluru",
                "types": ["E-Waste", "Batteries"]
            },
            {
                "name": "Saahas Zero Waste - HSR Layout",
                "lat": 12.9116,
                "lon": 77.6473,
                "address": "HSR Layout, Bengaluru",
                "types": ["Plastic", "Paper", "Organic"]
            },
            {
                "name": "ITC WOW Collection Point - Whitefield",
                "lat": 12.9698,
                "lon": 77.7500,
                "address": "Whitefield, Bengaluru",
                "types": ["Paper", "Cardboard"]
            },
            {
                "name": "BBMP Recycling Center - Jayanagar",
                "lat": 12.9250,
                "lon": 77.5938,
                "address": "Jayanagar 4th Block, Bengaluru",
                "types": ["Plastic", "Metal", "Glass", "Paper"]
            }
        ]
        return render_template("drop_points.html", drop_points=drop_points)

    @app.route("/check-in-drop-point", methods=["POST"])
    @login_required
    def check_in_drop_point():
        """Handle user check-ins at drop points"""
        if not current_user.is_authenticated:
            flash("You must be logged in to check in at a drop point", "warning")
            return redirect(url_for("auth.login"))
        
        drop_location_id = request.form.get("drop_location_id")
        waste_type = request.form.get("waste_type")
        notes = request.form.get("notes", "")
        
        if not drop_location_id or not waste_type:
            flash("Missing required information for check-in", "danger")
            return redirect(url_for("drop_points"))
        
        try:
            # Create a new waste item for the drop-off
            waste_item = WasteItem(
                user_id=current_user.id,
                material=waste_type,
                is_dropped_off=True,
                drop_location_id=drop_location_id,
                drop_date=datetime.utcnow(),
                description=notes,
                is_recyclable=True  # Assuming items being dropped off are recyclable
            )
            db.session.add(waste_item)
            db.session.commit()
            
            # Award points for the drop-off
            award_points_for_drop_off(current_user.id, waste_item.id, drop_location_id)
            
            # Check if user has earned any achievements
            check_achievements(current_user.id)
            
            flash("Thank you for your check-in! You've been awarded eco-points for your contribution.", "success")
            
        except Exception as e:
            logging.error(f"Error processing check-in: {e}")
            db.session.rollback()
            flash("Error processing your check-in. Please try again.", "danger")
            
        return redirect(url_for("drop_points"))
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", error="Server error"), 500
        
    # Register routes for our new features
    register_tracking_routes(app)
    register_infrastructure_routes(app)
