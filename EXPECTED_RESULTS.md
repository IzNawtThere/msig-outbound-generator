# MGIS Outbound Extraction - Expected Results

## Test Data: Regina's Feb-26 Declaration Documents

### Source Files (12 total)

| Invoice File | AWB File | Match Key |
|--------------|----------|-----------|
| ITR 2600246 - VN INV.pdf | ITR 2600246 - AWB.pdf | ITR 2600246 |
| ITR 2600272 - ID INV.pdf | ITR 2600272 - AWB.pdf | ITR 2600272 |
| ITR 2600285 - PH INV.pdf | ITR 2600285 - AWB.PDF | ITR 2600285 |
| ITR 2600395 - HK INV.pdf | ITR 2600395 - AWB.PDF | ITR 2600395 |
| SOM 2680033 - ID INV.pdf | SOM 2680033 - AWB.pdf | SOM 2680033 |
| SOM 2680036 - VN INV.pdf | SOM 2680036 - AWB.pdf | SOM 2680036 |

### Expected Extraction Results

#### 1. ITR 2600246 (Vietnam - USD)
- **Invoice Number**: ITR 2600246
- **Date**: 2026-02-06 (AWB Executed date takes priority)
- **Currency**: USD
- **Total Value**: 51,485.87
- **Destination**: Ho Chi Minh City, Vietnam
- **Description**: Skincare Products
- **Flight**: SQ178

#### 2. ITR 2600272 (Indonesia - IDR)
- **Invoice Number**: ITR 2600272
- **Date**: 2026-02-04
- **Currency**: IDR
- **Total Value**: 4,153,540,000.00
- **Destination**: Jakarta, Indonesia
- **Description**: Medical Devices (Profhilo)

#### 3. ITR 2600285 (Philippines - PHP)
- **Invoice Number**: ITR 2600285
- **Date**: 2026-02-04
- **Currency**: PHP
- **Total Value**: 44,954,968.32 (CIF Grand Total)
- **Destination**: Philippines
- **Description**: Medical Devices and Oral Supplements
- **Flight**: SQ914

#### 4. ITR 2600395 (Hong Kong - HKD)
- **Invoice Number**: ITR 2600395
- **Date**: 2026-02-24
- **Currency**: HKD
- **Total Value**: 401,371.80
- **Destination**: Hong Kong
- **Description**: Skincare Products
- **Flight**: SQ894

#### 5. SOM 2680033 (Indonesia - IDR)
- **Invoice Number**: SOM 2680033
- **Date**: 2026-02-23 (AWB Executed date)
- **Currency**: IDR
- **Total Value**: 246,180,000.00
- **Destination**: Jakarta, Indonesia
- **Description**: Skincare Products
- **Flight**: SQ968

#### 6. SOM 2680036 (Vietnam - USD)
- **Invoice Number**: SOM 2680036
- **Date**: 2026-03-02 (AWB Executed date)
- **Currency**: USD
- **Total Value**: 38,156.08
- **Destination**: Ho Chi Minh City, Vietnam
- **Description**: Oral Supplements and Skincare Products
- **Flight**: VN654

---

## Verification Checklist

When testing the extraction, verify:

1. ✅ All 6 shipments extracted (not just 1)
2. ✅ Values match expected totals (NOT weights from AWB!)
3. ✅ Currencies correct for each country
4. ✅ Flight numbers extracted from AWBs
5. ✅ Dates from AWB "Executed on" field (not invoice date)
6. ✅ Destinations include country name

## Common Issues to Watch For

| Issue | Symptom | Fix |
|-------|---------|-----|
| AWB-Invoice mismatch | Missing shipments | Check filename parsing |
| Weight as Value | Small USD values like 643 | Use Invoice for value, not AWB |
| Missing flight | Empty flight column | Check AWB prompt for flight extraction |
| Wrong date | Invoice date instead of shipment | Use AWB "Executed on" date |
