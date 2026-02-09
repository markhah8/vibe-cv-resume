# 🚀 Quick Start - Vibe CV với AI Auto-Optimization

## ✅ Hoàn thành rồi! Hệ thống đã sẵn sàng

Web UI đã được tích hợp **AI tự động optimize CV** - bạn không cần ra thêm lệnh thủ công nữa!

---

## 🎯 Workflow Tự Động (One-Click)

```
Điền form → Click "Create Variant" → Hệ thống tự động:
   ├─ Tạo folder
   ├─ 🤖 Gọi AI optimize CV
   ├─ 📄 Compile PDF
   └─ ✅ Hiện button Download
```

**Tất cả diễn ra tự động trong 1 request!**

---

## 🛠️ Setup API Key (Chỉ làm 1 lần)

### Bước 1: Lấy API Key
Chọn 1 trong 2:
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic Claude**: https://console.anthropic.com/settings/keys

### Bước 2: Cấu hình
```bash
cd /Applications/Soft/vibe-cv-resume/web
nano .env
```

Thay `your-key-here` bằng API key thật:
```env
AI_PROVIDER=openai
AI_MODEL=gpt-4-turbo
OPENAI_API_KEY=sk-proj-your-real-key-here
```

Hoặc dùng Claude:
```env
AI_PROVIDER=anthropic
AI_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-your-real-key-here
```

**Lưu ý**: Free tier OpenAI cần nạp tiền $5 minimum, Claude có free tier tốt hơn.

---

## 🎬 Sử dụng

### 1. Start Server
```bash
cd /Applications/Soft/vibe-cv-resume
python web/app.py
```

Output:
```
============================================================
🚀 Vibe CV Resume Builder - Web UI
============================================================
📁 Project Directory: /Applications/Soft/vibe-cv-resume
📄 Master CV: /Applications/Soft/vibe-cv-resume/v1/master.tex
🤖 AI Provider: OpenAI (gpt-4-turbo)
🌐 Starting server at: http://localhost:5000
============================================================
```

### 2. Mở trình duyệt
```
http://localhost:5000
```

### 3. Tạo CV variant
1. **Company Name**: Ví dụ `BIDV Bank`
2. **Role Name**: Ví dụ `Senior IT Manager`
3. **Job Description**: Copy/paste full job requirements
4. Click **"Create Variant"**

### 4. Theo dõi tiến trình
UI sẽ hiển thị 3 bước:
```
Step 1: ✓ Creating variant folder...
Step 2: ✓ AI optimizing CV... (15-30s)
Step 3: ✓ Compiling PDF... (10-20s)
```

### 5. Download PDF
Khi hoàn tất, button **"Download PDF"** sẽ xuất hiện → Click để tải CV đã optimize!

---

## 📁 Kết quả

Mỗi variant được lưu trong:
```
v1/bidv-bank-senior-it-manager/
├── job_desc.md          # Job requirements
├── main.tex             # CV đã optimize bởi AI
└── main.pdf             # PDF compiled
```

---

## 🔍 Xem nội dung đã optimize

Click icon 📄 bên cạnh variant để xem job description và main.tex đã được AI chỉnh sửa như thế nào.

---

## ⚙️ Technical Details

### AI Optimization Process
1. Đọc `master.tex` (CV gốc của bạn)
2. Đọc job description
3. Đọc prompt template từ `prompts/job_desc_match.md`
4. Gọi GPT-4/Claude với context đầy đủ
5. AI trả về LaTeX code đã optimize:
   - Summary viết lại theo job requirements
   - Experience reorder ưu tiên roles liên quan
   - Keywords từ JD được nhấn mạnh
   - Skills highlight theo yêu cầu

### Docker Compilation
- Image: `texlive/texlive:latest`
- Timeout: 60s
- Output: Professional 2-page PDF

### Endpoints
- `POST /api/create-variant`: Tạo variant + AI optimize + compile PDF
- `POST /api/compile-cv`: Compile lại PDF (nếu edit .tex manual)
- `GET /api/download-pdf/<folder>`: Download PDF
- `GET /api/get-job-desc/<folder>`: Xem job description
- `DELETE /api/delete-variant/<folder>`: Xóa variant

