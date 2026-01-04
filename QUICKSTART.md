# ⚡ Quick Start Guide

Get the AI Study Assistant running in 5 minutes!

## 1. Setup (2 minutes)

```bash
# Navigate to project directory
cd ai-study-assistant

# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure API Key (1 minute)

Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-key-here
```

Get a key at: https://platform.openai.com/api-keys

## 3. Run the App (1 minute)

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

## 4. Upload & Ask (1 minute)

1. Click "Choose a PDF file" → select your course PDF
2. Click "Process PDF" → wait for processing
3. Type a question → click "Get Answer"
4. See sources → expand "Source Material"

## ✨ That's it!

You now have a fully functional AI Study Assistant!

---

## 🔧 Troubleshooting Quick Fixes

**"ModuleNotFoundError"**
```bash
# Make sure virtual env is activated
# Then reinstall: pip install -r requirements.txt
```

**"OPENAI_API_KEY not set"**
- Check `.env` file exists
- Verify API key is correct
- Restart the app

**"App running slowly"**
- Wait for PDF processing (first time only)
- Large PDFs take 1-3 minutes

---

## 📚 Next Steps

- Read [README.md](README.md) for detailed docs
- Adjust `pdf_processor.py` for chunk size
- Try different prompts in `prompts/tutor_prompt.txt`
- Experiment with different PDFs

---

## 🎯 For the Interview

This project demonstrates:
✅ LLM integration (OpenAI API)  
✅ RAG implementation  
✅ Prompt engineering  
✅ PDF processing  
✅ Vector embeddings  
✅ Full-stack AI development  
✅ User-friendly UI design  

Perfect for: **Trainee AI Engineer** position!
