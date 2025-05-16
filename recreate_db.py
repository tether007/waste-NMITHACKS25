from app import app, db
import logging
from models import Achievement, DropLocation

print("Starting database recreation...")
logging.basicConfig(level=logging.INFO)

with app.app_context():
    logging.info("Dropping all tables...")
    db.drop_all()
    
    logging.info("Creating all tables...")
    db.create_all()
    
    logging.info("Adding initial achievements...")
    achievements = [
        Achievement(
            name="Recycle Rookie",
            description="Recycle your first item",
            badge_image="static/badges/rookie.svg",
            points_awarded=50,
            required_items=1
        ),
        Achievement(
            name="Plastic Hero",
            description="Recycle 5 plastic items",
            badge_image="static/badges/plastic_hero.svg", 
            points_awarded=100,
            required_items=5,
            required_material="Plastic"
        ),
        Achievement(
            name="E-Waste Warrior",
            description="Recycle 3 electronic waste items",
            badge_image="static/badges/ewaste_warrior.svg",
            points_awarded=150,
            required_items=3,
            required_material="Electronic"
        ),
        Achievement(
            name="Marketplace Maven",
            description="List 3 items on the marketplace",
            badge_image="static/badges/marketplace.svg",
            points_awarded=75,
            required_items=3
        ),
        Achievement(
            name="Community Champion",
            description="Maintain a 7-day recycling streak",
            badge_image="static/badges/champion.svg",
            points_awarded=200
        )
    ]
    
    db.session.add_all(achievements)
    
    logging.info("Adding drop locations...")
    drop_locations = [
        DropLocation(
            name="Dry Waste Collection Center - Koramangala",
            address="Koramangala 3rd Block, Bengaluru",
            latitude=12.9352,
            longitude=77.6245,
            accepted_materials="Plastic,Paper,Glass"
        ),
        DropLocation(
            name="E-Waste Collection Center - Indiranagar",
            address="100 Feet Road, Indiranagar, Bengaluru",
            latitude=12.9784,
            longitude=77.6408,
            accepted_materials="Electronic,Batteries"
        ),
        DropLocation(
            name="Saahas Zero Waste - HSR Layout",
            address="HSR Layout, Bengaluru",
            latitude=12.9116,
            longitude=77.6473,
            accepted_materials="Plastic,Paper,Organic"
        ),
        DropLocation(
            name="ITC WOW Collection Point - Whitefield",
            address="Whitefield, Bengaluru",
            latitude=12.9698,
            longitude=77.7500, 
            accepted_materials="Paper,Cardboard"
        ),
        DropLocation(
            name="BBMP Recycling Center - Jayanagar",
            address="Jayanagar 4th Block, Bengaluru",
            latitude=12.9250,
            longitude=77.5938,
            accepted_materials="Plastic,Metal,Glass,Paper"
        )
    ]
    
    db.session.add_all(drop_locations)
    db.session.commit()
    
    logging.info("Database recreation complete!")