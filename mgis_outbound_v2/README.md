# MGIS Outbound Declaration Generator

**Marine Insurance Declaration Generator - Outbound Shipments Only**

NeoAsia (S) Pte Ltd | Business Analytics Team

## Quick Start

1. Upload Outbound AWB and Invoice PDFs
2. Click "Process Outbound Documents"
3. Review and edit extracted data
4. Download Excel declaration

## Document Types Supported

| Document Type | What's Extracted |
|--------------|------------------|
| Air Waybills (AWB) | Flight numbers, dates, AWB numbers |
| Commercial Invoices | Destinations, values, currencies |

## Deployment

Deployed on Streamlit Community Cloud.

**Secrets Configuration:**
```toml
[api]
ANTHROPIC_API_KEY = "sk-ant-..."
```

---

*v2.0 - Outbound Only Edition*
