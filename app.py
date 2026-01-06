from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import uuid
from datetime import datetime
import json
import docx
import PyPDF2
import re
from io import BytesIO
import requests
import openai
import google.generativeai as genai
from functools import wraps

app = Flask(__name__)
app.secret_key = 'AIzaSyD-q-JzJI6CV2inHvTUhb_MfaAx0-GLRKM'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('generated_resumes', exist_ok=True)


openai.api_key = "AIzaSyD-q-JzJI6CV2inHvTUhb_MfaAx0-GLRKM"


GEMINI_API_KEY = "AIzaSyD-q-JzJI6CV2inHvTUhb_MfaAx0-GLRKM"
genai.configure(api_key=GEMINI_API_KEY)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    conn = sqlite3.connect('resumexpert.db')
    cursor = conn.cursor()
    
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            skills TEXT,
            experience TEXT,
            education TEXT,
            analysis_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            theme TEXT DEFAULT 'light',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('resumexpert.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        conn = get_db_connection()
        
        
        existing_user = conn.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?', 
            (username, email)
        ).fetchone()
        
        if existing_user:
            flash('Username or email already exists', 'error')
            conn.close()
            return render_template('signup.html')
        
        
        password_hash = generate_password_hash(password)
        conn.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        conn.commit()
        conn.close()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    resumes = conn.execute(
        'SELECT * FROM resumes WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    return render_template('dashboard.html', resumes=resumes)

@app.route('/upload', methods=['POST'])
@login_required
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        
        analysis_data = parse_resume(file_path)
        
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO resumes (user_id, filename, original_filename, file_path, skills, experience, education, analysis_data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (session['user_id'], unique_filename, filename, file_path, 
             ', '.join(analysis_data.get('skills', [])), analysis_data.get('experience', ''),
             analysis_data.get('education', ''), json.dumps(analysis_data))
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'analysis': analysis_data})
    
    return jsonify({'error': 'Invalid file type'}), 400

def parse_resume(file_path):
    """Parse resume file and extract information"""
    try:
        if file_path.lower().endswith('.pdf'):
            return parse_pdf(file_path)
        elif file_path.lower().endswith(('.docx', '.doc')):
            return parse_docx(file_path)
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return {'skills': [], 'experience': [], 'education': []}

def parse_pdf(file_path):
    """Parse PDF resume"""
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    
    return extract_info_from_text(text)

def parse_docx(file_path):
    """Parse DOCX resume"""
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    
    return extract_info_from_text(text)

def extract_info_from_text(text):
    """Extract skills, experience, and education from text"""
    
    skills_keywords = [
        'python', 'javascript', 'java', 'react', 'node.js', 'flask', 'django',
        'sql', 'mongodb', 'aws', 'docker', 'kubernetes', 'git', 'html', 'css',
        'machine learning', 'data analysis', 'project management', 'leadership'
    ]
    
    found_skills = []
    text_lower = text.lower()
    for skill in skills_keywords:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    
    experience_pattern = r'(experience|work|employment).*?(?=\n\n|\n[A-Z]|$)'
    experience_match = re.search(experience_pattern, text, re.IGNORECASE | re.DOTALL)
    experience = experience_match.group() if experience_match else ""
    
    
    education_pattern = r'(education|degree|university|college).*?(?=\n\n|\n[A-Z]|$)'
    education_match = re.search(education_pattern, text, re.IGNORECASE | re.DOTALL)
    education = education_match.group() if education_match else ""
    
    return {
        'skills': found_skills,
        'experience': experience,
        'education': education,
        'raw_text': text
    }

@app.route('/analyze/<int:resume_id>')
@login_required
def analyze_resume(resume_id):
    conn = get_db_connection()
    resume = conn.execute(
        'SELECT * FROM resumes WHERE id = ? AND user_id = ?',
        (resume_id, session['user_id'])
    ).fetchone()
    conn.close()
    
    if not resume:
        flash('Resume not found', 'error')
        return redirect(url_for('dashboard'))
    
    analysis_data = json.loads(resume['analysis_data']) if resume['analysis_data'] else {}
    return render_template('resume_analysis.html', resume=resume, analysis=analysis_data)

@app.route('/templates')
@login_required
def templates():
    return render_template('templates.html')

@app.route('/generate_template', methods=['POST'])
@login_required
def generate_template():
    template_type = request.form.get('template_type')
    user_data = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'phone': request.form.get('phone'),
        'skills': request.form.get('skills', '').split(','),
        'experience': request.form.get('experience'),
        'education': request.form.get('education')
    }
    
    
    output_filename = f"resume_{uuid.uuid4()}.html"
    output_path = os.path.join('generated_resumes', output_filename)
    
   
    html_content = create_resume_html(template_type, user_data)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return jsonify({'success': True, 'filename': output_filename})

