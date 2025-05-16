"""
Waste tracking routes for WasteWorks.
Handles the blockchain-like tracking system for waste items.
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import WasteItem, WasteJourneyBlock
from app import db
import blockchain_service

def register_tracking_routes(app):
    """Register waste tracking routes"""

    @app.route('/waste/track/<int:item_id>')
    @login_required
    def track_waste(item_id):
        """
        Display the tracking page for a waste item with blockchain-like journey
        """
        waste_item = WasteItem.query.get_or_404(item_id)
        
        # Check permissions (only owner or admin)
        if waste_item.user_id != current_user.id:
            flash('You do not have permission to view this item', 'danger')
            return redirect(url_for('index'))
        
        # Get waste journey blocks
        journey_blocks = blockchain_service.get_waste_journey(item_id)
        journey_stages = blockchain_service.get_journey_stages()
        
        # Get journey progress
        journey_progress = blockchain_service.get_journey_progress(item_id)
        
        # Verify journey integrity
        is_journey_valid = blockchain_service.verify_journey_integrity(item_id)
        
        # Generate QR code data
        qr_data = blockchain_service.generate_qr_code_data(item_id)
        
        return render_template(
            'waste_tracking.html',
            waste_item=waste_item,
            journey_blocks=journey_blocks,
            journey_stages=journey_stages,
            journey_progress=journey_progress,
            is_journey_valid=is_journey_valid,
            qr_data=qr_data
        )
    
    @app.route('/waste/track/add_stage/<int:item_id>', methods=['POST'])
    @login_required
    def add_journey_stage(item_id):
        """
        Add a new stage to the waste journey (admin or demo only)
        """
        waste_item = WasteItem.query.get_or_404(item_id)
        
        if request.method == 'POST':
            stage = request.form.get('stage')
            location = request.form.get('location')
            details = request.form.get('details')
            verified_by = request.form.get('verified_by', f"User {current_user.id}")
            
            # Create new journey block
            new_block = blockchain_service.create_journey_block(
                waste_item_id=item_id,
                stage=stage,
                location=location,
                details=details,
                verified_by=verified_by
            )
            
            flash('Journey stage added successfully', 'success')
            return redirect(url_for('track_waste', item_id=item_id))
        
        return redirect(url_for('track_waste', item_id=item_id))
    
    @app.route('/waste/verify/<int:item_id>')
    def verify_waste(item_id):
        """
        Public verification page for a waste item (no login required)
        This allows anyone with the QR code to verify the journey
        """
        waste_item = WasteItem.query.get_or_404(item_id)
        
        # Get waste journey blocks
        journey_blocks = blockchain_service.get_waste_journey(item_id)
        journey_stages = blockchain_service.get_journey_stages()
        
        # Verify journey integrity
        is_journey_valid = blockchain_service.verify_journey_integrity(item_id)
        
        # Get journey progress
        journey_progress = blockchain_service.get_journey_progress(item_id)
        
        return render_template(
            'waste_verification.html',
            waste_item=waste_item,
            journey_blocks=journey_blocks,
            journey_stages=journey_stages,
            journey_progress=journey_progress,
            is_journey_valid=is_journey_valid
        )
    
    @app.route('/api/waste/journey/<int:item_id>')
    def api_waste_journey(item_id):
        """
        API endpoint for waste journey data (for ajax calls)
        """
        waste_item = WasteItem.query.get_or_404(item_id)
        
        # Get waste journey blocks
        journey_blocks = blockchain_service.get_waste_journey(item_id)
        journey_stages = blockchain_service.get_journey_stages()
        
        # Format for API response
        blocks_data = []
        for block in journey_blocks:
            blocks_data.append({
                'id': block.id,
                'stage': block.stage,
                'stage_name': journey_stages[block.stage]['name'] if block.stage in journey_stages else block.stage,
                'location': block.location,
                'details': block.details,
                'timestamp': block.timestamp.isoformat(),
                'verified_by': block.verified_by,
                'block_hash': block.block_hash[:10] + '...' + block.block_hash[-10:]  # Truncated for display
            })
        
        return jsonify({
            'waste_item_id': item_id,
            'material': waste_item.material,
            'is_recyclable': waste_item.is_recyclable,
            'blocks': blocks_data,
            'is_valid': blockchain_service.verify_journey_integrity(item_id)
        })