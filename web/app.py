#!/usr/bin/env python3
"""
Web UI for Vibe CV Resume Builder
Automates job-specific CV variant creation with AI optimization
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
import os
import subprocess
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import openai
import anthropic
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import PyPDF2
from docx import Document
from models import db, User, CVMaster, CVVariant

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(Path(__file__).parent / 'vibe_cv.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# AI Configuration
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')
AI_MODEL = os.getenv('AI_MODEL', 'gpt-4-turbo')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Project paths
BASE_DIR = Path(__file__).parent.parent
V1_DIR = BASE_DIR / "v1"
MASTER_TEX = V1_DIR / "master.tex"
PROMPTS_DIR = BASE_DIR / "prompts"
UPLOAD_FOLDER = BASE_DIR / "web" / "uploads"
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Create upload folder if not exists
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Initialize database
with app.app_context():
    db.create_all()
    # Create default admin if no users exist
    if User.query.count() == 0:
        admin = User(email='admin@vibe-cv.com')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Created default admin user: admin@vibe-cv.com / admin123")

# User Storage Functions (kept for compatibility)
def save_users(users):
    """Deprecated - users now stored in database"""
    with open(Path(__file__).parent / 'users_backup.json', 'w') as f:
        json.dump(users, f, indent=2)

def get_user_by_email(email):
    """Get user by email from database"""
    return User.query.filter_by(email=email).first()
    return None

def get_user_by_id(user_id):
    """Get user by ID from database"""
    return User.query.get(int(user_id))

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

def sanitize_folder_name(name):
    """Convert company/role name to valid folder name"""
    name = re.sub(r'[^\w\s-]', '', name.lower())
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')

def get_variant_owner(variant_dir):
    """Get owner user_id of a variant from database"""
    folder_name = variant_dir.name
    variant = CVVariant.query.filter_by(folder_name=folder_name).first()
    return str(variant.user_id) if variant else None

def set_variant_owner(variant_dir, user_id):
    """Set owner user_id of a variant in database"""
    folder_name = variant_dir.name
    # Check if already exists
    variant = CVVariant.query.filter_by(folder_name=folder_name).first()
    if not variant:
        variant = CVVariant(user_id=user_id, folder_name=folder_name)
        db.session.add(variant)
        db.session.commit()

def user_owns_variant(variant_folder, user_id):
    """Check if user owns the variant"""
    variant_dir = V1_DIR / variant_folder
    if not variant_dir.exists():
        return False
    owner = get_variant_owner(variant_dir)
    return owner == str(user_id)

def get_existing_variants(user_id=None):
    """Get list of existing CV variants from database (filtered by user if provided)"""
    query = CVVariant.query
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    variants = []
    for variant in query.order_by(CVVariant.created_at.desc()).all():
        variant_dir = V1_DIR / variant.folder_name
        if not variant_dir.exists():
            continue
            
        job_desc_file = variant_dir / "job_desc.md"
        
        # Read company name from job_desc if exists
        company_name = variant.company or variant.folder_name
        if not variant.company and job_desc_file.exists():
            with open(job_desc_file, 'r', encoding='utf-8') as f:
                first_lines = f.read(200)
                # Try to extract company name from first few lines
                for line in first_lines.split('\n')[:5]:
                    if line.strip():
                        company_name = line.strip()
                        break
        
        variants.append({
            'folder': variant.folder_name,
            'company': company_name,
            'has_tex': variant.has_tex,
            'has_pdf': variant.has_pdf,
            'has_job_desc': job_desc_file.exists(),
            'match_score': variant.match_score,
            'created': variant.created_at.strftime('%Y-%m-%d')
        })
    
    return variants

def call_ai_to_optimize_cv(master_tex_content, job_desc_content, prompt_template):
    """Call AI API to optimize CV based on job description"""
    
    system_prompt = f"""You are an expert CV optimization assistant. You will:
1. Read the master CV (LaTeX format)
2. Read the job description
3. Calculate a realistic match percentage (0-100%)
4. Optimize the CV to match the job requirements
5. Return BOTH the match score AND the optimized LaTeX code

{prompt_template}

CRITICAL OUTPUT FORMAT:
First line MUST be: MATCH_SCORE: XX%
Then a blank line
Then the complete LaTeX code starting with \\documentclass

