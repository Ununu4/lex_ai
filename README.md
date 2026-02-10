# 🕷️ LEX - Lender Eligibility X

**LEX** is an AI-powered lender advisory chatbot built for **Monet Capital** in the Merchant Cash Advance (MCA) industry. It helps brokers quickly understand lender guidelines and match merchants with the right funding sources using Google Gemini AI.

---

## ✨ Features

- **Multi-Lender Analysis**: Query multiple lenders simultaneously and compare requirements
- **PDF-Based Intelligence**: Analyzes actual lender guideline PDFs with citations
- **Conversation Memory**: Maintains context throughout chat sessions
- **Smart Caching**: Efficient PDF upload caching for faster responses
- **User Authentication**: Email-based login with admin dashboard
- **Admin Analytics**: Track usage patterns, errors, and user interactions
- **Modular Configuration**: Easy setup with environment variables

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key ([Get one free here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd lex_ai
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your API key
   # GEMINI_API_KEY=your_actual_api_key_here
   ```

5. **Add lender PDF files**
   ```bash
   # IMPORTANT: Add your lender guideline PDFs to the lender_pdf_database/ folder
   # The repository does not include PDF files - you must provide your own
   # See lender_pdf_database/README.md for detailed instructions
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

7. **Open your browser**
   - Navigate to: `http://localhost:8501`
   - Login with any email and password: `lex444`

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with these settings:

```env
# Required: Your Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Custom model (default: models/gemini-1.5-pro-latest)
GEMINI_MODEL_NAME=models/gemini-1.5-pro-latest

# Optional: Application password (default: lex444)
APP_PASSWORD=lex444

# Optional: Admin email domain (default: @admin.lex)
ADMIN_EMAIL_DOMAIN=@admin.lex

# Optional: PDF directory (default: lender_pdf_database)
LENDER_PDF_DIR=lender_pdf_database

# Optional: Logo path (default: logo.png)
LOGO_PATH=logo.png
```

### Alternative: Streamlit Secrets

You can also use Streamlit's secrets management:

1. Create `.streamlit/secrets.toml`:
   ```toml
   GEMINI_API_KEY = "your_api_key_here"
   APP_PASSWORD = "your_password_here"
   ```

---

## 📖 Usage

### Basic Query

1. **Select lenders** from the dropdown in the sidebar
2. **Type your question** in the chat input
3. LEX analyzes the PDFs and provides cited answers

### Query Syntax

**Option 1: Use dropdown selection**
```
Select lenders from sidebar → Click "Add to Query" → Type question
```

**Option 2: Inline syntax**
```
(mulligan, kapitus) What are the minimum credit score requirements?
(on deck, rapid finance) trucking industry requirements?
```

### Admin Access

- Login with email ending in `@admin.lex` (or your configured domain)
- Access "Admin Dashboard" from sidebar
- View all user interactions, filter by user or errors
- Monitor system usage

---

## 🗂️ Project Structure

```
lex_ai/
├── app.py                    # Main Streamlit application
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .env                      # Your config (DO NOT COMMIT)
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── logo.png                 # LEX branding
└── lender_pdf_database/     # Lender guideline PDFs (add your own)
    ├── README.md            # PDF setup instructions
    └── ... (place your PDFs here)
```

---

## 🔒 Security Best Practices

### ✅ DO:
- Keep your `.env` file local (it's in `.gitignore`)
- Use environment variables for all secrets
- Rotate API keys regularly
- Use `.env.example` as a template for team members

### ❌ DON'T:
- Commit `.env` files to Git
- Hardcode API keys in code
- Share API keys in chat/email
- Push secrets to public repositories

---

## 🐛 Troubleshooting

### "API Key Required" Error

**Problem**: No API key configured

**Solution**:
1. Check if `.env` file exists in project root
2. Verify `GEMINI_API_KEY` is set in `.env`
3. Restart the application
4. Or manually enter key in sidebar

### "PDF directory not found" Error

**Problem**: Can't find lender PDFs

**Solution**:
1. **Add PDF files** to `lender_pdf_database/` folder (see `lender_pdf_database/README.md`)
2. Check `LENDER_PDF_DIR` path in `.env`
3. Ensure `lender_pdf_database/` folder exists
4. Verify at least one PDF is in the directory
5. Use absolute path if needed

**Note**: This repository does not include PDF files. You must provide your own lender guideline PDFs.

### API Key Not Being Read

**Problem**: Changed API key but app still uses old one

**Solution**:
1. Stop the Streamlit application (Ctrl+C)
2. Restart: `streamlit run app.py`
3. Check configuration status in sidebar
4. Clear cache if needed: `streamlit cache clear`

### Rate Limit Errors

**Problem**: Gemini API quota exceeded

**Solution**:
1. Check your API quota at [Google AI Studio](https://aistudio.google.com/)
2. Wait for quota reset
3. Upgrade to paid tier if needed
4. Use different API key temporarily

---

## 🔄 Development

### Running in Development Mode

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run with auto-reload
streamlit run app.py

# Clear cache
streamlit cache clear
```

### Adding New Lenders

1. Add PDF to `lender_pdf_database/`
2. Name format: `lender_name.pdf` (lowercase, underscores)
3. Restart app - it will auto-index the new PDF

---

## 📦 Deployment

### Local Deployment

Already covered in [Quick Start](#-quick-start)

### Streamlit Cloud

1. Push to GitHub (secrets excluded via `.gitignore`)
2. Connect repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add secrets in Streamlit Cloud dashboard:
   - Go to App Settings → Secrets
   - Add your `GEMINI_API_KEY`
4. Deploy!

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV STREAMLIT_SERVER_PORT=8501
EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
docker build -t lex-ai .
docker run -p 8501:8501 --env-file .env lex-ai
```

---

## 🤝 Contributing

This is a private internal tool for Monet Capital. If you have access:

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

---

## 📄 License

Proprietary - Internal use only at Monet Capital.

---

## 👨‍💻 Credits

**Developed by Otto**  
**Powered by Octophy Solutions** 🦑

Built with:
- [Streamlit](https://streamlit.io/) - Web framework
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI engine
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment management

---

## 📞 Support

For issues or questions:
- Check the [Troubleshooting](#-troubleshooting) section
- Review configuration in `.env.example`
- Contact the development team

---

## 🗺️ Roadmap

- [ ] Export conversation history
- [ ] Bulk PDF comparison tool
- [ ] Custom system prompts per user
- [ ] Advanced filtering by lender criteria
- [ ] Integration with CRM systems
- [ ] Mobile-responsive design improvements

---

**Made with 🕷️ by LEX - Your Expert Lender Advisor**

