"""
Rewards and gamification system for WasteWorks.
"""

from datetime import datetime, timedelta
from flask_login import current_user
from app import db
from models import User, WasteItem, Achievement, UserAchievement, Reward, DropLocation

def award_points(user_id, points, description, reward_type):
    """
    Award points to a user and create a reward record
    
    Args:
        user_id: ID of the user to award points to
        points: Number of points to award
        description: Description of why points were awarded
        reward_type: Type of reward (drop_off, listing, achievement)
    """
    if not user_id:
        return None
        
    user = User.query.get(user_id)
    if not user:
        return None
        
    # Create a reward record
    reward = Reward(
        user_id=user_id,
        points=points,
        description=description,
        reward_type=reward_type
    )
    
    # Add points to user
    user.eco_points += points
    
    # Update streak if applicable
    _update_recycling_streak(user)
    
    # Save changes
    db.session.add(reward)
    db.session.commit()
    
    # Check for new achievements
    check_achievements(user_id)
    
    return reward

def award_points_for_drop_off(user_id, waste_item_id, drop_location_id):
    """
    Award points when a user drops off a waste item at a drop location
    
    Args:
        user_id: ID of the user
        waste_item_id: ID of the waste item
        drop_location_id: ID of the drop location
    """
    if not user_id:
        return None
        
    waste_item = WasteItem.query.get(waste_item_id)
    drop_location = DropLocation.query.get(drop_location_id)
    
    if not waste_item or not drop_location:
        return None
    
    # Mark the item as dropped off
    waste_item.is_dropped_off = True
    waste_item.drop_location_id = drop_location_id
    waste_item.drop_date = datetime.utcnow()
    
    # Calculate points based on item type
    points = 10  # Base points
    
    # Bonus points for recyclable items
    if waste_item.is_recyclable:
        points += 5
    
    # Bonus points for e-waste
    if waste_item.is_ewaste:
        points += 10
    
    description = f"Dropped off {waste_item.material} item at {drop_location.name}"
    return award_points(user_id, points, description, "drop_off")

def award_points_for_listing(user_id, waste_item_id):
    """
    Award points when a user lists an item in the marketplace
    
    Args:
        user_id: ID of the user
        waste_item_id: ID of the waste item
    """
    if not user_id:
        return None
        
    waste_item = WasteItem.query.get(waste_item_id)
    
    if not waste_item:
        return None
        
    points = 5  # Base points for listing
    description = f"Listed {waste_item.material} item in marketplace"
    
    return award_points(user_id, points, description, "listing")

def check_achievements(user_id):
    """
    Check and award any achievements the user has earned
    
    Args:
        user_id: ID of the user to check achievements for
    """
    if not user_id:
        return None
        
    user = User.query.get(user_id)
    if not user:
        return None
    
    # Get all available achievements
    achievements = Achievement.query.all()
    earned_achievements = []
    
    for achievement in achievements:
        # Skip if user already has this achievement
        existing = UserAchievement.query.filter_by(
            user_id=user_id, 
            achievement_id=achievement.id
        ).first()
        
        if existing:
            continue
        
        # Check if user meets criteria for achievement
        is_earned = False
        
        # Achievement: Recycle Rookie (first recycled item)
        if achievement.name == "Recycle Rookie" and achievement.required_items == 1:
            item_count = WasteItem.query.filter_by(
                user_id=user_id,
                is_recyclable=True
            ).count()
            
            is_earned = item_count >= 1
        
        # Achievement: Plastic Hero (5 plastic items)
        elif achievement.name == "Plastic Hero" and achievement.required_material == "Plastic":
            plastic_items = WasteItem.query.filter_by(
                user_id=user_id,
                material="Plastic"
            ).count()
            
            is_earned = plastic_items >= achievement.required_items
        
        # Achievement: E-Waste Warrior (3 e-waste items)
        elif achievement.name == "E-Waste Warrior" and achievement.required_material == "Electronic":
            ewaste_items = WasteItem.query.filter_by(
                user_id=user_id,
                is_ewaste=True
            ).count()
            
            is_earned = ewaste_items >= achievement.required_items
        
        # Achievement: Marketplace Maven (3 listings)
        elif achievement.name == "Marketplace Maven":
            listings = WasteItem.query.filter_by(
                user_id=user_id,
                is_listed=True
            ).count()
            
            is_earned = listings >= achievement.required_items
        
        # Achievement: Community Champion (7-day streak)
        elif achievement.name == "Community Champion":
            is_earned = user.recycling_streak >= 7
        
        # Award the achievement if earned
        if is_earned:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id
            )
            
            db.session.add(user_achievement)
            earned_achievements.append(achievement)
            
            # Award points for the achievement
            award_points(
                user_id,
                achievement.points_awarded,
                f"Earned achievement: {achievement.name}",
                "achievement"
            )
    
    db.session.commit()
    return earned_achievements

def _update_recycling_streak(user):
    """
    Update the user's recycling streak
    
    Args:
        user: User model instance
    """
    today = datetime.utcnow().date()
    last_activity = user.last_activity_date.date() if user.last_activity_date else None
    
    if not last_activity or (today - last_activity) > timedelta(days=1):
        # Reset streak if more than 1 day has passed
        user.recycling_streak = 1
    elif today > last_activity:
        # Increment streak if active on a new day
        user.recycling_streak += 1
    
    # Update last activity date
    user.last_activity_date = datetime.utcnow()

def get_user_stats(user_id):
    """
    Get a summary of user statistics for display
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with user statistics
    """
    if not user_id:
        return None
        
    user = User.query.get(user_id)
    if not user:
        return None
    
    # Count items by type
    total_items = WasteItem.query.filter_by(user_id=user_id).count()
    recyclable_items = WasteItem.query.filter_by(user_id=user_id, is_recyclable=True).count()
    ewaste_items = WasteItem.query.filter_by(user_id=user_id, is_ewaste=True).count()
    listed_items = WasteItem.query.filter_by(user_id=user_id, is_listed=True).count()
    
    # Get achievements
    achievements = UserAchievement.query.filter_by(user_id=user_id).all()
    achievement_count = len(achievements)
    
    # Get rewards
    total_points = user.eco_points
    rewards = Reward.query.filter_by(user_id=user_id).order_by(Reward.created_at.desc()).limit(5).all()
    
    return {
        "total_items": total_items,
        "recyclable_items": recyclable_items,
        "ewaste_items": ewaste_items,
        "listed_items": listed_items,
        "achievement_count": achievement_count,
        "achievements": achievements,
        "recycling_streak": user.recycling_streak,
        "total_points": total_points,
        "recent_rewards": rewards
    }