Example:
MATCH_SCORE: 75%

\\documentclass[a4paper,11pt]{{article}}
...rest of LaTeX..."""
    
    user_prompt = f"""Please analyze and optimize this CV for the following job:

JOB DESCRIPTION:
{job_desc_content}

MASTER CV (LaTeX):
{master_tex_content}

Tasks:
1. Calculate match percentage based on:
   - Core skills alignment
   - Experience relevance
   - Tool/technology overlap
   - Seniority fit

2. Generate optimized CV in LaTeX format:
   - Rewrite summary to match job requirements
   - Reorder experience to prioritize relevant roles
   - Add keywords from job description (only if they reflect existing experience)
   - Emphasize relevant skills and technologies
   - Keep ALL formatting, packages, and custom commands intact (especially \\myuline definition)
- COPY THE ENTIRE PREAMBLE from master CV including all \\newcommand definitions"""
    
    try:
        if AI_PROVIDER == 'openai' and OPENAI_API_KEY:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            return response.choices[0].message.content.strip()
        
        elif AI_PROVIDER == 'anthropic' and ANTHROPIC_API_KEY:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=AI_MODEL if AI_MODEL.startswith('claude') else 'claude-3-sonnet-20240229',
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text.strip()
        
        else:
            return None
    
    except Exception as e:
        print(f"AI API Error: {e}")
        return None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return None

def extract_text_from_docx(docx_path):
    """Extract text from DOCX file"""
    try:
        doc = Document(docx_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        print(f"DOCX extraction error: {e}")
        return None

def extract_match_score(ai_response):
    """Extract match score percentage from AI response"""
    import re
    
    if not ai_response:
        return None
    
    # Look for patterns like "Overall Match Percentage: 75%" or "Match: 75%"
    patterns = [
        r'Overall Match(?:\s+Percentage)?[:\s]+([0-9]{1,3})%',
        r'Match(?:\s+Score)?[:\s]+([0-9]{1,3})%',
        r'Score[:\s]+([0-9]{1,3})%',
        r'([0-9]{1,3})%\s+match',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, ai_response, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 100:
                return score
    
    return None

def extract_match_score(ai_response):
    """Extract match score percentage from AI response"""
    import re
    
    if not ai_response:
        return None
    
    # Look for MATCH_SCORE: XX% format first (new format)
    match = re.search(r'MATCH_SCORE:\s*([0-9]{1,3})%', ai_response, re.IGNORECASE)
    if match:
        score = int(match.group(1))
        if 0 <= score <= 100:
            return score
    
    # Fallback to old patterns
    patterns = [
        r'Overall Match(?:\s+Percentage)?[:\s]+([0-9]{1,3})%',
        r'Match(?:\s+Score)?[:\s]+([0-9]{1,3})%',
        r'Score[:\s]+([0-9]{1,3})%',
        r'([0-9]{1,3})%\s+match',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, ai_response, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 100:
                return score
    
    return None

def fix_latex_special_chars(latex_content):
    """Fix common LaTeX special character issues"""
    import re
    
    # Don't fix escaped characters
    # Fix unescaped & (but not \\& or in table alignment)
    latex_content = re.sub(r'(?<!\\)&(?![&\s]*\\\\)', r'\\&', latex_content)
    
    # Fix unescaped % (but not \\%)
    latex_content = re.sub(r'(?<!\\)%(?!.*\\)', r'\\%', latex_content)
    
    # Fix unescaped _ (but not \\_ or in math mode)
    latex_content = re.sub(r'(?<!\\)_(?![_\s]*[\$\\])', r'\\_', latex_content)
    
    # Fix unescaped # (but not \\#)
    latex_content = re.sub(r'(?<!\\)#(?![\d])', r'\\#', latex_content)
    
    return latex_content

def convert_cv_to_latex(cv_text):
    """Convert CV text to LaTeX format using AI"""
    system_prompt = """You are an expert LaTeX CV converter. You will:
1. Read a CV in plain text format
2. Convert it to professional LaTeX format matching the provided template structure
3. Return ONLY the complete LaTeX code

