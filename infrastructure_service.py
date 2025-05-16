"""
Infrastructure reporting system for WasteWorks.
This module handles the creation and management of infrastructure reports.
"""

import os
from datetime import datetime
from models import InfrastructureReport, User
from app import db
from werkzeug.utils import secure_filename

# Define infrastructure categories
INFRASTRUCTURE_CATEGORIES = {
    'road': 'Roads and Highways',
    'footpath': 'Footpaths and Sidewalks',
    'street_light': 'Street Lights',
    'traffic_signal': 'Traffic Signals',
    'garbage_bin': 'Garbage Bins',
    'drainage': 'Drainage System',
    'water_pipe': 'Water Supply',
    'public_toilet': 'Public Toilets',
    'park': 'Parks and Recreation Areas',
    'bus_stop': 'Bus Stops and Shelters',
    'other': 'Other Infrastructure'
}

# Define severity levels
SEVERITY_LEVELS = {
    'low': {
        'name': 'Low',
        'description': 'Minor issue, not causing significant problems',
        'color': 'info'
    },
    'medium': {
        'name': 'Medium',
        'description': 'Moderate issue, causing some inconvenience',
        'color': 'warning'
    },
    'high': {
        'name': 'High',
        'description': 'Serious issue, requiring prompt attention',
        'color': 'danger'
    },
    'critical': {
        'name': 'Critical',
        'description': 'Immediate safety hazard, requires urgent action',
        'color': 'dark'
    }
}

# Define status types
STATUS_TYPES = {
    'pending': {
        'name': 'Pending',
        'description': 'Report received, awaiting review',
        'color': 'secondary'
    },
    'under_review': {
        'name': 'Under Review',
        'description': 'Report is being reviewed by authorities',
        'color': 'info'
    },
    'in_progress': {
        'name': 'In Progress',
        'description': 'Repair work has started',
        'color': 'primary'
    },
    'resolved': {
        'name': 'Resolved',
        'description': 'Issue has been fixed',
        'color': 'success'
    },
    'rejected': {
        'name': 'Rejected',
        'description': 'Report rejected or cannot be addressed',
        'color': 'danger'
    }
}

def get_infrastructure_categories():
    """
    Get available infrastructure categories.
    
    Returns:
        Dictionary of category codes and names
    """
    return INFRASTRUCTURE_CATEGORIES

def get_severity_levels():
    """
    Get available severity levels with metadata.
    
    Returns:
        Dictionary of severity levels with metadata
    """
    return SEVERITY_LEVELS

def get_status_types():
    """
    Get available status types with metadata.
    
    Returns:
        Dictionary of status types with metadata
    """
    return STATUS_TYPES

def save_infrastructure_image(image_file, report_id):
    """
    Save uploaded infrastructure image to filesystem.
    
    Args:
        image_file: Uploaded file object
        report_id: ID of the infrastructure report
        
    Returns:
        Path where the image was saved
    """
    # Ensure directory exists
    upload_dir = os.path.join('static', 'uploads', 'infrastructure')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create unique filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = secure_filename(f"infra_{report_id}_{timestamp}_{image_file.filename}")
    
    # Save the file
    file_path = os.path.join(upload_dir, filename)
    image_file.save(file_path)
    
    # Return the relative path for database storage
    return os.path.join('uploads', 'infrastructure', filename)

def create_infrastructure_report(user_id, title, description, category, severity, 
                                location_description, latitude, longitude, image_file):
    """
    Create a new infrastructure report.
    
    Args:
        user_id: ID of the reporting user
        title: Title of the report
        description: Detailed description of the issue
        category: Type of infrastructure affected
        severity: Severity level of the issue
        location_description: Text description of the location
        latitude: GPS latitude (optional)
        longitude: GPS longitude (optional)
        image_file: Uploaded image file
        
    Returns:
        Newly created InfrastructureReport
    """
    # Create a placeholder report to get an ID
    new_report = InfrastructureReport(
        user_id=user_id,
        title=title,
        description=description,
        category=category,
        severity=severity,
        location_description=location_description,
        latitude=latitude,
        longitude=longitude,
        image_path='',  # Placeholder, will update after saving the image
        status='pending'
    )
    
    # Save to get an ID
    db.session.add(new_report)
    db.session.flush()
    
    # Save the image and update the path
    if image_file:
        image_path = save_infrastructure_image(image_file, new_report.id)
        new_report.image_path = image_path
    
    # Commit to database
    db.session.commit()
    
    # Award points to the user for reporting (gamification)
    user = User.query.get(user_id)
    if user:
        user.eco_points += 20  # Award points for civic engagement
        db.session.commit()
    
    return new_report

def update_report_status(report_id, status, municipality_notes=None):
    """
    Update the status of an infrastructure report.
    
    Args:
        report_id: ID of the report to update
        status: New status value
        municipality_notes: Optional notes from municipality
        
    Returns:
        Updated InfrastructureReport or None if not found
    """
    report = InfrastructureReport.query.get(report_id)
    
    if not report:
        return None
    
    report.status = status
    report.status_updated_at = datetime.utcnow()
    
    if municipality_notes:
        report.municipality_notes = municipality_notes
    
    db.session.commit()
    
    # If resolved, award additional points to the reporter
    if status == 'resolved':
        user = User.query.get(report.user_id)
        if user:
            user.eco_points += 30  # Bonus for resolved reports
            db.session.commit()
    
    return report

def get_user_reports(user_id):
    """
    Get all infrastructure reports submitted by a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of InfrastructureReport objects
    """
    return InfrastructureReport.query.filter_by(user_id=user_id).order_by(
        InfrastructureReport.reported_at.desc()
    ).all()

def get_reports_by_category(category):
    """
    Get infrastructure reports filtered by category.
    
    Args:
        category: Infrastructure category to filter by
        
    Returns:
        List of InfrastructureReport objects
    """
    return InfrastructureReport.query.filter_by(category=category).order_by(
        InfrastructureReport.reported_at.desc()
    ).all()

def get_reports_by_status(status):
    """
    Get infrastructure reports filtered by status.
    
    Args:
        status: Status to filter by
        
    Returns:
        List of InfrastructureReport objects
    """
    return InfrastructureReport.query.filter_by(status=status).order_by(
        InfrastructureReport.reported_at.desc()
    ).all()

def get_reports_near_location(latitude, longitude, radius_km=5):
    """
    Get infrastructure reports near a specific location.
    
    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius_km: Search radius in kilometers
        
    Returns:
        List of InfrastructureReport objects
    """
    # This is a simplified version - in production you would use
    # proper geospatial queries with PostGIS or similar
    reports = InfrastructureReport.query.filter(
        InfrastructureReport.latitude.isnot(None),
        InfrastructureReport.longitude.isnot(None)
    ).all()
    
    # Filter reports within radius (simplified calculation)
    # In production, use proper geospatial distance calculation
    nearby_reports = []
    for report in reports:
        # Simple approximation: 1 degree ≈ 111km
        lat_diff = abs(report.latitude - latitude)
        lng_diff = abs(report.longitude - longitude)
        
        # Rough distance calculation (not accounting for earth's curvature)
        approx_distance = ((lat_diff * 111) ** 2 + (lng_diff * 111) ** 2) ** 0.5
        
        if approx_distance <= radius_km:
            nearby_reports.append(report)
    
    return nearby_reports