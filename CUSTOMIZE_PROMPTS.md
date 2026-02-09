# 🎯 Hướng Dẫn Tùy Chỉnh Prompts - Vibe CV Resume Builder

## Tổng Quan

Có 2 loại prompt chính trong hệ thống:

1. **Job Matching Prompt** - Phân tích và đánh giá CV vs Job Description
2. **CV Optimization Prompt** - Tối ưu hóa CV theo job description

---

## 📍 Vị Trí Files Cần Chỉnh Sửa

### 1. File Prompt Template (Recommended)
```
prompts/job_desc_match.md
```
- Đây là file template chứa hướng dẫn chi tiết cho AI
- Được load tự động khi optimize CV
- **Nên chỉnh sửa file này** thay vì code trực tiếp

### 2. Code Prompt (Advanced)
```
web/app.py
Function: call_ai_to_optimize_cv() (dòng 152-178)
```
- Prompt được hard-code trong Python
- Chỉ sửa nếu cần thay đổi cấu trúc hoặc logic

---

## 🎨 Các Điểm Chỉnh Sửa Để CV Sát Thực Tế Hơn

### A. Trong File `prompts/job_desc_match.md`

#### 1. **Thêm Context Về Ngành/Lĩnh Vực**
Thêm vào phần "Role Definition":
```markdown
### Role Definition
You are a strict, analytical recruitment evaluation system with expertise in:
- [THÊM NGÀNH CỤ THỂ: Tech, Finance, Marketing, etc.]
- [THÊM MARKET: Vietnam, Asia-Pacific, Global]
- [THÊM COMPANY SIZE: Startup, Enterprise, SME]

You understand:
- Local market standards and salary expectations
- Industry-specific terminology in both English and Vietnamese
- Cultural nuances in CV presentation for [TARGET REGION]
```

#### 2. **Customize Scoring Weights**
Chỉnh sửa phần "Scoring Methodology":
```markdown
### Scoring Methodology
Calculate weighted scores:
- **Core Skills**: 35% (hard requirements)
- **Experience**: 30% (years + relevance)
- **Tools/Tech**: 20% (specific technologies)
- **Soft Skills**: 10% (communication, leadership)
- **Education**: 5% (degrees, certifications)

[ĐIỀU CHỈNH % TÙY THEO NGÀNH]
```

#### 3. **Thêm Industry-Specific Keywords**
Thêm section mới:
```markdown
### Industry Context Rules
For [YOUR INDUSTRY]:
- Key technologies: [React, Node.js, AWS, etc.]
- Standard certifications: [AWS Certified, PMP, etc.]
- Common job titles: [Senior Developer, Tech Lead, etc.]
- Red flags: [job hopping every 6 months, etc.]
```

#### 4. **Tùy Chỉnh Gap Detection**
Sửa phần "Gap and Risk Detection":
```markdown
### Gap and Risk Detection
Critical evaluation points:
- Missing mandatory requirements (automatic rejection)
- **Over-qualification risks** (may leave quickly)
- **Under-qualification gaps** (training needed)
- Career trajectory inconsistencies
- [THÊM: Location mismatch, visa requirements, etc.]

Rejection triggers specific to [YOUR REGION]:
- [Lack of work permit/visa]
- [Unrealistic salary expectations]
- [Too short notice period]
```

### B. Trong Code `web/app.py`

#### 1. **Tăng Độ Chính Xác Technical Details**

Tìm dòng 168-178, sửa `user_prompt`:

