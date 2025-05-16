"""
Blockchain-like waste tracking system service for WasteWorks.
This module manages the creation and validation of waste journey blocks.
"""

from models import WasteJourneyBlock, WasteItem
from app import db
from datetime import datetime

# Define the journey stages and their descriptions
JOURNEY_STAGES = {
    'drop_off': {
        'name': 'Drop Off',
        'description': 'Waste item dropped off at collection point',
        'icon': 'droplet'
    },
    'collection': {
        'name': 'Collection',
        'description': 'Waste collected from drop-off location',
        'icon': 'truck'
    },
    'sorting': {
        'name': 'Sorting',
        'description': 'Waste sorted by material type',
        'icon': 'filter'
    },
    'processing': {
        'name': 'Processing',
        'description': 'Materials processed for recycling',
        'icon': 'repeat'
    },
    'recycling': {
        'name': 'Recycling',
        'description': 'Materials converted into new products',
        'icon': 'refresh-cw'
    },
    'completed': {
        'name': 'Completed',
        'description': 'Recycling process completed',
        'icon': 'check-circle'
    }
}

def get_journey_stages():
    """
    Return the defined journey stages with metadata.
    
    Returns:
        Dictionary of journey stages with metadata
    """
    return JOURNEY_STAGES

def create_journey_block(waste_item_id, stage, location, details, verified_by):
    """
    Create a new block in the waste item's journey.
    
    Args:
        waste_item_id: ID of the waste item
        stage: Current stage of the journey (e.g., 'drop_off', 'collection')
        location: Location where this stage occurred
        details: Additional details about this stage
        verified_by: Name or ID of entity verifying this stage
        
    Returns:
        Newly created WasteJourneyBlock
    """
    # Get the previous block for this waste item, if any
    previous_block = WasteJourneyBlock.query.filter_by(
        waste_item_id=waste_item_id
    ).order_by(WasteJourneyBlock.timestamp.desc()).first()
    
    previous_hash = previous_block.block_hash if previous_block else None
    
    # Create the new block
    new_block = WasteJourneyBlock(
        waste_item_id=waste_item_id,
        stage=stage,
        location=location,
        details=details,
        verified_by=verified_by,
        previous_hash=previous_hash
    )
    
    # Mine the block (simulate proof of work)
    new_block.mine_block(difficulty=2)
    
    # Save to database
    db.session.add(new_block)
    db.session.commit()
    
    # Update the waste item status if this is the final stage
    if stage == 'completed':
        waste_item = WasteItem.query.get(waste_item_id)
        if waste_item:
            waste_item.recycling_completed = True
            waste_item.recycling_completion_date = datetime.utcnow()
            db.session.commit()
    
    return new_block

def get_waste_journey(waste_item_id):
    """
    Get the complete journey of a waste item.
    
    Args:
        waste_item_id: ID of the waste item
        
    Returns:
        List of journey blocks in chronological order
    """
    blocks = WasteJourneyBlock.query.filter_by(
        waste_item_id=waste_item_id
    ).order_by(WasteJourneyBlock.timestamp).all()
    
    return blocks

def verify_journey_integrity(waste_item_id):
    """
    Verify the integrity of the waste journey blockchain.
    
    Args:
        waste_item_id: ID of the waste item
        
    Returns:
        True if all blocks are valid and linked correctly, False otherwise
    """
    blocks = get_waste_journey(waste_item_id)
    
    if not blocks:
        return True  # No blocks yet, so integrity is intact
    
    # Check each block
    for i in range(len(blocks)):
        current_block = blocks[i]
        
        # Verify the block's hash
        if not current_block.is_valid():
            return False
        
        # Check link to previous block
        if i > 0:
            previous_block = blocks[i-1]
            if current_block.previous_hash != previous_block.block_hash:
                return False
    
    return True

def generate_qr_code_data(waste_item_id):
    """
    Generate data for QR code to track waste item.
    
    Args:
        waste_item_id: ID of the waste item
        
    Returns:
        Dictionary with waste tracking data
    """
    waste_item = WasteItem.query.get(waste_item_id)
    
    if not waste_item:
        return None
    
    # Get the latest block
    latest_block = WasteJourneyBlock.query.filter_by(
        waste_item_id=waste_item_id
    ).order_by(WasteJourneyBlock.timestamp.desc()).first()
    
    # Prepare data for QR code
    qr_data = {
        'waste_item_id': waste_item_id,
        'material': waste_item.material,
        'is_recyclable': waste_item.is_recyclable,
        'drop_date': waste_item.drop_date.isoformat() if waste_item.drop_date else None,
        'current_stage': latest_block.stage if latest_block else 'not_started',
        'verification_url': f"/waste/verify/{waste_item_id}"
    }
    
    return qr_data

def get_journey_progress(waste_item_id):
    """
    Calculate the progress percentage of the waste journey.
    
    Args:
        waste_item_id: ID of the waste item
        
    Returns:
        Dictionary with progress details
    """
    blocks = get_waste_journey(waste_item_id)
    stages_completed = len(blocks)
    total_stages = len(JOURNEY_STAGES)
    
    # Get the current stage
    current_stage = blocks[-1].stage if blocks else None
    
    # Calculate progress percentage
    progress_pct = int((stages_completed / total_stages) * 100) if total_stages > 0 else 0
    
    return {
        'current_stage': current_stage,
        'stages_completed': stages_completed,
        'total_stages': total_stages,
        'progress_pct': progress_pct,
        'blocks': blocks
    }