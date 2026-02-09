# Hướng dẫn sử dụng Vibe CV Resume

## 🚀 Setup ban đầu

### Bước 1: Cài đặt môi trường

Chọn 1 trong 2 cách:

#### Cách 1 - Docker (Recommended)

1. Cài đặt [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Cài VS Code extension [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
3. Mở project trong VS Code
4. Khi được hỏi, chọn **"Reopen in Container"**
5. Done! File `.tex` sẽ tự động compile khi save

#### Cách 2 - Manual (Mac ARM)

```bash
# Cài đặt MacTeX
brew install --cask mactex-no-gui

# Thêm TeX vào PATH
eval "$(/usr/libexec/path_helper)"

# Verify installation
latexmk --version
```

**Lưu ý:** Hướng dẫn manual hiện chỉ có cho Mac ARM. Đóng góp hướng dẫn cho các platform khác được hoan nghênh!

---

## 📝 Workflow thực tế

### Bước 1: Chuẩn bị CV master

Chỉnh sửa `v1/master.tex` với thông tin thật của bạn:

- **Thông tin cá nhân**: Thay "Budi Santoso" → tên bạn
- **Contact**: Update email, phone, LinkedIn, GitHub, portfolio
- **Summary**: Viết tóm tắt về background và expertise
- **Experience**: Điền kinh nghiệm làm việc thật (công ty, vị trí, thành tích)
- **Education**: Cập nhật học vấn
- **Skills**: List các skills và công nghệ bạn biết

```bash
# Mở file master.tex
code v1/master.tex

# Hoặc compile để xem PDF
cd v1
latexmk -pdf master.tex
open master.pdf
```

---

### Bước 2: Khi có job mới muốn apply

```bash
# Tạo folder cho job đó (đặt tên theo công ty hoặc vị trí)
mkdir -p v1/google-swe

# Tạo file job description
touch v1/google-swe/job_desc.md
```

Copy toàn bộ job description từ website vào `v1/google-swe/job_desc.md`.

---

### Bước 3: Dùng AI agent tối ưu CV

Mở chat với AI coding agent (Claude/Cursor/GitHub Copilot) và gửi prompt:

```
Tôi có:
- CV master: v1/master.tex
- Job description: v1/google-swe/job_desc.md  
- Prompt template: prompts/job_desc_match.md

Hãy:
1. Phân tích job description theo framework trong job_desc_match.md
2. Tạo v1/google-swe/main.tex tối ưu cho JD này từ master.tex
3. Reorder experience section để phù hợp với role requirements
4. Update summary và skills section với keywords từ JD
5. Đảm bảo ATS-friendly (tối ưu cho Applicant Tracking System)
6. Giữ nguyên format và structure của LaTeX template
```

AI agent sẽ:
- Phân tích JD để tìm mandatory skills, nice-to-have, keywords
- Sắp xếp lại thứ tự kinh nghiệm (ưu tiên relevant experience lên trước)
- Viết lại summary để match với role
- Highlight relevant skills và technologies
- Optimize bullet points với action verbs và quantified results

---

### Bước 4: Review và compile PDF

```bash
# Di chuyển vào folder job-specific
cd v1/google-swe

# Compile LaTeX thành PDF
latexmk -pdf main.tex

# Mở PDF để review
open main.pdf  # macOS
# hoặc xdg-open main.pdf  # Linux
# hoặc start main.pdf  # Windows
```

**Review checklist:**
- [ ] Contact info chính xác
- [ ] Summary match với JD
- [ ] Relevant experience lên trước
- [ ] Keywords từ JD có trong CV
- [ ] Số liệu và metrics rõ ràng
- [ ] Không có lỗi chính tả
- [ ] PDF format đẹp, dễ đọc

---

### Bước 5: Version control với Git

```bash
# Stage changes
git add v1/google-swe/

# Commit với message rõ ràng
git commit -m "Optimize CV for Google SWE role"

# Tag để dễ tìm sau này
git tag google-swe-2026-02-09

# Push lên remote (nếu cần)
git push origin main --tags
```

---

## 💡 Ví dụ có sẵn trong repo

Xem folder `v1/canva/` để tham khảo cách optimize:

### So sánh master.tex vs canva/main.tex

| Aspect | master.tex | canva/main.tex |
|--------|-----------|----------------|
| **Summary** | Focus Frontend Engineer | Nhấn mạnh Python, LLM, RAG |
| **Experience order** | Tiket.com → ITB → Bukalapak | ITB (AI) → Tiket.com → Bukalapak |
| **Skills section** | Frontend-heavy | AI/ML tools lên đầu |
| **Match** | Generic | Tối ưu cho Canva AI role |

### Files trong canva/:
- `job_desc.md` - Job description từ Canva
- `main.tex` - CV đã optimize dựa trên JD

**Lesson learned:**
- AI Research experience được đưa lên đầu vì Canva tìm AI role
- Summary được viết lại để nhấn mạnh "AI, LLM integration, RAG systems"
- Skills section thêm LangChain, OpenAI API, HuggingFace

---

## 🎯 Tips và Best Practices

### 1. Tái sử dụng prompt hiệu quả

```bash
# Template cho mỗi job mới:
mkdir v1/<company>-<role>
cp v1/canva/job_desc.md v1/<company>-<role>/
# Edit job_desc.md với JD mới
# Chạy lại prompt với AI agent
```

### 2. Branch strategy cho nhiều applications

```bash
# Tạo branch cho đợt apply tháng này
git checkout -b applications-feb-2026

# Tạo nhiều variants
mkdir v1/meta-ml v1/google-ai v1/openai-research

# Apply cho từng job...

# Commit tất cả
git add v1/
git commit -m "Feb 2026 job applications batch"

# Push branch
git push origin applications-feb-2026
```

### 3. So sánh changes giữa versions

```bash
# Xem AI agent đã thay đổi gì
diff v1/master.tex v1/canva/main.tex

# Hoặc dùng Git
git diff v1/master.tex v1/google-swe/main.tex

# Visual diff trong VS Code
code --diff v1/master.tex v1/canva/main.tex
```

### 4. Maintain master.tex updated

```bash
# Sau khi có kinh nghiệm mới hoặc skills mới
code v1/master.tex

# Update và commit
git add v1/master.tex
git commit -m "Add new experience at Company X"

# Regenerate các variants nếu cần
# AI agent có thể incorporate new experience vào variants
```

### 5. Quick commands

```bash
# Compile tất cả CVs
find v1 -name "*.tex" -exec latexmk -pdf {} \;

# Clean build files
find v1 -name "*.aux" -o -name "*.log" -o -name "*.fls" | xargs rm

# Count số variants
ls -d v1/*/ | wc -l

# Tìm CV theo keyword
grep -r "Python" v1/*/main.tex
```

---

## 🔍 Troubleshooting

### LaTeX không compile

```bash
# Kiểm tra TeX installation
which pdflatex
latexmk --version

# Reinstall (Mac)
brew reinstall --cask mactex-no-gui

# Check log file để xem lỗi
cat v1/master.log
```

### Docker container không start

```bash
# Rebuild container
# Command Palette (Cmd/Ctrl+Shift+P)
# > Dev Containers: Rebuild Container

# Hoặc xóa và rebuild
docker system prune -a
# Reopen in Container
```

### AI agent không hiểu LaTeX

**Tips:**
- Đảm bảo AI agent có context về LaTeX
- Paste cả template structure trong prompt
- Yêu cầu preserve formatting và custom commands
- Test với 1 section nhỏ trước

### PDF không mở được

```bash
# Check file tồn tại
ls -lh v1/google-swe/main.pdf

# Recompile clean
cd v1/google-swe
latexmk -C  # Clean
latexmk -pdf main.tex  # Rebuild
```

---

## 📚 Advanced Usage

### Custom LaTeX template

Nếu muốn đổi template design:

1. Backup master.tex
2. Thay đổi preamble (packages, custom commands)
3. Test compile
4. Update tất cả variants nếu cần

### Multi-language CVs

```bash
# Tạo structure cho mỗi ngôn ngữ
mkdir v1/master-en v1/master-vi v1/master-ja

# Maintain translations
# AI agent có thể giúp translate content
```

### ATS Testing

Tools để test ATS compatibility:
- [Resume Worded](https://resumeworded.com/)
- [Jobscan](https://www.jobscan.co/)
- Upload PDF và check score

### Automation với scripts

```bash
# Script tự động compile tất cả
cat > compile-all.sh << 'EOF'
#!/bin/bash
for dir in v1/*/; do
    if [ -f "$dir/main.tex" ]; then
        cd "$dir"
        latexmk -pdf main.tex
        cd ../..
    fi
done
EOF

chmod +x compile-all.sh
./compile-all.sh
```

---

## 🤝 Contributing

Đóng góp được hoan nghênh! Đặc biệt:

- Setup instructions cho Windows, Linux, Mac Intel
- Prompt templates mới (interview prep, portfolio, etc.)
- LaTeX templates khác nhau (modern, minimal, colorful)
- Automation scripts

---

## 📖 Resources

### LaTeX Learning
- [Overleaf Documentation](https://www.overleaf.com/learn)
- [LaTeX Wikibook](https://en.wikibooks.org/wiki/LaTeX)

### CV Writing
- [Harvard Resume Guide](https://hwpi.harvard.edu/files/ocs/files/hes-resume-cover-letter-guide.pdf)
- [Google XYZ Method](https://www.inc.com/bill-murphy-jr/google-recruiters-say-these-5-resume-tips-including-x-y-z-formula-will-improve-your-odds-of-getting-hired-at-google.html)

### AI Prompting
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [OpenAI Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)

---

## 📞 Support

Nếu có câu hỏi hoặc gặp issue:
- Open issue trên GitHub
- Check [README.md](README.md) cho overview
- Xem [prompts/job_desc_match.md](prompts/job_desc_match.md) cho prompt reference

---

**Happy job hunting! 🚀**
