#!/usr/bin/env python3
"""
Debug script to test extraction on actual documents.
Run this locally or in Claude to verify extraction is working.
"""

import fitz
import base64
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from anthropic import Anthropic


def pdf_to_base64(pdf_path: str, page_num: int = 0, zoom: float = 2.0) -> str:
    """Convert PDF page to base64 PNG"""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    doc.close()
    return base64.standard_b64encode(img_bytes).decode('utf-8')


def load_prompt(prompt_name: str) -> str:
    """Load prompt from file"""
    prompt_path = f"config/prompts/{prompt_name}.txt"
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r') as f:
            return f.read()
    else:
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")


def extract_from_pdf(client: Anthropic, pdf_path: str, prompt_type: str) -> dict:
    """Extract data from a PDF using Claude Vision"""
    print(f"\n{'='*70}")
    print(f"Processing: {os.path.basename(pdf_path)}")
    print(f"Prompt type: {prompt_type}")
    print(f"{'='*70}")
    
    # Convert to base64
    base64_img = pdf_to_base64(pdf_path)
    
    # Load prompt
    prompt = load_prompt(prompt_type)
    
    # Call API
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_img
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    
    raw_response = response.content[0].text
    print(f"\nRaw Response:\n{raw_response}")
    
    # Parse JSON
    import re
    json_match = re.search(r'\{[\s\S]*\}', raw_response)
    if json_match:
        try:
            data = json.loads(json_match.group())
            print(f"\nParsed Data:")
            print(json.dumps(data, indent=2))
            return data
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {}
    else:
        print("No JSON found in response")
        return {}


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Debug extraction')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('--type', choices=['outbound_awb', 'outbound_invoice'], 
                       required=True, help='Document type')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: No API key provided. Set ANTHROPIC_API_KEY or use --api-key")
        sys.exit(1)
    
    client = Anthropic(api_key=api_key)
    
    result = extract_from_pdf(client, args.pdf_path, args.type)
    
    # Summary
    print(f"\n{'='*70}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*70}")
    
    if args.type == 'outbound_invoice':
        print(f"Invoice Number: {result.get('invoice_number')}")
        print(f"Date: {result.get('date')}")
        print(f"Currency: {result.get('currency')}")
        print(f"Total Value: {result.get('total_value')}")
        print(f"Destination: {result.get('destination_city')}, {result.get('destination_country')}")
        print(f"Confidence: {result.get('confidence')}")
    else:
        print(f"AWB Number: {result.get('awb_number')}")
        print(f"Flight Number: {result.get('flight_number')}")
        print(f"Flight Date: {result.get('flight_date')}")
        print(f"Destination: {result.get('destination_city')}, {result.get('destination_country')}")
        print(f"Invoice Reference: {result.get('invoice_reference')}")
        print(f"Confidence: {result.get('confidence')}")


if __name__ == "__main__":
    main()
