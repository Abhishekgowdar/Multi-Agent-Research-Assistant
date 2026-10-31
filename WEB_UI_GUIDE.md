# 🎨 Web UI Guide

## 🚀 Quick Start

### Step 1: Start the Web Server

```powershell
.\run_web.bat
```

Or manually:
```powershell
.\venv\Scripts\activate
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Open Your Browser

Navigate to: **http://localhost:8000**

---

## ✨ Features

### 🎯 **Beautiful Modern Interface**
- Gradient design with smooth animations
- Dark mode optimized
- Responsive (works on mobile!)
- Professional aesthetic

### ⚡ **Real-Time Progress**
- Watch AI agents work live
- See each step of the research process
- Progress indicators and status updates
- WebSocket-powered instant updates

### 📊 **Interactive Results**
- Statistics dashboard (papers found, analyzed, confidence)
- Full literature review display
- Must-read papers with links
- Smooth scrolling and animations

### 🎨 **User Experience**
- Simple, intuitive form
- Clear labels and instructions
- Visual feedback on all actions
- Error handling with user-friendly messages

---

## 🎯 How to Use

### 1. **Enter Your Research Query**
   - Type your research topic (e.g., "AI in healthcare")
   - Be as specific as you want

### 2. **Set Parameters**
   - Choose maximum papers (1-50)
   - Select data sources (arXiv, PubMed, Semantic Scholar)

### 3. **Start Research**
   - Click "🚀 Start Research"
   - Watch live progress updates
   - See AI agents working in real-time

### 4. **View Results**
   - Automatic scroll to results
   - Read comprehensive literature review
   - Browse must-read papers with direct links
   - Check confidence scores and statistics

---

## 📋 Example Queries

**Technology:**
- "machine learning in healthcare"
- "transformer neural networks"
- "quantum computing algorithms"

**Science:**
- "CRISPR gene editing applications"
- "climate change mitigation"
- "renewable energy storage"

**Healthcare:**
- "AI for cancer detection"
- "drug discovery machine learning"
- "precision medicine approaches"

---

## 🔧 API Endpoints

### REST API

**POST** `/api/research`
```json
{
  "query": "AI applications",
  "max_papers": 10,
  "sources": ["arxiv", "pubmed", "semantic_scholar"]
}
```

**GET** `/health`
- Health check endpoint

### WebSocket

**WS** `/ws`
- Real-time progress updates
- Bidirectional communication
- Live research status

---

## 🎨 Customization

### Change Colors

Edit `web/index.html` CSS variables:
```css
:root {
    --primary: #6366f1;     /* Main color */
    --secondary: #8b5cf6;   /* Accent color */
    --bg-dark: #0f172a;     /* Background */
    /* ... */
}
```

### Modify Layout

The UI is built with:
- **Pure HTML/CSS/JS** (no frameworks needed!)
- **Responsive Grid Layout**
- **CSS Animations**
- **WebSocket for real-time**

---

## 🌐 Deployment

### Local Network Access

Access from other devices on your network:
1. Find your IP: `ipconfig`
2. Open: `http://YOUR_IP:8000`

### Cloud Deployment

**Railway (FREE):**
```bash
# Install Railway CLI
npm install -g railway

# Login and deploy
railway login
railway init
railway up
```

**Render (FREE):**
1. Push to GitHub
2. Connect Render to repo
3. Deploy as Web Service

---

## 🐛 Troubleshooting

### "Connection Error"
- Make sure server is running (`run_web.bat`)
- Check firewall isn't blocking port 8000

### "WebSocket Failed"
- Refresh the page
- Restart the server
- Clear browser cache

### "No Papers Found"
- Try broader search terms
- Select different data sources
- Check internet connection

---

## 📱 Mobile Experience

The UI is fully responsive!
- Works on phones and tablets
- Touch-optimized
- Readable on small screens

---

## 🎉 Features Showcase

### ✅ What Makes This UI Special

1. **Real-Time Updates**
   - See agents working live
   - No page refresh needed
   - Instant feedback

2. **Beautiful Design**
   - Modern gradient aesthetics
   - Smooth animations
   - Professional appearance

3. **User-Friendly**
   - Clear instructions
   - Intuitive layout
   - Helpful error messages

4. **Fast & Responsive**
   - WebSocket for speed
   - Optimized performance
   - Smooth animations

5. **Comprehensive Results**
   - Full literature reviews
   - Paper recommendations
   - Statistics dashboard

---

## 💡 Pro Tips

1. **Use Specific Queries**
   - ✅ "machine learning for drug discovery"
   - ❌ "AI"

2. **Start Small**
   - Try 5-10 papers first
   - Then increase for comprehensive reviews

3. **Select Relevant Sources**
   - PubMed for medical topics
   - arXiv for physics/CS/math
   - Semantic Scholar for broad coverage

4. **Save Your Results**
   - Copy-paste the review
   - Or use browser's "Save As" feature

---

## 🚀 Next Steps

Want to enhance the UI further?

1. **Add Export Button** (PDF/Markdown download)
2. **History Feature** (save past searches)
3. **User Accounts** (personalized experience)
4. **Advanced Filters** (date range, authors)
5. **Citation Manager** (export citations)

---

**Enjoy your beautiful AI Research Assistant!** 🎉
