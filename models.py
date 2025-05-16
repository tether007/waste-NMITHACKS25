from datetime import datetime
import hashlib
import json
from app import db, bcrypt
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    full_name = db.Column(db.String(120))
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User status and scores
    is_active = db.Column(db.Boolean, default=True)
    eco_points = db.Column(db.Integer, default=0)
    recycling_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    waste_items = db.relationship('WasteItem', backref='user', lazy=True)
    rewards = db.relationship('Reward', backref='user', lazy=True)
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def award_points(self, points):
        self.eco_points += points
        db.session.commit()
    
    def __repr__(self):
        return f"<User {self.username}>"


class WasteItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(255), nullable=False)
    is_recyclable = db.Column(db.Boolean, default=False)
    is_ewaste = db.Column(db.Boolean, default=False)
    material = db.Column(db.String(100))
    full_analysis = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # User relationship
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Additional analysis fields
    summary = db.Column(db.Text)
    recycling_instructions = db.Column(db.Text)
    environmental_impact = db.Column(db.Text)
    disposal_recommendations = db.Column(db.Text)
    
    # Material detection results (stored as JSON string)
    _material_detection = db.Column('material_detection', db.Text, nullable=True)
    
    # Fields for marketplace listings
    is_listed = db.Column(db.Boolean, default=False)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    location = db.Column(db.String(200))
    
    # Municipality routing
    sent_to_municipality = db.Column(db.Boolean, default=False)
    municipality_status = db.Column(db.String(50), default="Not Sent")  # Not Sent, Pending, Accepted, Rejected
    
    # Drop-off tracking
    is_dropped_off = db.Column(db.Boolean, default=False)
    drop_location_id = db.Column(db.Integer, db.ForeignKey('drop_location.id'), nullable=True)
    drop_date = db.Column(db.DateTime, nullable=True)
    
    # Blockchain-like journey tracking
    recycling_completed = db.Column(db.Boolean, default=False)
    recycling_completion_date = db.Column(db.DateTime, nullable=True)
    
    @property
    def material_detection(self):
        """Getter: Deserialize JSON string to Python dictionary"""
        if self._material_detection:
            return json.loads(self._material_detection)
        return None
    
    @material_detection.setter
    def material_detection(self, value):
        """Setter: Serialize Python dictionary to JSON string"""
        if value is not None:
            self._material_detection = json.dumps(value)
        else:
            self._material_detection = None

    def __repr__(self):
        return f"<WasteItem {self.id}: {'Recyclable' if self.is_recyclable else 'Non-Recyclable'}>"


class DropLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accepted_materials = db.Column(db.String(255))  # Comma-separated list of materials
    
    # Relationships
    waste_items = db.relationship('WasteItem', backref='drop_location', lazy=True)
    
    def __repr__(self):
        return f"<DropLocation {self.name}>"


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    badge_image = db.Column(db.String(255))
    points_awarded = db.Column(db.Integer, default=0)
    
    # Achievement requirements
    required_items = db.Column(db.Integer, default=0)  # Number of items required
    required_material = db.Column(db.String(100))  # Specific material type if applicable
    
    # Relationships
    users = db.relationship('UserAchievement', backref='achievement', lazy=True)
    
    def __repr__(self):
        return f"<Achievement {self.name}>"


class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    earned_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserAchievement user_id={self.user_id} achievement_id={self.achievement_id}>"


class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    points = db.Column(db.Integer, default=0)
    description = db.Column(db.String(255), nullable=False)
    reward_type = db.Column(db.String(50), nullable=False)  # 'drop_off', 'listing', 'achievement'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Reward {self.id}: {self.points} points for {self.reward_type}>"


class WasteJourneyBlock(db.Model):
    """
    A block in the blockchain-like waste tracking system.
    Each block represents a stage in the waste item's journey from drop-off to recycling.
    """
    id = db.Column(db.Integer, primary_key=True)
    waste_item_id = db.Column(db.Integer, db.ForeignKey('waste_item.id'), nullable=False)
    
    # Block data
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    stage = db.Column(db.String(50), nullable=False)  # 'drop_off', 'collection', 'sorting', 'processing', 'recycling'
    location = db.Column(db.String(255))
    details = db.Column(db.Text)
    verified_by = db.Column(db.String(100))  # Who verified this stage
    
    # Blockchain properties
    previous_hash = db.Column(db.String(64), nullable=True)  # Hash of the previous block
    block_hash = db.Column(db.String(64), nullable=False)  # Hash of this block
    nonce = db.Column(db.Integer, default=0)  # For proof of work simulation
    
    # Relationships
    waste_item = db.relationship('WasteItem', backref='journey_blocks', lazy=True)
    
    def __init__(self, waste_item_id, stage, location, details, verified_by, previous_hash=None):
        self.waste_item_id = waste_item_id
        self.stage = stage
        self.location = location
        self.details = details
        self.verified_by = verified_by
        self.previous_hash = previous_hash
        self.nonce = 0
        
        # Calculate block hash on creation
        self.block_hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate the hash of this block based on its contents"""
        block_data = {
            'waste_item_id': self.waste_item_id,
            'timestamp': str(self.timestamp),
            'stage': self.stage,
            'location': self.location,
            'details': self.details,
            'verified_by': self.verified_by,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }
        
        # Convert the data to a JSON string and hash it
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty=2):
        """Simulate proof of work by finding a hash with leading zeros"""
        target = '0' * difficulty
        
        while self.block_hash[:difficulty] != target:
            self.nonce += 1
            self.block_hash = self.calculate_hash()
        
        return self.block_hash
    
    def is_valid(self):
        """Verify that the block's hash is valid"""
        return self.block_hash == self.calculate_hash()
    
    def __repr__(self):
        return f"<WasteJourneyBlock {self.id}: {self.stage} for waste_item_id={self.waste_item_id}>"


class InfrastructureReport(db.Model):
    """
    Reports of damaged infrastructure submitted by users through webcam photos.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Report details
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'road', 'street_light', 'water_pipe', 'garbage_bin', etc.
    severity = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    
    # Location details
    location_description = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Image and timestamps
    image_path = db.Column(db.String(255), nullable=False)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # 'pending', 'under_review', 'in_progress', 'resolved', 'rejected'
    status_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    municipality_notes = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('infrastructure_reports', lazy=True))
    
    def __repr__(self):
        return f"<InfrastructureReport {self.id}: {self.title} ({self.status})>"
