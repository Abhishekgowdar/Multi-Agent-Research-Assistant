# 📚 Data Sources Guide

Your AI Research Assistant now supports **9 data sources** for comprehensive paper search!

---

## 🎯 **Available Data Sources**

### ✅ **FREE - No API Key Needed**

1. **🎓 Google Scholar** - MOST POPULAR in India
   - Coverage: ALL academic fields
   - Papers: Millions
   - Setup: ✅ Works immediately, no key needed

2. **📄 arXiv**
   - Coverage: Physics, Math, Computer Science
   - Papers: 2M+ preprints
   - Setup: ✅ Works immediately, no key needed

3. **🏥 PubMed**
   - Coverage: Medical & Life Sciences
   - Papers: 35M+ citations
   - Setup: ✅ Works immediately, no key needed

4. **🔍 Semantic Scholar**
   - Coverage: All fields (AI-powered search)
   - Papers: 200M+
   - Setup: ✅ Works immediately, no key needed

5. **📖 CORE**
   - Coverage: Open access papers (all fields)
   - Papers: 200M+ open access articles
   - Setup: ✅ Works immediately, no key needed

6. **📚 CrossRef**
   - Coverage: Metadata for 130M+ research works
   - Papers: 130M+ DOIs
   - Setup: ✅ Works immediately, no key needed

7. **🧬 bioRxiv**
   - Coverage: Biology & Medical preprints
   - Papers: Latest research preprints
   - Setup: ✅ Works immediately, no key needed

8. **🔬 PLOS ONE**
   - Coverage: Open access journals
   - Papers: High-quality peer-reviewed
   - Setup: ✅ Works immediately, no key needed

---

### 🔑 **FREE - Requires API Key**

9. **🔧 IEEE Xplore** - Very Popular for Indian Engineering Students!
   - Coverage: Engineering, Computer Science, Electronics
   - Papers: 5M+ technical papers
   - Setup: Requires FREE API key (5 minutes to get)

---

## 🚀 **Quick Start**

### **Option 1: Use Without IEEE (8 sources)**
Just run the system! Google Scholar, arXiv, PubMed, and 5 other sources work immediately.

```powershell
.\run_web.bat
```

### **Option 2: Add IEEE for Full Access (9 sources)**
Follow the IEEE setup below to get access to engineering/CS papers.

---

## 🔧 **IEEE Xplore Setup (5 Minutes)**

IEEE is **crucial** for Indian engineering students! Here's how to get your FREE API key:

### **Step 1: Create IEEE Account**
1. Go to: **https://developer.ieee.org/member/register**
2. Click **"Register"**
3. Fill in your details:
   - Email (use your college email if available)
   - Name
   - Password
4. Verify your email

### **Step 2: Get Your API Key**
1. Login to: **https://developer.ieee.org/**
2. Click **"My Profile"** or **"API Keys"**
3. Click **"Request API Key"**
4. Fill the form:
   - Application Name: "AI Research Assistant"
   - Purpose: "Academic Research"
5. Copy your API key (looks like: `abc123xyz456`)

### **Step 3: Add to Your Project**
1. Open `.env` file
2. Find the line: `IEEE_API_KEY=your_ieee_key_here`
3. Replace with your actual key:
   ```
   IEEE_API_KEY=abc123xyz456
   ```
4. Save the file

### **Step 4: Test It!**
```powershell
.\run_web.bat
```

Check "IEEE Xplore" in the UI and search for engineering/CS topics!

---

## 📊 **Data Source Comparison**

| Source | Best For | Speed | Coverage |
|--------|----------|-------|----------|
| 🎓 Google Scholar | Everything (Most Popular) | Medium | ⭐⭐⭐⭐⭐ |
| 🔧 IEEE Xplore | Engineering, CS, Electronics | Fast | ⭐⭐⭐⭐ |
| 📄 arXiv | Physics, Math, CS Preprints | Fast | ⭐⭐⭐⭐ |
| 🏥 PubMed | Medicine, Biology | Fast | ⭐⭐⭐⭐⭐ |
| 🔍 Semantic Scholar | AI-powered search | Fast | ⭐⭐⭐⭐⭐ |
| 📖 CORE | Open Access | Medium | ⭐⭐⭐⭐ |
| 📚 CrossRef | Metadata | Fast | ⭐⭐⭐⭐⭐ |
| 🧬 bioRxiv | Biology Preprints | Fast | ⭐⭐⭐ |
| 🔬 PLOS ONE | Quality Journals | Fast | ⭐⭐⭐ |

---

## 💡 **Recommended Combinations**

### For **Computer Science** Students:
✅ Google Scholar + IEEE Xplore + arXiv + Semantic Scholar

### For **Medical** Students:
✅ Google Scholar + PubMed + bioRxiv + PLOS ONE

### For **Engineering** Students:
✅ Google Scholar + IEEE Xplore + CrossRef + CORE

### For **General Research**:
✅ Google Scholar + Semantic Scholar + CrossRef + CORE

### For **Maximum Coverage** (Recommended!):
✅ Select ALL 9 sources!

---

## 🎓 **Why These Sources are Great for Indian Students**

1. **Google Scholar** - Most widely used in India, covers Indian journals
2. **IEEE Xplore** - Essential for IIT/NIT students, covers Indian conferences
3. **Open Access** - CORE, PLOS, bioRxiv are completely free
4. **No Paywall** - All sources provide at least abstracts for free
5. **Global + Local** - Mix of international and Indian publications

---

## ⚡ **Tips for Better Results**

1. **Use Multiple Sources**: Select 3-5 sources for best coverage
2. **Start with Google Scholar**: It's the most comprehensive
3. **Add IEEE for Tech**: If you're in CS/Engineering, IEEE is a must
4. **More Papers = Better**: Increase "Maximum Papers" for thorough research
5. **Specific Keywords**: Use precise terms for better results

---

## 🐛 **Troubleshooting**

### **Google Scholar Not Working**
- Wait a minute and try again (rate limiting)
- Google Scholar has anti-bot measures, it might be temporarily blocked

### **IEEE Shows No Results**
- Check your API key is correct in `.env`
- Make sure your query is related to engineering/CS
- Verify your IEEE account is active

### **Slow Searches**
- Reduce "Maximum Papers" number
- Select fewer data sources
- Some sources (bioRxiv) are slower than others

---

## 📝 **Installation**

If you haven't installed the new dependencies yet:

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Install new packages
pip install beautifulsoup4 lxml

# Or reinstall all
pip install -r requirements.txt
```

---

## 🎉 **You're Ready!**

Start your research with **9 powerful data sources**:

```powershell
.\run_web.bat
```

Open: **http://localhost:8000**

**Happy Researching!** 🚀📚
