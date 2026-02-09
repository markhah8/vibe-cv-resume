#!/usr/bin/env python3
"""
Web UI for Vibe CV Resume Builder
Automates job-specific CV variant creation with AI optimization
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import subprocess
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import openai
import anthropic

# Load environment variables
load_dotenv()

app = Flask(__name__)

# AI Configuration
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')
AI_MODEL = os.getenv('AI_MODEL', 'gpt-4-turbo')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Project paths
BASE_DIR = Path(__file__).parent.parent
V1_DIR = BASE_DIR / "v1"
MASTER_TEX = V1_DIR / "master.tex"

def sanitize_folder_name(name):
    """Convert company/role name to valid folder name"""
    name = re.sub(r'[^\w\s-]', '', name.lower())
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')

def get_existing_variants():
    """Get list of existing CV variants"""
    variants = []
    if not V1_DIR.exists():
        return variants
    
    for item in V1_DIR.iterdir():
        if item.is_dir() and item.name not in ['.git', '__pycache__', 'canva']:
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

CRITICAL: Return ONLY the LaTeX code. No explanations, no markdown code blocks, just pure LaTeX starting with \\documentclass"""

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
- Keeping all formatting and structure intact"""

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
                model=AI_MODEL,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            return response.content[0].text.strip()
        
        else:
            return None
    
    except Exception as e:
        print(f"AI Error: {e}")
        return None


@app.route('/api/create-variant', methods=['POST'])
def create_variant():
    """Create new CV variant folder, job description, and auto-optimize with AI"""
    try:
        data = request.json
        company_name = data.get('company_name', '').strip()
        role_name = data.get('role_name', '').strip()
        job_description = data.get('job_description', '').strip()
        auto_optimize = data.get('auto_optimize', True)
        
        if not company_name or not job_description:
            return jsonify({'error': 'Company name and job description are required'}), 400
        
        # Create folder name
        if role_name:
            folder_name = sanitize_folder_name(f"{company_name}-{role_name}")
        else:
            folder_name = sanitize_folder_name(company_name)
        
        variant_dir = V1_DIR / folder_name
        
        # Check if folder exists
        if variant_dir.exists():
            return jsonify({'error': f'Variant "{folder_name}" already exists'}), 400
        
        # Create folder
        variant_dir.mkdir(parents=True, exist_ok=True)
        
        # Create job_desc.md
        job_desc_file = variant_dir / "job_desc.md"
        with open(job_desc_file, 'w', encoding='utf-8') as f:
            f.write(f"# {company_name}")
            if role_name:
                f.write(f" - {role_name}")
            f.write("\n\n")
            f.write(job_description)
        
        result = {
            'success': True,
            'folder_name': folder_name,
            'message': f'Created variant folder: {folder_name}',
            'has_tex': False,
            'has_pdf': False
        }
        
        # Auto-optimize with AI if enabled and API key available
        if auto_optimize and (OPENAI_API_KEY or ANTHROPIC_API_KEY):
            try:
                # Read master CV
                with open(MASTER_TEX, 'r', encoding='utf-8') as f:
                    master_content = f.read()
                
                # Read prompt template
                prompt_file = BASE_DIR / "prompts" / "job_desc_match.md"
                prompt_template = ""
                if prompt_file.exists():
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        prompt_template = f.read()
                
                # Call AI to optimize
                optimized_tex = call_ai_to_optimize_cv(master_content, job_description, prompt_template)
                
                if optimized_tex:
                    # Clean up response (remove markdown code blocks if present)
                    if '```' in optimized_tex:
                        optimized_tex = optimized_tex.split('```')[1]
                        if optimized_tex.startswith('latex'):
                            optimized_tex = optimized_tex[5:]
                    
                    optimized_tex = optimized_tex.strip()
                    
                    # Save optimized CV
                    main_tex = variant_dir / "main.tex"
                    with open(main_tex, 'w', encoding='utf-8') as f:
                        f.write(optimized_tex)
                    
                    result['has_tex'] = True
                    result['message'] += ' | AI optimization completed'
                    
                    # Auto-compile PDF
                    try:
                        compile_success = compile_cv_internal(folder_name)
                        if compile_success:
                            result['has_pdf'] = True
                            result['message'] += ' | PDF compiled successfully'
                    except Exception as compile_error:
                        result['message'] += f' | PDF compilation failed: {str(compile_error)}'
                
                else:
                    result['message'] += ' | AI optimization skipped (no API response)'
            
            except Exception as ai_error:
                result['message'] += f' | AI optimization failed: {str(ai_error)}'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def compile_cv_internal(folder_name):
    """Internal function to compile CV (used by auto-optimize)"""
    variant_dir = V1_DIR / folder_name
    main_tex = variant_dir / "main.tex"
    
    if not main_tex.exists():
        return False
    
    # Use Docker to compile
    home_dir = Path.home()
    temp_tex = home_dir / f"{folder_name}-cv.tex"
    
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
                f.write(f" - {role_name}")
            f.write("\n\n")
            f.write(job_description)
        
        return jsonify({
            'success': True,
            'folder_name': folder_name,
            'message': f'Created variant folder: {folder_name}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compile-cv', methods=['POST'])
def compile_cv():
    """Compile LaTeX to PDF using Docker"""
    try:
        data = request.json
        folder_name = data.get('folder_name', '').strip()
        
        if not folder_name:
            return jsonify({'error': 'Folder name is required'}), 400
        
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

@app.route('/api/download-pdf/<folder_name>')
def download_pdf(folder_name):
    """Download compiled PDF"""
    try:
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

@app.route('/api/delete-variant/<folder_name>', methods=['DELETE'])
def delete_variant(folder_name):
    """Delete a variant folder"""
    try:
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
    print(f"🌐 Starting server at: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
