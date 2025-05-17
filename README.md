# WasteWorks

A cutting-edge waste management platform that transforms recycling into an engaging, rewarding experience through advanced technologies and user-centric design.

## 🌟 Key Features

- **AI-powered Material Identification**: Upload images of waste items to receive detailed analysis on recyclability, material composition, and proper disposal methods
- **Blockchain-enabled Waste Tracking**: Monitor waste items from drop-off to recycling completion with a secure, transparent tracking system
- **Smart Recycling Guidance**: Get personalized instructions on how to properly prepare and recycle different types of materials
- **Interactive Drop-off Map**: Find nearby recycling centers and drop-off points with an interactive map
- **Infrastructure Reporting**: Report damaged waste management infrastructure through webcam photos
- **Community Marketplace**: List recyclable items for reuse in the community marketplace
- **Municipality Integration**: Direct routing of recyclable materials to municipal collection services
- **Gamification & Rewards**: Earn eco-points and achievements for responsible waste management

## 🛠️ Technical Stack

- **Backend**: Flask (Python 3.11)
- **Database**: PostgreSQL
- **AI/ML**: Google Gemini API, OpenCV, scikit-learn
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Authentication**: Flask-Login, Flask-Bcrypt
- **Forms**: Flask-WTF, WTForms
- **Image Processing**: Pillow, OpenCV
- **Geospatial**: OpenLayers for maps

## 🚀 Getting Started

### Prerequisites

- Python 3.9+ (3.11 recommended)
- PostgreSQL
- pip (Python package manager)

### Local Development Setup

#### 1. Clone the repository
```bash
git clone https://github.com/yourusername/wasteworks.git
cd wasteworks
```

#### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

#### 3. Install dependencies
```bash
pip install -r dependencies.txt
```

#### 4. Set up PostgreSQL
- Install PostgreSQL if you haven't already
- Create a new database:
  ```bash
  createdb wasteworks
  ```
- Or use the included setup script:
  ```bash
  chmod +x setup_database.sh
  ./setup_database.sh
  ```

#### 5. Configure environment variables
Create a `.env` file in the project root with the following variables:
```
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/wasteworks

# Flask Configuration
SESSION_SECRET=your_random_secret_key
FLASK_ENV=development
PYTHONUNBUFFERED=true

# Optional: AI API Keys
# OPENAI_API_KEY=your_openai_api_key
# ANTHROPIC_API_KEY=your_anthropic_api_key
```

#### 6. Initialize the database
```bash
python recreate_db.py
```

#### 7. Run the application
```bash
python main.py
```
The application will be available at http://localhost:5000

### Using Docker (Alternative)

If you prefer using Docker:

```bash
# Build the Docker image
docker build -t wasteworks .

# Run the container
docker run -p 5000:5000 --env-file .env wasteworks
```

## 🗃️ Database Schema

The application uses several related models:

- **User**: Authentication, profile, and gamification data
- **WasteItem**: Uploaded waste items with AI analysis results
- **DropLocation**: Recycling centers and drop-off points
- **WasteJourneyBlock**: Blockchain-like tracking for waste journey
- **Achievement**: Gamification achievements and badges
- **Reward**: Points and rewards for user actions
- **InfrastructureReport**: Citizen reports of damaged infrastructure

## 📊 API Endpoints

The application provides the following main routes:

- `/`: Home page and waste item upload/analysis
- `/auth/register`: User registration
- `/auth/login`: User login
- `/auth/profile`: User profile and statistics
- `/marketplace`: Community marketplace for recyclable items
- `/municipality`: Items routed to municipal collection
- `/drop-points`: Map of recycling drop-off locations
- `/tracking`: Blockchain-based waste journey tracking
- `/infrastructure`: Infrastructure reporting system

## 🚀 Deployment

### Deploy to Render.com

This application is configured for easy deployment on Render.com:

1. Fork or clone this repository to your GitHub account
2. Sign up for Render.com and connect your GitHub account
3. Create a new Web Service and select your repository
4. Use the following settings:
   - Environment: Python
   - Build Command: `pip install -r requirements-render.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers=2 main:app`

5. Add the following environment variables:
   - `SESSION_SECRET`: Generate a secure random string
   - `FLASK_ENV`: production
   - `PYTHONUNBUFFERED`: true
   - `PYTHON_VERSION`: 3.11.8

6. Create a PostgreSQL database in Render:
   - Go to Dashboard → New → PostgreSQL
   - Link it to your web service (Render will automatically set the DATABASE_URL environment variable)

7. Deploy your application
   - The application will automatically set up the database schema during the first deployment
   - If needed, you can run database migrations through the Render shell

### Database Management

For database schema updates after deployment:

```bash
# For adding new columns to existing tables:
python update_db.py

# For completely resetting the database (warning: all data will be lost):
python recreate_db.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open issues for bugs and feature requests.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

Project Link: [https://github.com/yourusername/wasteworks](https://github.com/tether007/wasteworks)
