# Lender PDF Database

This directory should contain your lender guideline PDF files.

## 📁 Setup Instructions

**IMPORTANT:** This repository does not include PDF files. You must add your own lender guideline PDFs to this directory before running the application.

### How to Add PDFs:

1. **Obtain lender guideline PDFs** from your lender partners or internal sources
2. **Place PDF files** in this directory (`lender_pdf_database/`)
3. **Naming convention** (recommended):
   - Use lowercase with underscores
   - Example: `mulligan.pdf`, `kapitus.pdf`, `on_deck.pdf`
   - Avoid spaces in filenames

### Example Structure:

```
lender_pdf_database/
├── README.md (this file)
├── mulligan.pdf
├── kapitus.pdf
├── on_deck.pdf
├── rapid_finance.pdf
└── ... (add your PDFs here)
```

### Notes:

- **Minimum**: At least 1 PDF file is required for the app to function
- **File format**: Only PDF files are supported
- **File size**: Keep PDFs under 10MB each for optimal performance
- **Privacy**: PDF files are excluded from Git (see `.gitignore`)
- **Security**: Never commit proprietary/confidential lender documents to public repositories

### Verification:

After adding PDFs, run the application and check the sidebar to see the list of available lenders.

---

**Need help?** See the main [README.md](../README.md) for complete setup instructions.
