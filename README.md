# CV Resume Agentic Building

Maintain your CV at a higher level of abstraction using coding agents, now with a web UI for AI-powered CV optimization.

https://github.com/user-attachments/assets/0ef93cae-9ad0-4564-a6ef-3d8f5d3aec4c

---

## ✨ What's New

🚀 **Web UI with AI Auto-Optimization** - Create job-specific CV variants through a beautiful web interface  
🔐 **Multi-User Authentication** - Secure login system with user isolation  
🤖 **AI Integration** - GPT-4 and Claude automatically optimize your CV for each job  
📦 **One-Click Compilation** - Auto-compile LaTeX to PDF with Docker  
🎨 **Modern Interface** - Responsive design with Tailwind CSS

---

## Motivation

2025 changed how we code. We now work with AI agents that understand context, make intelligent edits, and iterate on feedback. So why are we still manually tweaking CV bullet points and reformatting layouts by hand?

**The problem:** CV maintenance is tedious. Every job application means copying content, adjusting formatting, and hoping you didn't break the layout. Version control is an afterthought. Tailoring for ATS systems feels like guesswork.

**The solution:** Treat your CV like code. LaTeX provides the structure. AI provides the intelligence. Git provides the history. You provide the direction.

**The upgrade:** Now with a web interface that lets you create, optimize, and compile CV variants without touching the terminal. Paste a job description, click a button, download your tailored PDF.

---

## Why This Approach Works

- **LaTeX decouples content from presentation** - Change your layout without touching your achievements. Update your experience without breaking your design.
- **Agents can edit LaTeX like any code** - They understand the structure, can make targeted changes, and iterate based on your feedback.
- **Git provides versioning, branching, and tracking** - See exactly what changed between versions. Branch for different job applications. Tag your submissions.

---

## Use Cases

### Web UI Mode (New!)
1. **One-click CV optimization** - Paste job description, AI tailors your CV, compile PDF instantly
2. **Multi-user CV management** - Team members can manage their own CV variants independently
3. **Real-time compilation** - See your PDF within 60 seconds of creating a variant
4. **Version tracking** - All variants stored and accessible through the dashboard

### Agent Mode (Original)
1. **Match CV to job descriptions for higher ATS scores** - Feed in a job posting and let the agent optimize your bullet points for keyword alignment
2. **Optimize achievement writing** - Transform weak bullets into quantified, action-driven statements
3. **Change layout without touching content** - Swap templates or adjust formatting while preserving your carefully crafted text
4. **Get expert CV reviewer evaluation** - Use agents to critique your CV like a professional recruiter would
5. **Version and branch for different applications** - Maintain a master CV while creating targeted variants for specific roles

---

## Folder Structure

```
├── prompts/                    # AI prompt templates for CV operations
│   └── job_desc_match.md       # CV-to-job-description matching prompt
├── v1/                         # Version 1 of CV templates
│   ├── master.tex              # Base CV - your source of truth
│   └── [company-role]/         # Job-specific variant folders
│       ├── main.tex            # Optimized CV for this application
│       ├── main.pdf            # Compiled PDF
│       ├── job_desc.md         # Target job description
│       └── .owner              # User ownership tracking
├── web/                        # Web UI application
│   ├── app.py                  # Flask backend with auth & AI
│   ├── templates/              # HTML templates (login, register, dashboard)
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # API keys and secrets (gitignored)
│   ├── users.json              # User database (gitignored)
│   ├── AUTH.md                 # Authentication documentation
│   ├── README.md               # Web UI documentation
│   └── SETUP.md                # Setup instructions
└── .devcontainer/              # Docker dev container config
```

### How the folders work

- **`prompts/`** - Collection of battle-tested prompts for specific use cases. Start with `job_desc_match.md` to tailor your CV for a specific role.
- **`v1/`** - Folder-based versioning. `master.tex` is your base CV. Job-specific variants are auto-created in subfolders.
- **`web/`** - Flask web application with authentication, AI integration, and PDF compilation. Run locally for full control.

---

## What You Get

### Web UI Features
- **🔐 User Authentication** - Secure email/password login with Flask-Login
- **🤖 AI Auto-Optimization** - GPT-4 or Claude automatically tailors your CV
- **📦 Docker Integration** - One-click LaTeX compilation to PDF
- **👥 Multi-User Support** - Each user's CVs are isolated and private
- **📱 Responsive Design** - Works beautifully on desktop and mobile
- **⚡ Real-Time Progress** - See optimization and compilation status live

### Core Features
- **Zero LaTeX setup** - Docker handles the entire TeX Live installation
- **Battle-tested template** - A clean, professional CV layout that compiles reliably
- **Working agent prompts** - Prompts that actually work with Claude, GPT-4, and other coding agents
- **Workflow examples** - See how to structure job-specific variants

---

## Quick Start

### Option 1: Web UI with AI Auto-Optimization (Recommended)

#### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) - For LaTeX compilation
- Python 3.7+ - For Flask backend
- OpenAI or Anthropic API key - For AI optimization

#### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/markhah8/vibe-cv-resume.git
   cd vibe-cv-resume
   ```

2. **Install Python dependencies**
   ```bash
   cd web
   pip install -r requirements.txt
   ```

3. **Configure AI API**
   ```bash
   cp .env.example .env
   # Edit .env and add your API key:
   # OPENAI_API_KEY=sk-proj-your-key-here
   # or
   # ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

4. **Start Docker Desktop**
   ```bash
   open -a Docker  # Mac
   # or start Docker Desktop manually
   ```

5. **Run the web server**
   ```bash
   python app.py
   ```

6. **Open your browser**
   - Navigate to `http://localhost:5000`
   - Default login: `admin@vibe-cv.com` / `admin123`
   - Or create a new account

#### Usage Flow
1. **Login** to your account
2. **Fill the form**: Company name, role, job description
3. **Click "Create & Auto-Optimize"**
4. **Wait ~30-60 seconds** while AI optimizes and compiles
5. **Download your PDF** - Ready to submit!

For detailed documentation, see:
- [web/README.md](web/README.md) - Web UI documentation
- [web/SETUP.md](web/SETUP.md) - Detailed setup instructions
- [web/AUTH.md](web/AUTH.md) - Authentication system details

---

### Option 2: Dev Container (VS Code)

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Fork this repository
3. Clone your fork and open in VS Code
4. Click **"Reopen in Container"** when prompted
5. Edit `v1/master.tex` and save - your PDF appears automatically

---

### Option 3: Manual LaTeX Setup

Install [LaTeX Workshop extension](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop) for VS Code.

#### Mac ARM

1. `brew install --cask mactex-no-gui`
2. Add TeX to PATH:
   - **bash/zsh:** `eval "$(/usr/libexec/path_helper)"`
   - **other shells:** add `/usr/local/texlive/YYYY/bin/universal-darwin` to PATH (replace `YYYY` with your installed TeX Live version year)
3. Verify installation: `latexmk -pdf v1/master.tex`

Currently, these manual setup instructions are documented for **Mac ARM only**. Contributions for other platforms (Mac Intel, Windows, Linux) are welcome.

---

## Technology Stack

### Backend
- **Flask 3.0** - Python web framework
- **Flask-Login** - User authentication and session management
- **Werkzeug** - Password hashing with scrypt
- **OpenAI API** - GPT-4 Turbo for CV optimization
- **Anthropic API** - Claude 3.5 Sonnet alternative

### Frontend
- **Tailwind CSS** - Modern responsive design
- **Font Awesome** - Icons and visual elements
- **Vanilla JavaScript** - AJAX interactions

### Infrastructure
- **Docker** - LaTeX compilation with TeXLive
- **JSON** - Simple user database (no external DB needed)
- **Git** - Version control for CV variants

---

## Security & Privacy

🔒 **Password Security**
- Passwords hashed with Werkzeug scrypt (32768 rounds)
- Never stored in plain text
- Session-based authentication

🔐 **Data Isolation**
- Each user sees only their own CVs
- `.owner` files track variant ownership
- 403 Forbidden on unauthorized access

⚠️ **Important**: 
- Keep your `.env` file secure (contains API keys)
- Don't commit `users.json` to public repositories
- API keys in this repo's `.gitignore`

---

## Contributing

Contributions welcome! Areas of interest:
- **Platform setup docs** - Windows, Linux installation guides
- **UI/UX improvements** - Design enhancements, accessibility
- **New AI providers** - Additional LLM integrations
- **Features** - PDF preview, version comparison, ATS scoring
- **Templates** - More LaTeX CV layouts

---

## License

This project builds on the original [vibe-cv-resume](https://github.com/madnanrizqu/vibe-cv-resume) concept by adding web UI and multi-user capabilities.

---

## Documentation

- [USAGE.md](USAGE.md) - Vietnamese usage guide
- [QUICKSTART.md](QUICKSTART.md) - Quick reference
- [web/README.md](web/README.md) - Web UI documentation
- [web/SETUP.md](web/SETUP.md) - Detailed setup
- [web/AUTH.md](web/AUTH.md) - Authentication system

---

## Troubleshooting

### Docker Not Running
```bash
open -a Docker  # Mac
# Wait 30s for Docker to start
```

### API Key Issues
- Check `.env` file exists in `web/` folder
- Verify API key format (starts with `sk-proj-` for OpenAI)
- Test key at [platform.openai.com](https://platform.openai.com)

### Compilation Fails
- Ensure Docker Desktop is running
- Check `main.tex` for LaTeX syntax errors
- View logs in terminal output

### Port 5000 Already in Use
```bash
# Kill existing Flask process
pkill -f "python.*app.py"
# Or change port in app.py
```

For more issues, see [web/README.md](web/README.md) troubleshooting section.

