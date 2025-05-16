"""
Infrastructure reporting routes for WasteWorks.
Handles the infrastructure reporting system with webcam uploads.
"""

import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import infrastructure_service
from models import InfrastructureReport

def register_infrastructure_routes(app):
    """Register infrastructure reporting routes"""

    @app.route('/infrastructure/report', methods=['GET', 'POST'])
    @login_required
    def report_infrastructure():
        """
        Display the infrastructure reporting form and handle submissions
        """
        categories = infrastructure_service.get_infrastructure_categories()
        severity_levels = infrastructure_service.get_severity_levels()
        
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            category = request.form.get('category')
            severity = request.form.get('severity')
            location_description = request.form.get('location_description')
            
            # Try to get coordinates
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            
            # Check if we have coordinates
            if latitude and longitude:
                try:
                    latitude = float(latitude)
                    longitude = float(longitude)
                except ValueError:
                    latitude = None
                    longitude = None
            else:
                latitude = None
                longitude = None
            
            # Handle image upload - from webcam or file
            image_data = request.form.get('webcam_image')
            
            if image_data and image_data.startswith('data:image'):
                # Process webcam image
                import base64
                from io import BytesIO
                from PIL import Image
                
                # Extract the image data from the data URL
                image_data = image_data.split(',')[1]
                image_binary = base64.b64decode(image_data)
                
                # Create a file-like object
                image_buffer = BytesIO(image_binary)
                
                # Create a temp file
                upload_dir = os.path.join('static', 'uploads', 'infrastructure')
                os.makedirs(upload_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"webcam_{timestamp}.jpg"
                file_path = os.path.join(upload_dir, filename)
                
                # Save the image
                with Image.open(image_buffer) as img:
                    img.save(file_path)
                
                image_path = os.path.join('uploads', 'infrastructure', filename)
            else:
                # Process uploaded file
                if 'image' not in request.files:
                    flash('No image file provided', 'danger')
                    return redirect(request.url)
                
                image_file = request.files['image']
                
                if image_file.filename == '':
                    flash('No image selected', 'danger')
                    return redirect(request.url)
                
                if image_file:
                    image_path = infrastructure_service.save_infrastructure_image(
                        image_file, 0  # 0 is temporary, will be updated with actual ID
                    )
                else:
                    flash('Error processing image', 'danger')
                    return redirect(request.url)
            
            # Create report
            report = infrastructure_service.create_infrastructure_report(
                user_id=current_user.id,
                title=title,
                description=description,
                category=category,
                severity=severity,
                location_description=location_description,
                latitude=latitude,
                longitude=longitude,
                image_file=None  # Already saved the image
            )
            
            # Update the image path directly
            report.image_path = image_path
            
            flash('Thank you for reporting this infrastructure issue!', 'success')
            return redirect(url_for('view_report', report_id=report.id))
        
        return render_template(
            'report_infrastructure.html',
            categories=categories,
            severity_levels=severity_levels
        )
    
    @app.route('/infrastructure/report/<int:report_id>')
    @login_required
    def view_report(report_id):
        """
        Display a single infrastructure report
        """
        report = InfrastructureReport.query.get_or_404(report_id)
        
        # Check if current user can view this report
        if report.user_id != current_user.id:
            # Still allow viewing but note it's not the user's report
            is_owner = False
        else:
            is_owner = True
        
        categories = infrastructure_service.get_infrastructure_categories()
        severity_levels = infrastructure_service.get_severity_levels()
        status_types = infrastructure_service.get_status_types()
        
        return render_template(
            'view_infrastructure_report.html',
            report=report,
            is_owner=is_owner,
            categories=categories,
            severity_levels=severity_levels,
            status_types=status_types
        )
    
    @app.route('/infrastructure/my-reports')
    @login_required
    def my_infrastructure_reports():
        """
        Display all reports submitted by the current user
        """
        reports = infrastructure_service.get_user_reports(current_user.id)
        
        categories = infrastructure_service.get_infrastructure_categories()
        severity_levels = infrastructure_service.get_severity_levels()
        status_types = infrastructure_service.get_status_types()
        
        return render_template(
            'my_infrastructure_reports.html',
            reports=reports,
            categories=categories,
            severity_levels=severity_levels,
            status_types=status_types
        )
    
    @app.route('/infrastructure/reports/map')
    def infrastructure_map():
        """
        Display a map of all reported infrastructure issues
        """
        # Get all reports with coordinates
        reports = InfrastructureReport.query.filter(
            InfrastructureReport.latitude.isnot(None),
            InfrastructureReport.longitude.isnot(None)
        ).all()
        
        categories = infrastructure_service.get_infrastructure_categories()
        severity_levels = infrastructure_service.get_severity_levels()
        status_types = infrastructure_service.get_status_types()
        
        return render_template(
            'infrastructure_map.html',
            reports=reports,
            categories=categories,
            severity_levels=severity_levels,
            status_types=status_types
        )
    
    @app.route('/infrastructure/update-status/<int:report_id>', methods=['POST'])
    @login_required
    def update_infrastructure_status(report_id):
        """
        Update the status of an infrastructure report (admin only in real app)
        For demo purposes, we allow any user to update
        """
        report = InfrastructureReport.query.get_or_404(report_id)
        
        if request.method == 'POST':
            status = request.form.get('status')
            notes = request.form.get('notes')
            
            infrastructure_service.update_report_status(
                report_id=report_id,
                status=status,
                municipality_notes=notes
            )
            
            flash('Status updated successfully', 'success')
            return redirect(url_for('view_report', report_id=report_id))
        
        return redirect(url_for('view_report', report_id=report_id))