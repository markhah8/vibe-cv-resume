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
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

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
USERS_FILE = BASE_DIR / "web" / "users.json"

# User Model
class User(UserMixin):
    def __init__(self, id, email, password_hash):
        self.id = id
        self.email = email
        self.password_hash = password_hash

# User Storage Functions
def load_users():
    """Load users from JSON file"""
    if not USERS_FILE.exists():
        # Create default admin user
        default_users = {
            "1": {
                "email": "admin@vibe-cv.com",
                "password_hash": generate_password_hash("admin123")
            }
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f, indent=2)
        return default_users
    
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_user_by_email(email):
    """Get user by email"""
    users = load_users()
    for user_id, user_data in users.items():
        if user_data['email'] == email:
            return User(user_id, user_data['email'], user_data['password_hash'])
    return None

def get_user_by_id(user_id):
    """Get user by ID"""
    users = load_users()
    if str(user_id) in users:
        user_data = users[str(user_id)]
        return User(user_id, user_data['email'], user_data['password_hash'])
    return None

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

def sanitize_folder_name(name):
    """Convert company/role name to valid folder name"""
    name = re.sub(r'[^\w\s-]', '', name.lower())
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')

def get_variant_owner(variant_dir):
    """Get owner user_id of a variant"""
    owner_file = variant_dir / ".owner"
    if owner_file.exists():
        with open(owner_file, 'r') as f:
            return f.read().strip()
    return None

def set_variant_owner(variant_dir, user_id):
    """Set owner user_id of a variant"""
    owner_file = variant_dir / ".owner"
    with open(owner_file, 'w') as f:
        f.write(str(user_id))

def user_owns_variant(variant_folder, user_id):
    """Check if user owns the variant"""
    variant_dir = V1_DIR / variant_folder
    if not variant_dir.exists():
        return False
    owner = get_variant_owner(variant_dir)
    return owner == str(user_id)

def get_existing_variants(user_id=None):
    """Get list of existing CV variants (filtered by user if provided)"""
    variants = []
    if not V1_DIR.exists():
        return variants
    
    for item in V1_DIR.iterdir():
        if item.is_dir() and item.name not in ['.git', '__pycache__', 'canva']:
            # Check ownership if user_id provided
            if user_id:
                owner = get_variant_owner(item)
                if owner != str(user_id):
                    continue  # Skip variants not owned by this user
            
            job_desc_file = item / "job_desc.md"
            main_tex = item / "main.tex"
            pdf_file = item / "main.pdf"
            
            # Read company name from job_desc if exists
            company_name = item.name
            if job_desc_file.exists():
                with open(job_desc_file, 'r', encoding='utf-8') as f:
                    first_lines = f.read(200)
                    # Try to extract company name from first few lines
                    for line in first_lines.split('\n')[:5]:
                        if line.strip():
                            company_name = line.strip()
                            break
            
            variants.append({
                'folder': item.name,
                'company': company_name,
                'has_tex': main_tex.exists(),
                'has_pdf': pdf_file.exists(),
                'has_job_desc': job_desc_file.exists(),
                'created': datetime.fromtimestamp(item.stat().st_ctime).strftime('%Y-%m-%d')
            })
    
    return sorted(variants, key=lambda x: x['created'], reverse=True)