```python
user_prompt = f"""Please optimize this CV for the following job:

JOB DESCRIPTION:
{job_desc_content}

MASTER CV (LaTeX):
{master_tex_content}

CRITICAL OPTIMIZATION RULES:
1. **Quantify Everything**: Add numbers, percentages, metrics
   - Bad: "Improved system performance"
   - Good: "Reduced API response time by 40% (from 500ms to 300ms)"

2. **Use Action Verbs**: Led, Designed, Implemented, Reduced, Increased
   - Avoid: "Responsible for", "Worked on", "Helped with"

3. **Show Impact & Scale**:
   - Add team size: "Led team of 5 developers"
   - Add user scale: "System serving 10K+ daily active users"
   - Add business value: "Generated $500K additional revenue"

4. **Match Job Keywords NATURALLY**:
   - If JD mentions "microservices", use "microservices" not "micro-services"
   - Copy exact technology names: React.js, AWS Lambda, PostgreSQL
   - Use industry-standard abbreviations

5. **Realistic Claims Only**:
   - DO NOT add skills/experience not in master CV
   - DO NOT inflate years of experience
   - DO NOT add fake projects or companies
   - Only REWORD and EMPHASIZE existing experience

6. **Professional Formatting**:
   - Bullet points: 1-2 lines max
   - Dates: MM/YYYY format
   - Consistent tense: Past for old jobs, Present for current

7. **Keep Structure**:
   - Copy ALL LaTeX preamble and custom commands
   - Maintain all \\newcommand definitions
   - Preserve formatting packages

FOCUS AREAS FOR THIS JD:
- Match: [EXTRACT TOP 3 KEYWORDS FROM JD]
- Emphasize: [IDENTIFY MOST RELEVANT PAST ROLE]
- Highlight: [KEY ACHIEVEMENT MATCHING JD]

OUTPUT: Pure LaTeX code only, starting with \\documentclass"""
```

#### 2. **Thêm Temperature Tuning**

Tìm dòng 192, điều chỉnh `temperature`:

```python
# Giảm temperature để CV ổn định hơn, ít "sáng tạo" hơn
temperature=0.3,  # Thay vì 0.7
max_tokens=5000,  # Tăng lên nếu CV dài
```

#### 3. **Thêm Context About User**

Thêm function mới để extract thông tin user:

```python
def extract_user_context(master_tex_content):
    """Extract key info from master CV for better optimization"""
    import re
    
    # Extract years of experience
    years_match = re.search(r'(\d+)\+?\s*years?\s+(?:of\s+)?experience', master_tex_content, re.I)
    years = int(years_match.group(1)) if years_match else 0
    
    # Extract tech stack
    tech_keywords = ['Python', 'Java', 'React', 'Node', 'AWS', 'Docker', 'Kubernetes']
    user_tech = [tech for tech in tech_keywords if tech.lower() in master_tex_content.lower()]
    
    return {
        'years_experience': years,
        'tech_stack': user_tech,
        'seniority': 'Senior' if years >= 5 else 'Mid' if years >= 2 else 'Junior'
    }
```

Sau đó update `call_ai_to_optimize_cv`:

```python
def call_ai_to_optimize_cv(master_tex_content, job_desc_content, prompt_template):
    # Thêm context extraction
    user_context = extract_user_context(master_tex_content)
    
    system_prompt = f"""You are optimizing a CV for a {user_context['seniority']} candidate with:
- {user_context['years_experience']} years experience
- Tech stack: {', '.join(user_context['tech_stack'])}

Your optimization must:
1. Stay true to candidate's actual level
2. Not over-promise or exaggerate
3. Match realistic expectations for their seniority
...
```

---

## 🔧 Quick Wins - Top 5 Tweaks Cho CV Sát Thực Tế

### 1. **Thêm Metrics Template**
Trong `prompts/job_desc_match.md`, thêm:
```markdown
### Quantification Examples
Transform vague statements:
- "Improved performance" → "Reduced load time by 35% (2.1s to 1.4s)"
- "Led team" → "Led cross-functional team of 8 engineers"
- "Built system" → "Architected system handling 50K requests/day"
```

### 2. **Disable Hallucinations**
Trong code, thêm vào `system_prompt`:
```python
system_prompt = f"""
STRICT RULES - NO EXCEPTIONS:
- NEVER add skills not in original CV
- NEVER fabricate project names or companies
- NEVER increase years of experience
- ONLY reword and emphasize EXISTING content
...
```

### 3. **Add ATS Keyword Density Check**
```python
# Trong prompt
"Ensure 8-12% keyword density from JD without keyword stuffing"
```

