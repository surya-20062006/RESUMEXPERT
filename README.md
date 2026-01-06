# ResumeXpert - AI-Powered Resume Builder

ResumeXpert is a comprehensive Flask-based web application that helps users create, analyze, and optimize their professional resumes using AI technology. The application features modern UI/UX design, resume analysis, template generation, and an AI chatbot assistant.

## 🚀 Features

### 🔐 Authentication System
- Secure user registration and login
- Password hashing with Werkzeug
- Session management
- Form validation with real-time feedback

### 📄 Resume Analysis
- Upload and parse PDF/DOCX resumes
- AI-powered skill extraction
- Experience and education analysis
- Resume scoring and improvement suggestions
- Missing skills identification

### 🎨 Professional Templates
- Multiple modern resume templates
- ATS-friendly designs
- Customizable layouts and colors
- Preview before download
- Export to HTML, PDF, and DOCX formats

### 🤖 AI Chatbot Assistant
- Interactive career guidance
- Resume writing tips
- Interview preparation help
- Skill recommendations
- Real-time chat interface

### 🎨 Modern UI/UX
- Responsive design for all devices
- Dark/light theme toggle
- Smooth animations and transitions
- Drag-and-drop file upload
- Interactive progress bars
- Glass morphism effects

### 📊 Analytics & Insights
- Resume performance scoring
- Skill gap analysis
- Career progression tracking
- Personalized recommendations

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (easily upgradeable to MySQL/PostgreSQL)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **AI Integration**: OpenAI API
- **File Processing**: PyPDF2, python-docx
- **Styling**: Custom CSS with CSS Grid and Flexbox
- **Icons**: Font Awesome 6
- **Fonts**: Google Fonts (Inter)

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/resumexpert.git
cd resumexpert
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Create a `.env` file in the root directory:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### Step 5: Initialize Database
```bash
python app.py
```
The database will be automatically created on first run.

### Step 6: Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 🚀 Deployment

### Heroku Deployment
1. Create a `Procfile` in the root directory:
```
web: gunicorn app:app
```

2. Deploy to Heroku:
```bash
heroku create your-app-name
git push heroku main
```

### Docker Deployment
1. Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

2. Build and run:
```bash
docker build -t resumexpert .
docker run -p 5000:5000 resumexpert
```

## 📁 Project Structure

```
resumexpert/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .env                  # Environment variables
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Landing page
│   ├── login.html        # Login page
│   ├── signup.html       # Registration page
│   ├── dashboard.html    # User dashboard
│   ├── resume_analysis.html # Resume analysis page
│   ├── templates.html    # Resume templates page
│   └── chatbot.html      # AI chatbot page
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── main.js       # JavaScript functionality
├── uploads/              # User uploaded files
├── generated_resumes/    # Generated resume files
└── resumexpert.db        # SQLite database
```

## 🔧 Configuration

### Database Configuration
The application uses SQLite by default. To use MySQL or PostgreSQL:

1. Install the appropriate driver:
```bash
# For MySQL
pip install mysql-connector-python

# For PostgreSQL
pip install psycopg2-binary
```

2. Update database connection in `app.py`

### AI Configuration
To enable full AI functionality:

1. Get an OpenAI API key from [OpenAI](https://platform.openai.com/)
2. Add it to your `.env` file
3. Update the `openai.api_key` in `app.py`

## 🎯 Usage Guide

### For Users
1. **Register/Login**: Create an account or sign in
2. **Upload Resume**: Upload your existing resume for analysis
3. **View Analysis**: Get detailed feedback and improvement suggestions
4. **Create New Resume**: Use professional templates to build a new resume
5. **AI Assistant**: Chat with the AI for career guidance and tips

### For Developers
1. **Customize Templates**: Modify HTML templates in the `templates/` directory
2. **Add Features**: Extend functionality by adding new routes in `app.py`
3. **Styling**: Customize appearance in `static/css/style.css`
4. **Database**: Add new tables or modify existing ones in the `init_db()` function

## 🔒 Security Features

- Password hashing with Werkzeug
- Session-based authentication
- File upload validation
- SQL injection protection
- XSS prevention
- CSRF protection ready

## 📱 Responsive Design

The application is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- Various screen sizes and orientations

## 🎨 Customization

### Themes
- Light theme (default)
- Dark theme
- Custom theme support

### Colors
- Primary: #667eea
- Secondary: #764ba2
- Easily customizable via CSS variables

### Animations
- Smooth transitions
- Hover effects
- Loading animations
- Scroll-triggered animations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@resumexpert.com or create an issue in the GitHub repository.

## 🙏 Acknowledgments

- Bootstrap for the responsive framework
- Font Awesome for icons
- OpenAI for AI capabilities
- Flask community for excellent documentation

## 📈 Roadmap

- [ ] Advanced AI resume optimization
- [ ] LinkedIn integration
- [ ] Job matching algorithm
- [ ] Resume sharing features
- [ ] Mobile app development
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Team collaboration features

---

**ResumeXpert** - Your professional resume companion powered by AI 🚀