def create_resume_html(template_type, user_data):
    """Create HTML resume based on template type"""
    if template_type == 'modern':
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{user_data['name']} - Resume</title>
            <style>
                body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .resume {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 3px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
                .name {{ font-size: 2.5em; color: #007bff; margin: 0; }}
                .contact {{ color: #666; margin: 10px 0; }}
                .section {{ margin-bottom: 30px; }}
                .section h2 {{ color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 5px; }}
                .skills {{ display: flex; flex-wrap: wrap; gap: 10px; }}
                .skill {{ background: #007bff; color: white; padding: 5px 15px; border-radius: 20px; }}
            </style>
        </head>
        <body>
            <div class="resume">
                <div class="header">
                    <h1 class="name">{user_data['name']}</h1>
                    <div class="contact">
                        <p>📧 {user_data['email']}</p>
                        <p>📱 {user_data['phone']}</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Skills</h2>
                    <div class="skills">
                        {''.join([f'<span class="skill">{skill.strip()}</span>' for skill in user_data['skills']])}
                    </div>
                </div>
                
                <div class="section">
                    <h2>Experience</h2>
                    <p>{user_data['experience']}</p>
                </div>
                
                <div class="section">
                    <h2>Education</h2>
                    <p>{user_data['education']}</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
    
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{user_data['name']} - Resume</title>
            <style>
                body {{ font-family: 'Times New Roman', serif; margin: 0; padding: 20px; background: white; }}
                .resume {{ max-width: 800px; margin: 0 auto; padding: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .name {{ font-size: 2em; font-weight: bold; margin: 0; }}
                .contact {{ margin: 10px 0; }}
                .section {{ margin-bottom: 25px; }}
                .section h2 {{ font-size: 1.2em; border-bottom: 1px solid #333; }}
            </style>
        </head>
        <body>
            <div class="resume">
                <div class="header">
                    <h1 class="name">{user_data['name']}</h1>
                    <div class="contact">
                        <p>{user_data['email']} | {user_data['phone']}</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>SKILLS</h2>
                    <p>{', '.join(user_data['skills'])}</p>
                </div>
                
                <div class="section">
                    <h2>EXPERIENCE</h2>
                    <p>{user_data['experience']}</p>
                </div>
                
                <div class="section">
                    <h2>EDUCATION</h2>
                    <p>{user_data['education']}</p>
                </div>
            </div>
        </body>
        </html>
        """

@app.route('/download/<filename>')
@login_required
def download_resume(filename):
    
    generated_path = os.path.join('generated_resumes', filename)
    if os.path.exists(generated_path):
        return send_file(generated_path, as_attachment=True)
    
    
    conn = get_db_connection()
    resume = conn.execute(
        'SELECT * FROM resumes WHERE filename = ? AND user_id = ?',
        (filename, session['user_id'])
    ).fetchone()
    conn.close()
    
    if resume and os.path.exists(resume['file_path']):
        return send_file(resume['file_path'], as_attachment=True)
    else:
        flash('File not found', 'error')
        return redirect(url_for('dashboard'))

@app.route('/job_matching')
@login_required
def job_matching():
    return render_template('job_matching.html')


@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    message = request.json.get('message')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    
    response = get_ai_response(message, session['user_id'])
    
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)',
        (session['user_id'], message, response)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'response': response})

def get_ai_response(message, user_id):
    """Get AI response for chatbot using Gemini API with enhanced capabilities"""
    try:
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        
        prompt = f"""
        You are ResumeXpert AI Assistant, an intelligent career advisor and resume expert. You can answer ANY question, but specialize in career development, resume building, job searching, and professional growth.

        User Question: {message}

        Instructions:
        1. If it's a career/resume question: Provide detailed, actionable advice
        2. If it's a general question: Answer helpfully and professionally
        3. If it's about ResumeXpert: Explain features and capabilities
        4. If it's personal: Be encouraging and supportive
        5. If it's technical: Provide clear, step-by-step guidance

        Response Guidelines:
        - Be conversational and friendly
        - Keep responses between 50-300 words
        - Use bullet points, numbered lists, or formatting when helpful
        - Provide specific examples when relevant
        - End with a follow-up question or suggestion when appropriate
        - Be encouraging and positive
        - If you don't know something, admit it and offer to help with related topics

        Context: This is a resume builder application user asking questions.
        """
        
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        
        return get_enhanced_fallback_response(message)

def get_enhanced_fallback_response(message):
    """Enhanced fallback responses for when Gemini API fails"""
    message_lower = message.lower()
    
    
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! I'm ResumeXpert AI Assistant, your career companion! 👋 I'm here to help with resume building, career advice, job searching, and professional development. What would you like to know?"
    
    
    if any(word in message_lower for word in ['name', 'who', 'what are you', 'introduce']):
        return "I'm ResumeXpert AI Assistant! 🤖 I'm your intelligent career advisor specializing in resume optimization, job search strategies, interview preparation, and professional growth. I can help with any career-related questions or general topics too!"
    
    
    if any(word in message_lower for word in ['resume', 'cv', 'curriculum vitae']):
        return """**Resume Building Tips:**
• Keep it 1-2 pages maximum
• Use clear, professional formatting
• Include relevant keywords from job descriptions
• Quantify achievements with numbers
• Tailor each resume to the specific job
• Proofread carefully for errors
• Use action verbs to start bullet points

Need help with a specific section of your resume?"""
    
    
    if any(word in message_lower for word in ['skill', 'skills', 'learn', 'training']):
        return """**In-Demand Skills for 2024:**
• **Technical:** Python, JavaScript, React, AWS, Docker, Machine Learning
• **Soft Skills:** Leadership, Communication, Problem-solving, Adaptability
• **Digital:** Data Analysis, Project Management, Digital Marketing
• **Emerging:** AI/ML, Cloud Computing, Cybersecurity, Blockchain

What field are you interested in? I can suggest specific skills for your industry!"""
    
    
    if any(word in message_lower for word in ['interview', 'interviewing', 'interview tips']):
        return """**Interview Success Tips:**
• Research the company and role thoroughly
• Practice common questions using STAR method
• Prepare 3-5 questions to ask them
• Dress professionally and arrive 10 minutes early
• Bring copies of your resume and references
• Follow up with a thank-you email within 24 hours
• Practice your elevator pitch

What type of interview are you preparing for?"""
    
    
    if any(word in message_lower for word in ['job', 'jobs', 'hiring', 'employment', 'work']):
        return """**Job Search Strategies:**
• Use multiple job boards (LinkedIn, Indeed, company websites)
• Network actively on LinkedIn and at industry events
• Customize applications for each position
• Follow up on applications after 1-2 weeks
• Consider informational interviews
• Build a strong online presence
• Keep your skills updated

What industry or role are you targeting?"""
    
    
    if any(word in message_lower for word in ['help', 'assist', 'support', 'how']):
        return """I'm here to help! I can assist with:
• Resume writing and optimization
• Career advice and planning
• Interview preparation
• Job search strategies
• Skill development recommendations
• General questions about anything

What specific area would you like help with?"""
    
    
    if any(word in message_lower for word in ['thank', 'thanks', 'appreciate']):
        return "You're very welcome! 😊 I'm always here to help with your career journey. Is there anything else you'd like to know or discuss?"
    
    
    return f"""I understand you're asking about: "{message}"

While I specialize in career advice and resume building, I'm happy to help with general questions too! 

For career-related topics, I can provide expert guidance on:
• Resume optimization and writing
• Interview preparation and techniques
• Job search strategies and networking
• Skill development and career planning
• Professional growth and advancement

Could you provide more details about what you'd like to know? I'm here to help! 🤖"""

@app.route('/theme', methods=['POST'])
@login_required
def toggle_theme():
    theme = request.json.get('theme', 'light')
    
    conn = get_db_connection()
    conn.execute(
        'INSERT OR REPLACE INTO user_preferences (user_id, theme) VALUES (?, ?)',
        (session['user_id'], theme)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/get_theme')
@login_required
def get_theme():
    conn = get_db_connection()
    preference = conn.execute(
        'SELECT theme FROM user_preferences WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    theme = preference['theme'] if preference else 'light'
    return jsonify({'theme': theme})

@app.route('/delete_resume/<int:resume_id>', methods=['DELETE'])
@login_required
def delete_resume(resume_id):
    try:
        conn = get_db_connection()
        
        # Get resume details
        resume = conn.execute(
            'SELECT * FROM resumes WHERE id = ? AND user_id = ?',
            (resume_id, session['user_id'])
        ).fetchone()
        
        if not resume:
            conn.close()
            return jsonify({'error': 'Resume not found'}), 404
        
        # Delete file from filesystem
        file_path = resume['file_path']
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        conn.execute(
            'DELETE FROM resumes WHERE id = ? AND user_id = ?',
            (resume_id, session['user_id'])
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Resume deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': 'Failed to delete resume'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