### 4. **Cultural Localization**
Thêm vào prompt:
```python
f"""For Vietnam market specifically:
- Use Vietnamese company names correctly
- Follow Vietnamese date format conventions
- Include expected salary range expectations for role level
- Mention visa/work permit status if applicable
"""
```

### 5. **Add Reality Check Section**
```markdown
### Post-Optimization Verification
Before returning optimized CV, verify:
- [ ] All quantified metrics are realistic
- [ ] No invented technologies or tools
- [ ] Seniority claims match years of experience
- [ ] No contradictions with original CV timeline
```

---

## 🧪 Testing Your Prompts

### Test Cases
```bash
# 1. Test với job description thật
curl -X POST http://localhost:5000/api/create-variant \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "role_name": "Test Role",
    "job_description": "[PASTE REAL JD HERE]",
    "auto_optimize": true
  }'

# 2. So sánh trước và sau
diff v1/master.tex v1/test-company-test-role/main.tex
```

### Đánh Giá Chất Lượng
- ✅ Metrics có cụ thể không?
- ✅ Keywords tự nhiên không?
- ✅ Có thêm skill fake không?
- ✅ Format nhất quán không?
- ✅ PDF compile được không?

---

## 📚 Resources & Examples

### Ví Dụ Prompt Tốt
```
"Led development of microservices architecture serving 100K+ MAU, 
reducing deployment time from 2 hours to 15 minutes using Docker + K8s"
```

### Ví Dụ Prompt Tệ
```
"Worked on improving things and making stuff better with modern tech stack"
```

### Keywords By Industry

**Tech/Software:**
```
- DevOps: CI/CD, Docker, Kubernetes, Jenkins, GitLab
- Backend: REST API, GraphQL, Microservices, Message Queue
- Frontend: React, Vue, TypeScript, Responsive Design
- Cloud: AWS (EC2, S3, Lambda), Azure, GCP
- Database: PostgreSQL, MongoDB, Redis, MySQL
```

**Finance:**
```
- Compliance: KYC, AML, GDPR, Basel III
- Systems: Core Banking, Payment Gateway, Trading Platform
- Skills: Risk Management, Financial Modeling, Audit
```

---

## ⚠️ Lưu Ý Quan Trọng

1. **Backup trước khi sửa**: 
   ```bash
   cp prompts/job_desc_match.md prompts/job_desc_match.md.backup
   cp web/app.py web/app.py.backup
   ```

2. **Test từng thay đổi**: Đừng sửa tất cả cùng lúc

3. **Monitor AI output**: Check log để xem AI có follow instructions không

4. **Iterate**: Prompt engineering cần thử nghiệm nhiều lần

---

## 🚀 Advanced: Multi-Language Support

Nếu muốn support CV tiếng Việt:

```python
def detect_cv_language(master_tex_content):
    vietnamese_chars = sum(1 for c in master_tex_content if ord(c) > 127)
    total_chars = len(master_tex_content)
    
    if vietnamese_chars / total_chars > 0.1:
        return 'vi'
    return 'en'

# Trong call_ai_to_optimize_cv:
lang = detect_cv_language(master_tex_content)
if lang == 'vi':
    system_prompt += "\nOutput CV must be in VIETNAMESE language with proper diacritics"
```

---

## 💡 Tips From Production Use

1. **Giảm hallucination**: Temperature 0.1-0.3 tốt hơn 0.7
2. **Tăng context**: Cho AI thấy cả JD requirements + user background
3. **Use examples**: Thêm 2-3 ví dụ "before/after" trong prompt
4. **Validate output**: Parse LaTeX để check syntax trước khi save
5. **Version prompts**: Git commit mỗi lần thay đổi prompt để track performance

---

## 📞 Support

Nếu cần customize thêm, edit files:
- `prompts/job_desc_match.md` - Main prompt template
- `web/app.py` line 152-210 - CV optimization logic
- `web/app.py` line 250-295 - CV upload conversion

Sau khi sửa, restart server:
```bash
pkill -9 python && cd /Applications/Soft/vibe-cv-resume && python web/app.py
```
