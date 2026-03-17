# MGIS Outbound Declaration Generator v2.0

**Enterprise-grade document extraction for NeoAsia's Marine Insurance Outbound Declarations**

NeoAsia (S) Pte Ltd | Business Analytics Team

---

## What's New in v2.0

### Critical Fixes
- ✅ **Enhanced Vision Prompts**: Completely rewritten extraction prompts with specific field locations and real examples
- ✅ **Proper Value Extraction**: Invoice TOTAL VALUE is now correctly extracted (not weight from AWB)
- ✅ **Latest Model**: Upgraded to `claude-sonnet-4-5-20250514` for best OCR accuracy
- ✅ **Multi-Currency Support**: Handles USD, IDR, PHP, HKD, VND, MYR correctly
- ✅ **Better AWB-Invoice Matching**: Improved filename parsing and matching logic
- ✅ **Comprehensive Logging**: Debug logs show exactly what's being extracted

---

## Quick Start

### Streamlit Cloud Deployment

1. Push code to GitHub repository
2. Connect to Streamlit Cloud
3. Add secret in Streamlit Cloud settings:
   ```toml
   [api]
   ANTHROPIC_API_KEY = "sk-ant-api03-YOUR-KEY"
   ```
4. Deploy!

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="sk-ant-api03-YOUR-KEY"

# Run app
streamlit run app.py
```

---

## Usage

1. **Upload Documents**: 
   - AWB PDFs in the first uploader
   - Invoice PDFs in the second uploader
   
2. **Process**: Click "Process Outbound Documents"

3. **Review**: Check extracted data in the Review tab

4. **Export**: Download Excel declaration file

---

## File Naming Convention

For best AWB-Invoice matching, use consistent naming:

| Invoice File | AWB File | Match Key |
|--------------|----------|-----------|
| `ITR 2600246 - VN INV.pdf` | `ITR 2600246 - AWB.pdf` | ITR 2600246 |
| `SOM 2680033 - ID INV.pdf` | `SOM 2680033 - AWB.pdf` | SOM 2680033 |

---

## Expected Output

| Field | Source | Priority |
|-------|--------|----------|
| Invoice Number | Invoice filename / extracted | Invoice |
| Date | AWB "Executed on" field | AWB > Invoice |
| Flight/Vehicle | AWB "Requested Flight" field | AWB |
| Destination | Invoice "Ship To" section | Invoice |
| Currency | Invoice header | Invoice |
| Value | Invoice TOTAL VALUE | Invoice |

---

## Supported Currencies

| Currency | Country | Typical Range |
|----------|---------|---------------|
| USD | Vietnam (some), Hong Kong | Thousands |
| IDR | Indonesia | Millions/Billions |
| PHP | Philippines | Millions |
| HKD | Hong Kong | Hundreds of thousands |
| VND | Vietnam | Very large numbers |
| MYR | Malaysia | Thousands |

---

## Troubleshooting

### Missing Values
- Check that Invoice PDF has clear "TOTAL VALUE" or "TOTAL AMOUNT" section
- Verify PDF is not too blurry (Vision API needs readable text)

### Wrong Currency
- Currency is extracted from Invoice, not AWB
- Check Invoice header for Currency field

### No Flight Number
- Flight is extracted from AWB "Requested Flight/Date" field
- Format: 2 letters + 3-4 digits (e.g., SQ914, VN654)

### AWB-Invoice Not Matching
- Ensure both files have same ITR/SOM number in filename
- Check for typos or extra spaces

---

## Architecture

```
mgis_outbound_v2/
├── app.py                    # Streamlit UI
├── pipeline.py               # Processing orchestration
├── config/
│   ├── settings.py           # Configuration (model, timeouts)
│   └── prompts/
│       ├── outbound_awb.txt      # AWB extraction prompt
│       └── outbound_invoice.txt  # Invoice extraction prompt
├── extractors/
│   └── vision_extractor.py   # Claude Vision API integration
├── generators/
│   └── excel_generator.py    # Excel output generation
├── models/
│   └── shipment.py           # Data models
├── classifiers/
│   └── product_classifier.py # Product categorization
└── utils/
    └── helpers.py            # Utilities
```

---

## Technical Details

### Model Configuration
- **Model**: `claude-sonnet-4-5-20250514`
- **Max Tokens**: 4000
- **Rate Limit Delay**: 8 seconds between calls
- **Timeout**: 90 seconds

### PDF Processing
- **Zoom Factor**: 2.0x for clear text extraction
- **Format**: PNG images sent to Vision API

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.0 | Mar 2026 | Complete prompt rewrite, model upgrade, enhanced logging |
| v1.0 | Feb 2026 | Initial release |

---

*Built with ❤️ by NeoAsia Business Analytics Team*