def call_ai_to_optimize_cv(master_tex_content, job_desc_content, prompt_template):
    """Call AI API to optimize CV based on job description"""
    
    system_prompt = f"""You are an expert CV optimization assistant. You will:
1. Read the master CV (LaTeX format)
2. Read the job description
3. Optimize the CV to match the job requirements
4. Return ONLY the complete optimized LaTeX code

{prompt_template}

CRITICAL: Return ONLY the LaTeX code. No explanations, no markdown code blocks, 
just pure LaTeX starting with \\documentclass"""
    
    user_prompt = f"""Please optimize this CV for the following job:

JOB DESCRIPTION:
{job_desc_content}

MASTER CV (LaTeX):
{master_tex_content}

Generate the optimized CV in LaTeX format. Focus on:
- Rewriting summary to match job requirements
- Reordering experience to prioritize relevant roles
- Adding keywords from job description
- Emphasizing relevant skills and technologies
- Keeping ALL formatting, packages, and custom commands intact (especially \\myuline definition)
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

def compile_cv_internal(folder_name):
    """Internal function to compile CV (used by auto-optimize)"""
    variant_dir = V1_DIR / folder_name
    main_tex = variant_dir / "main.tex"
    
    if not main_tex.exists():
        return False
    
    # Use Docker to compile
    home_dir = Path.home()
    temp_tex = home_dir / f"{folder_name}-cv.tex"
    
    try:
        # Copy tex file to home directory
        subprocess.run(['cp', str(main_tex), str(temp_tex)], check=True)
        
        # Compile with Docker
        result = subprocess.run([
            'docker', 'run', '--rm',
            '-v', f'{home_dir}:/workspace',
            '-w', '/workspace',
            'texlive/texlive:latest',
            'latexmk', '-pdf', f'{folder_name}-cv.tex'
        ], capture_output=True, timeout=60)
        
        if result.returncode != 0:
            return False
        
        # Copy PDF back
        temp_pdf = home_dir / f"{folder_name}-cv.pdf"
        output_pdf = variant_dir / "main.pdf"
        
        if temp_pdf.exists():
            subprocess.run(['cp', str(temp_pdf), str(output_pdf)], check=True)
            # Cleanup temp files
            for ext in ['tex', 'pdf', 'aux', 'log', 'out', 'fls', 'fdb_latexmk']:
                temp_file = home_dir / f"{folder_name}-cv.{ext}"
                if temp_file.exists():
                    temp_file.unlink()
            return True
        
        return False
    
    except Exception as e:
        print(f"Compilation error: {e}")
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
        
        if user and check_password_hash(user.password_hash, password):
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
        
        # Create new user
        users = load_users()
        new_user_id = str(max([int(uid) for uid in users.keys()]) + 1) if users else "1"
        
        users[new_user_id] = {
            'email': email,
            'password_hash': generate_password_hash(password)
        }
        
        save_users(users)
        
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
        
        # Check if already exists
        if variant_dir.exists():
            return jsonify({'error': f'Variant "{folder_name}" already exists'}), 400
        
        # Create directory
        variant_dir.mkdir(parents=True, exist_ok=True)
        
        # Set owner
        set_variant_owner(variant_dir, current_user.id)
        
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
                # Read master.tex
                with open(MASTER_TEX, 'r', encoding='utf-8') as f:
                    master_tex_content = f.read()
                
                # Read prompt template
                prompt_file = PROMPTS_DIR / "job_desc_match.md"
                prompt_template = ""
                if prompt_file.exists():
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        prompt_template = f.read()
                
                # Call AI
                optimized_latex = call_ai_to_optimize_cv(master_tex_content, job_description, prompt_template)
                
                if optimized_latex:
                    # Clean the response (remove markdown code blocks if present)
                    if '```latex' in optimized_latex:
                        optimized_latex = optimized_latex.split('```latex')[1].split('```')[0].strip()
                    elif '```' in optimized_latex:
                        optimized_latex = optimized_latex.split('```')[1].split('```')[0].strip()
                    
                    # Write optimized LaTeX
                    main_tex = variant_dir / "main.tex"
                    with open(main_tex, 'w', encoding='utf-8') as f:
                        f.write(optimized_latex)
                    
                    result['message'] += ' | AI optimized successfully'
                    
                    # Auto-compile PDF
                    try:
                        compile_success = compile_cv_internal(folder_name)
                        if compile_success:
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
        
        if not folder_name:
            return jsonify({'error': 'Folder name is required'}), 400
        
        # Check ownership
        if not user_owns_variant(folder_name, current_user.id):
            return jsonify({'error': 'Access denied'}), 403
        
        variant_dir = V1_DIR / folder_name
        main_tex = variant_dir / "main.tex"
        
        if not main_tex.exists():
            return jsonify({'error': 'main.tex not found. Please optimize CV first.'}), 400
        
        # Use Docker to compile
        home_dir = Path.home()
        temp_tex = home_dir / f"{folder_name}-cv.tex"
        
        # Copy tex file to home directory (Docker can access it)
        subprocess.run(['cp', str(main_tex), str(temp_tex)], check=True)
        
        # Compile with Docker
        result = subprocess.run([
            'docker', 'run', '--rm',
            '-v', f'{home_dir}:/workspace',
            '-w', '/workspace',
            'texlive/texlive:latest',
            'latexmk', '-pdf', f'{folder_name}-cv.tex'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return jsonify({'error': f'Compilation failed: {result.stderr}'}), 500
        
        # Copy PDF back
        temp_pdf = home_dir / f"{folder_name}-cv.pdf"
        output_pdf = variant_dir / "main.pdf"
        
        if temp_pdf.exists():
            subprocess.run(['cp', str(temp_pdf), str(output_pdf)], check=True)
            # Cleanup temp files
            for ext in ['tex', 'pdf', 'aux', 'log', 'out', 'fls', 'fdb_latexmk']:
                temp_file = home_dir / f"{folder_name}-cv.{ext}"
                if temp_file.exists():
                    temp_file.unlink()
            
            return jsonify({
                'success': True,
                'message': 'CV compiled successfully',
                'pdf_path': str(output_pdf)
            })
        else:
            return jsonify({'error': 'PDF not generated'}), 500
    
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Compilation timeout (60s)'}), 500
    except Exception as e:
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