CRITICAL: 
- Return ONLY the LaTeX code starting with \\documentclass
- Use the moderncv template style
- Include all necessary packages and formatting
- Keep the structure clean and professional
- Extract: name, contact info, summary, experience, education, skills
- Properly escape special LaTeX characters: & becomes \\&, # becomes \\#, % becomes \\%, _ becomes \\_"""

    user_prompt = f"""Convert this CV to LaTeX format:

CV TEXT:
{cv_text}

Generate a complete LaTeX CV using moderncv style. Include:
- Document class and packages
- Personal information (name, email, phone, location)
- Professional summary
- Work experience with bullet points
- Education
- Skills
- Use \\documentclass{{moderncv}} or similar professional template
- Return ONLY the LaTeX code, no explanations"""

    try:
        if AI_PROVIDER == 'openai' and OPENAI_API_KEY:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            return response.choices[0].message.content.strip()
        
        elif AI_PROVIDER == 'anthropic' and ANTHROPIC_API_KEY:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            response = client.messages.create(
                model=AI_MODEL if AI_MODEL.startswith('claude') else 'claude-3-sonnet-20240229',
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text.strip()
        
        return None
    
    except Exception as e:
        print(f"AI conversion error: {e}")
        return None

def get_user_master_tex(user_id):
    """Get user's personal master.tex content from database, or default from file"""
    cv_master = CVMaster.query.filter_by(user_id=user_id, is_active=True).first()
    if cv_master:
        return cv_master.latex_content
    
    # Fallback to default master.tex file
    if MASTER_TEX.exists():
        with open(MASTER_TEX, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def compile_cv_internal(folder_name):
    """Internal function to compile CV (used by auto-optimize)"""
    variant_dir = V1_DIR / folder_name
    main_tex = variant_dir / "main.tex"
    
    if not main_tex.exists():
        print(f"❌ main.tex not found for {folder_name}")
        return False
    
    # Use Docker to compile
    home_dir = Path.home()
    # Use hash of folder_name to avoid special characters in filename
    import hashlib
    safe_name = hashlib.md5(folder_name.encode()).hexdigest()[:12]
    temp_tex = home_dir / f"cv-{safe_name}.tex"
    
    try:
        # Copy tex file to home directory
        subprocess.run(['cp', str(main_tex), str(temp_tex)], check=True)
        print(f"📄 Compiling {folder_name}...")
        
        # Compile with Docker (disable bibtex, force compilation)
        result = subprocess.run([
            'docker', 'run', '--rm',
            '-v', f'{home_dir}:/workspace',
            '-w', '/workspace',
            'texlive/texlive:latest',
            'latexmk', '-pdf', '-interaction=nonstopmode', '-f', '-bibtex-', f'cv-{safe_name}.tex'
        ], capture_output=True, timeout=60, text=True)
        
        if result.returncode != 0:
            print(f"❌ LaTeX compilation failed for {folder_name}")
            print(f"STDERR: {result.stderr[:500]}")
            # Save error log for debugging
            error_log = variant_dir / "compile_error.log"
            with open(error_log, 'w') as f:
                f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
            return False
        
        # Copy PDF back
        temp_pdf = home_dir / f"cv-{safe_name}.pdf"
        output_pdf = variant_dir / "main.pdf"
        
        if temp_pdf.exists():
            subprocess.run(['cp', str(temp_pdf), str(output_pdf)], check=True)
            print(f"✅ PDF compiled successfully: {output_pdf}")
            # Cleanup temp files
            for ext in ['tex', 'pdf', 'aux', 'log', 'out', 'fls', 'fdb_latexmk']:
                temp_file = home_dir / f"cv-{safe_name}.{ext}"
                if temp_file.exists():
                    temp_file.unlink()
            return True
        else:
            print(f"❌ PDF file not generated for {folder_name}")
        
        return False
    
    except subprocess.TimeoutExpired:
        print(f"⏱️ Compilation timeout for {folder_name}")
        return False
    except Exception as e:
        print(f"❌ Compilation error for {folder_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/')
@login_required
def index():
    """Render main page"""
    variants = get_existing_variants(user_id=current_user.id)
    return render_template('index.html', variants=variants, user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')
        
        user = get_user_by_email(email)
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register new user"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not email or not password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        # Check if email already exists
        if get_user_by_email(email):
            flash('Email already registered. Please login.', 'error')
            return render_template('register.html')
        
        # Create new user in database
        new_user = User(email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/api/upload-cv', methods=['POST'])
@login_required
def upload_cv():
    """Upload user's CV (PDF/DOC) and convert to LaTeX master"""
    try:
        # Check if file is present
        if 'cv_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['cv_file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF and DOC/DOCX files are allowed'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        temp_file_path = UPLOAD_FOLDER / f"user_{current_user.id}_{filename}"
        file.save(temp_file_path)
        
        # Extract text from file
        if file_ext == 'pdf':
            cv_text = extract_text_from_pdf(temp_file_path)
        else:  # doc or docx
            cv_text = extract_text_from_docx(temp_file_path)
        
        if not cv_text:
            temp_file_path.unlink()  # Clean up
            return jsonify({'error': 'Failed to extract text from file'}), 500
        
        # Convert to LaTeX using AI
        if not (OPENAI_API_KEY or ANTHROPIC_API_KEY):
            temp_file_path.unlink()
            return jsonify({'error': 'AI API key not configured'}), 500
        
        latex_content = convert_cv_to_latex(cv_text)
        
        if not latex_content:
            temp_file_path.unlink()
            return jsonify({'error': 'Failed to convert CV to LaTeX format'}), 500
        
        # Clean LaTeX content (remove markdown blocks if present)
        if '```latex' in latex_content:
            latex_content = latex_content.split('```latex')[1].split('```')[0].strip()
        elif '```' in latex_content:
            latex_content = latex_content.split('```')[1].split('```')[0].strip()
        
        # Fix common LaTeX special character issues
        latex_content = fix_latex_special_chars(latex_content)
        
        # Save as user's master.tex
        user_master = V1_DIR / f"user_{current_user.id}_master.tex"
        with open(user_master, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # Store in database
        # Deactivate previous masters
        CVMaster.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
        
        # Create new master record
        cv_master = CVMaster(
            user_id=current_user.id,
            latex_content=latex_content,
            original_filename=filename,
            version=CVMaster.query.filter_by(user_id=current_user.id).count() + 1
        )
        db.session.add(cv_master)
        db.session.commit()
        
        # Clean up temp file
        temp_file_path.unlink()
        
        return jsonify({
            'success': True,
            'message': 'CV uploaded and converted successfully',
            'master_file': f"user_{current_user.id}_master.tex"
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-user-master', methods=['GET'])
@login_required
def check_user_master():
    """Check if user has uploaded their own master CV"""
    cv_master = CVMaster.query.filter_by(user_id=current_user.id, is_active=True).first()
    return jsonify({
        'has_master': cv_master is not None,
        'master_file': f"database_id_{cv_master.id}" if cv_master else None
    })

@app.route('/api/create-variant', methods=['POST'])
@login_required
def create_variant():
    """Create new CV variant with AI optimization and auto-compile"""
    try:
        data = request.json
        company_name = data.get('company_name', '').strip()
        role_name = data.get('role_name', '').strip()
        job_description = data.get('job_description', '').strip()
        auto_optimize = data.get('auto_optimize', True)
        
        if not company_name or not role_name or not job_description:
            return jsonify({'error': 'All fields are required'}), 400
        
        # Create folder name
        folder_name = sanitize_folder_name(f"{company_name}-{role_name}")
        variant_dir = V1_DIR / folder_name
        
        # Check if already exists in database
        existing = CVVariant.query.filter_by(user_id=current_user.id, folder_name=folder_name).first()
        if existing:
            return jsonify({'error': f'Variant "{folder_name}" already exists'}), 400
        
        # Create directory
        variant_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database record
        variant = CVVariant(
            user_id=current_user.id,
            folder_name=folder_name,
            company=company_name,
            role=role_name,
            job_description=job_description
        )
        db.session.add(variant)
        db.session.commit()
        
        # Write job description
        job_desc_file = variant_dir / "job_desc.md"
        with open(job_desc_file, 'w', encoding='utf-8') as f:
            f.write(f"# {company_name}\n")
            f.write(f"**Role:** {role_name}\n\n")
            f.write(f"---\n\n")
            f.write(job_description)
        
        result = {
            'success': True,
            'folder_name': folder_name,
            'has_pdf': False,
            'message': f'Created variant folder: {folder_name}'
        }
        
        # AI Optimization (if enabled and API key available)
        if auto_optimize and (OPENAI_API_KEY or ANTHROPIC_API_KEY):
            try:
                # Read user's master.tex or default
                master_tex_content = get_user_master_tex(current_user.id)
                
                if not master_tex_content:
                    result['message'] += ' | No master CV found'
                    return jsonify(result)
                
                # Read prompt template
                prompt_file = PROMPTS_DIR / "job_desc_match.md"
                prompt_template = ""
                if prompt_file.exists():
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        prompt_template = f.read()
                
                # Call AI
                ai_response = call_ai_to_optimize_cv(master_tex_content, job_description, prompt_template)
                
                if ai_response:
                    # Extract match score from response
                    match_score = extract_match_score(ai_response)
                    if match_score:
                        variant.match_score = match_score
                        result['match_score'] = match_score
                        result['message'] += f' | Match: {match_score}%'
                    
                    # Remove MATCH_SCORE line if present
                    optimized_latex = ai_response
                    if 'MATCH_SCORE:' in optimized_latex:
                        lines = optimized_latex.split('\n')
                        # Skip first line (MATCH_SCORE) and any blank lines after it
                        start_idx = 0
                        for i, line in enumerate(lines):
                            if line.strip() and not line.startswith('MATCH_SCORE:'):
                                start_idx = i
                                break
                        optimized_latex = '\n'.join(lines[start_idx:])
                    
                    # Clean markdown code blocks if present
                    if '```latex' in optimized_latex:
                        optimized_latex = optimized_latex.split('```latex')[1].split('```')[0].strip()
                    elif '```' in optimized_latex:
                        optimized_latex = optimized_latex.split('```')[1].split('```')[0].strip()
                    
                    # Fix common LaTeX special character issues
                    optimized_latex = fix_latex_special_chars(optimized_latex)
                    
                    # Write optimized LaTeX
                    main_tex = variant_dir / "main.tex"
                    with open(main_tex, 'w', encoding='utf-8') as f:
                        f.write(optimized_latex)
                    
                    # Update database
                    variant.has_tex = True
                    db.session.commit()
                    
                    result['message'] += ' | AI optimized successfully'
                    
                    # Auto-compile PDF
                    try:
                        compile_success = compile_cv_internal(folder_name)
                        if compile_success:
                            variant.has_pdf = True
                            db.session.commit()
                            result['has_pdf'] = True
                            result['message'] += ' | PDF compiled successfully'
                        else:
                            result['message'] += ' | PDF compilation failed'
                    except Exception as compile_error:
                        result['message'] += f' | PDF compilation failed: {str(compile_error)}'
                
                else:
                    result['message'] += ' | AI optimization skipped (no API response)'
            
            except Exception as ai_error:
                result['message'] += f' | AI optimization failed: {str(ai_error)}'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compile-cv', methods=['POST'])
@login_required
def compile_cv():
    """Compile LaTeX to PDF using Docker"""
    try:
        data = request.json
        folder_name = data.get('folder_name', '').strip()
        
        print(f"🔧 Compile request for: {folder_name}")
        
        if not folder_name:
            return jsonify({'error': 'Folder name is required'}), 400
        
        # Check ownership
        variant = CVVariant.query.filter_by(user_id=current_user.id, folder_name=folder_name).first()
        if not variant:
            print(f"❌ Variant not found or access denied: {folder_name}")
            return jsonify({'error': 'Access denied'}), 403
        
        variant_dir = V1_DIR / folder_name
        main_tex = variant_dir / "main.tex"
        
        print(f"📂 Variant dir: {variant_dir}")
        print(f"📄 main.tex exists: {main_tex.exists()}")
        
        if not main_tex.exists():
            return jsonify({'error': 'main.tex not found. Please optimize CV first.'}), 400
        
        # Use Docker to compile
        home_dir = Path.home()
        # Use hash of folder_name to avoid special characters in filename
        import hashlib
        safe_name = hashlib.md5(folder_name.encode()).hexdigest()[:12]
        temp_tex = home_dir / f"cv-{safe_name}.tex"
        
        print(f"🔨 Temp file: {temp_tex}")
        
        # Copy tex file to home directory (Docker can access it)
        subprocess.run(['cp', str(main_tex), str(temp_tex)], check=True)
        
        print(f"🐳 Running Docker compilation...")
        
        # Compile with Docker (disable bibtex, force compilation)
        result = subprocess.run([
            'docker', 'run', '--rm',
            '-v', f'{home_dir}:/workspace',
            '-w', '/workspace',
            'texlive/texlive:latest',
            'latexmk', '-pdf', '-interaction=nonstopmode', '-f', '-bibtex-', f'cv-{safe_name}.tex'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"❌ Compilation failed with return code: {result.returncode}")
            print(f"STDERR: {result.stderr[:500]}")
            # Save error log
            error_log = variant_dir / "compile_error.log"
            with open(error_log, 'w') as f:
                f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
            return jsonify({'error': f'Compilation failed: {result.stderr[:200]}'}), 500
        
        # Copy PDF back
        temp_pdf = home_dir / f"cv-{safe_name}.pdf"
        output_pdf = variant_dir / "main.pdf"
        
        print(f"📦 PDF exists: {temp_pdf.exists()}")
        
        if temp_pdf.exists():
            subprocess.run(['cp', str(temp_pdf), str(output_pdf)], check=True)
            print(f"✅ PDF copied to: {output_pdf}")
            # Cleanup temp files
            for ext in ['tex', 'pdf', 'aux', 'log', 'out', 'fls', 'fdb_latexmk']:
                temp_file = home_dir / f"cv-{safe_name}.{ext}"
                if temp_file.exists():
                    temp_file.unlink()
            
            # Update database
            variant.has_pdf = True
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'CV compiled successfully',
                'pdf_path': str(output_pdf)
            })
        else:
            print(f"❌ PDF file not generated")
            return jsonify({'error': 'PDF not generated'}), 500
    
    except subprocess.TimeoutExpired:
        print(f"⏱️ Compilation timeout")
        return jsonify({'error': 'Compilation timeout (60s)'}), 500
    except Exception as e:
        print(f"❌ Exception in compile_cv: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@login_required
@app.route('/api/download-pdf/<folder_name>')
@login_required
def download_pdf(folder_name):
    """Download compiled PDF"""
    try:
        # Check ownership
        if not user_owns_variant(folder_name, current_user.id):
            return jsonify({'error': 'Access denied'}), 403
        
        variant_dir = V1_DIR / folder_name
        pdf_file = variant_dir / "main.pdf"
        
        if not pdf_file.exists():
            return jsonify({'error': 'PDF not found'}), 404
        
        return send_file(pdf_file, as_attachment=True, download_name=f'{folder_name}-cv.pdf')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-job-desc/<folder_name>')
def get_job_desc(folder_name):
    """Get job description content"""
    try:
        variant_dir = V1_DIR / folder_name
        job_desc_file = variant_dir / "job_desc.md"
        
        if not job_desc_file.exists():
            return jsonify({'error': 'Job description not found'}), 404
        
        with open(job_desc_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({'content': content})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@login_required
@app.route('/api/delete-variant/<folder_name>', methods=['DELETE'])
@login_required
def delete_variant(folder_name):
    """Delete a variant folder"""
    try:
        # Check ownership
        if not user_owns_variant(folder_name, current_user.id):
            return jsonify({'error': 'Access denied'}), 403
        
        variant_dir = V1_DIR / folder_name
        
        if not variant_dir.exists():
            return jsonify({'error': 'Variant not found'}), 404
        
        # Delete folder and all contents
        import shutil
        shutil.rmtree(variant_dir)
        
        return jsonify({
            'success': True,
            'message': f'Deleted variant: {folder_name}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure v1 directory exists
    V1_DIR.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("🚀 Vibe CV Resume Builder - Web UI")
    print("=" * 60)
    print(f"📁 Project Directory: {BASE_DIR}")
    print(f"📄 Master CV: {MASTER_TEX}")
    
    # Check AI API configuration
    if OPENAI_API_KEY:
        print(f"🤖 AI Provider: OpenAI ({AI_MODEL})")
    elif ANTHROPIC_API_KEY:
        print(f"🤖 AI Provider: Anthropic ({AI_MODEL})")
    else:
        print("⚠️  No AI API key configured - auto-optimization disabled")
    
    print(f"🌐 Starting server at: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
