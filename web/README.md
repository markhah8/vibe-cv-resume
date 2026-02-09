# Vibe CV Resume Builder - Web UI

Web interface để tự động hóa việc tạo và quản lý CV variants cho các job applications khác nhau.

## 🎯 Features

- ✅ **Tạo CV Variants**: Nhập job description trên web, tự động tạo folder và files
- 📝 **Quản lý Variants**: Xem danh sách tất cả CV variants đã tạo
- 🔧 **Compile PDF**: Compile LaTeX thành PDF ngay trên web (cần Docker)
- 📥 **Download**: Download PDF đã compile
- 🗑️ **Delete**: Xóa variants không cần thiết

## 🚀 Quick Start

### 1. Cài đặt dependencies

```bash
cd web
pip install -r requirements.txt
```

### 2. Chạy web server

```bash
python app.py
```

Hoặc:

```bash
# Make it executable
chmod +x app.py
./app.py
```

### 3. Mở trình duyệt

Truy cập: **http://localhost:5000**

## 📖 Cách sử dụng

### Tạo CV Variant mới

1. Mở web UI (http://localhost:5000)
2. Điền thông tin:
   - **Company Name** (bắt buộc): Tên công ty
   - **Role Name** (tùy chọn): Tên vị trí
   - **Job Description** (bắt buộc): Paste toàn bộ job description
3. Click "Create Variant"
4. Hệ thống tự động tạo:
   - Folder: `v1/{company-role}/`
   - File: `v1/{company-role}/job_desc.md`

### Optimize CV với AI Agent

Sau khi tạo variant:

1. Mở AI coding agent (Claude/Cursor/Copilot)
2. Gửi prompt:

```
Tôi có:
- CV master: v1/master.tex
- Job description: v1/{company-role}/job_desc.md  
- Prompt template: prompts/job_desc_match.md

Hãy:
1. Phân tích JD theo framework trong job_desc_match.md
2. Tạo v1/{company-role}/main.tex tối ưu từ master.tex
3. Reorder experience phù hợp với JD
4. Update summary và skills với keywords từ JD
5. Đảm bảo ATS-friendly
```

### Compile và Download PDF

1. Sau khi AI tạo `main.tex`, click button "Compile" trong danh sách variants
2. Đợi 30-60 giây (Docker compile LaTeX)
3. Click "Download" để tải PDF

## 🔧 Requirements

- **Python 3.7+**
- **Flask** (auto-installed từ requirements.txt)
- **Docker** (để compile LaTeX thành PDF)

## 📂 Cấu trúc Web App

```
web/
├── app.py              # Flask backend
├── templates/
│   └── index.html      # Main UI
├── requirements.txt    # Python dependencies
└── README.md          # Docs này
```

## 🎨 UI Features

- **Responsive Design**: Hoạt động tốt trên desktop và mobile
- **Real-time Status**: Hiển thị status của mỗi variant (có JD, TeX, PDF)
- **Action Buttons**: Compile, Download, Delete ngay trên UI
- **Error Handling**: Hiển thị lỗi rõ ràng khi có vấn đề

## 🔍 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI page |
| `/api/create-variant` | POST | Tạo variant mới |
| `/api/compile-cv` | POST | Compile LaTeX → PDF |
| `/api/download-pdf/<folder>` | GET | Download PDF |
| `/api/get-job-desc/<folder>` | GET | Lấy job description |
| `/api/delete-variant/<folder>` | DELETE | Xóa variant |

## 🐛 Troubleshooting

### Docker not running

```
Error: Cannot connect to Docker daemon
```

**Giải pháp**: Start Docker Desktop

```bash
open -a Docker
# Đợi 30s, sau đó compile lại
```

### Port 5000 đã được sử dụng

```
Error: Address already in use
```

**Giải pháp**: Đổi port trong `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001
```

### LaTeX compilation fails

**Giải pháp**:
1. Kiểm tra `main.tex` có syntax error không
2. Xem log trong terminal
3. Test compile manual:

```bash
cd v1/{company-role}
latexmk -pdf main.tex
```

## 🚀 Production Deployment

Để deploy lên production server:

```bash
# Sử dụng Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Hoặc với Docker:

```bash
# Tạo Dockerfile trong thư mục web/
# TODO: Add Dockerfile example
```

## 📝 Next Steps

- [ ] Tích hợp AI Agent API để auto-optimize CV
- [ ] Preview PDF trực tiếp trên web
- [ ] Edit job description sau khi tạo
- [ ] Compare variants side-by-side
- [ ] Export to other formats (Word, HTML)
- [ ] ATS score calculator

## 🤝 Contributing

Đóng góp được hoan nghênh! Đặc biệt:
- UI/UX improvements
- AI integration features
- Docker optimization
- Error handling enhancements