---

## 🐛 Troubleshooting

### Không có AI optimization
Kiểm tra:
```bash
cd /Applications/Soft/vibe-cv-resume/web
cat .env
```

Đảm bảo có API key hợp lệ:
```env
OPENAI_API_KEY=sk-proj-abc123...  # Không phải "your-key-here"
```

Test API key:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Docker not running
```bash
open -a Docker
# Đợi 30s để Docker khởi động
```

### Compilation failed
Check Docker logs:
```bash
docker ps -a
docker logs <container_id>
```

### Port 5000 đã dùng
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Hoặc dùng port khác
python web/app.py --port 5001
```

---

## 💡 Tips

### Tối ưu kết quả AI
- **Job description càng chi tiết càng tốt**: Copy full JD, không tóm tắt
- **Bullets points**: Giữ nguyên format bullets từ JD
- **Keywords**: AI sẽ tự động extract và nhấn mạnh

### Tiết kiệm API cost
- OpenAI GPT-4: ~$0.03-0.05/request
- Claude Sonnet: ~$0.01-0.02/request
- Dùng Claude nếu budget hạn chế

### Edit thủ công
Nếu AI result chưa ưng:
1. Download main.tex
2. Edit manual trong text editor
3. Upload lại hoặc dùng endpoint `/api/compile-cv`

### Multiple roles cùng company
```
bidv-bank-senior-it-manager
bidv-bank-it-project-lead
bidv-bank-digital-transformation-head
```
Tạo nhiều variants để so sánh!

---

## 📊 So sánh với workflow cũ

### Trước (Manual)
```
1. Create variant folder    - Manual command
2. Copy job_desc.md          - Manual command
3. Gọi AI agent              - Manual prompt
4. Paste AI output vào file  - Manual copy/paste
5. Compile PDF               - Manual command
6. Download PDF              - Manual file copy

Total: ~5-10 phút + 6 bước manual
```

### Bây giờ (Auto)
```
1. Điền form web UI
2. Click "Create Variant"
3. ☕ Chờ 30-60s
4. Click "Download PDF"

Total: ~1 phút + 2 clicks
```

**Tiết kiệm 80% thời gian!** 🎉

---

## 🎯 Example: Tạo CV cho BIDV Bank

### Input
- Company: `BIDV Bank`
- Role: `Senior IT Manager`
- JD:
```
BIDV Bank is seeking a Senior IT Manager to lead digital 
transformation initiatives. Requirements:
- 10+ years banking IT experience
- Leadership in core banking systems
- Agile project management
- Budget management $5M+
- Team management 20+ people
```

### Output (Tự động sau 45s)
```
✓ Variant created: bidv-bank-senior-it-manager
✓ AI optimized (GPT-4): 28s
✓ PDF compiled: 12s
📄 Download: bidv-bank-senior-it-manager-cv.pdf
```

### AI đã làm gì?
- Summary: "Senior IT Leader with 15+ years Banking & Finance, specializing in Core Banking Systems and Digital Transformation..."
- Experience reordered: MIRAE ASSET (Core Banking) lên đầu
- Bullets enhanced: "Led T24 core banking migration" → "Spearheaded T24 Core Banking System digital transformation ($8M budget, 25 team members)"
- Keywords added: Agile, Digital Transformation, Budget Management, Team Leadership
- Skills highlighted: Core Banking, Leadership, Project Management

---

## 🚀 Production Tips

### For serious usage:
1. **Git commit master.tex**: Luôn backup CV gốc
2. **Version control variants**: Git add các variants tốt để reuse
3. **API key security**: Không commit .env vào Git
4. **Cost monitoring**: OpenAI platform có usage dashboard
5. **Batch processing**: Tạo multiple variants cùng lúc để compare

---

## 📞 Support

Có vấn đề? Check:
1. Server logs trong terminal
2. Browser console (F12) để xem API errors
3. Docker logs: `docker logs $(docker ps -q)`
4. File `.env` có API key hợp lệ

---

**Chúc bạn thành công với CV hunting! 🎯**
