"""
Convert the FalconIQ AML CSV dataset to a professional PDF report.
Uses only Python standard library + a lightweight HTML-to-PDF approach via pdfkit or 
falls back to a pure-Python reportlab-free approach using csv + basic PDF generation.
"""
import csv
import os
import sys
from datetime import datetime

INPUT_CSV = os.path.expanduser("~/Desktop/FalconIQ_AML_Sample_Dataset_2100_Customers.csv")
OUTPUT_PDF = os.path.expanduser("~/Desktop/FalconIQ_AML_Sample_Dataset_2100_Customers.pdf")

# We'll generate an HTML file and then convert it
OUTPUT_HTML = os.path.expanduser("~/Desktop/FalconIQ_AML_Sample_Dataset_2100_Customers.html")


def read_csv():
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def risk_color(level):
    return {
        "LOW": "#10b981",
        "MEDIUM": "#f59e0b", 
        "HIGH": "#ef4444",
        "CRITICAL": "#dc2626",
    }.get(level, "#6b7280")


def kyc_color(status):
    return {
        "VERIFIED": "#10b981",
        "PENDING": "#f59e0b",
        "FAILED": "#ef4444",
        "EXPIRED": "#6b7280",
    }.get(status, "#6b7280")


def segment_color(seg):
    return {
        "RETAIL": "#6366f1",
        "PRIVATE": "#8b5cf6",
        "CORPORATE": "#0ea5e9",
        "SME": "#14b8a6",
        "WEALTH": "#d97706",
    }.get(seg, "#6b7280")


def generate_html(customers):
    # Compute stats
    from collections import Counter
    risk_counts = Counter(c["risk_category"] for c in customers)
    kyc_counts = Counter(c["kyc_status"] for c in customers)
    country_counts = Counter(c["country"] for c in customers)
    segment_counts = Counter(c["customer_segment"] for c in customers)
    
    total_income = sum(float(c["annual_income"]) for c in customers)
    avg_income = total_income / len(customers)

    rows_html = ""
    for idx, c in enumerate(customers, 1):
        rc = risk_color(c["risk_category"])
        kc = kyc_color(c["kyc_status"])
        sc = segment_color(c["customer_segment"])
        income_val = float(c["annual_income"])
        
        # Format income as INR if country is IND, else USD
        if c["country"] == "IND":
            income_str = f"₹ {income_val:,.0f}"
        else:
            income_str = f"$ {income_val:,.0f}"
        
        bg = "#ffffff" if idx % 2 == 0 else "#f8fafc"
        
        rows_html += f"""
        <tr style="background:{bg}">
            <td style="padding:6px 10px;font-size:11px;font-family:monospace;color:#6366f1;border-bottom:1px solid #e2e8f0">{c['customer_id']}</td>
            <td style="padding:6px 10px;font-size:11px;font-weight:600;border-bottom:1px solid #e2e8f0">{c['name']}</td>
            <td style="padding:6px 10px;font-size:10px;color:#6b7280;border-bottom:1px solid #e2e8f0">{c['email']}</td>
            <td style="padding:6px 10px;font-size:11px;border-bottom:1px solid #e2e8f0">{c['occupation']}</td>
            <td style="padding:6px 10px;font-size:11px;text-align:right;font-weight:600;border-bottom:1px solid #e2e8f0">{income_str}</td>
            <td style="padding:6px 10px;text-align:center;border-bottom:1px solid #e2e8f0"><span style="background:{rc}20;color:{rc};padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700">{c['risk_category']}</span></td>
            <td style="padding:6px 10px;text-align:center;border-bottom:1px solid #e2e8f0"><span style="background:{kc}20;color:{kc};padding:2px 8px;border-radius:10px;font-size:10px;font-weight:700">{c['kyc_status']}</span></td>
            <td style="padding:6px 10px;text-align:center;border-bottom:1px solid #e2e8f0"><span style="background:{sc}15;color:{sc};padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600">{c['customer_segment']}</span></td>
            <td style="padding:6px 10px;text-align:center;font-size:11px;font-weight:600;border-bottom:1px solid #e2e8f0">{c['country']}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FalconIQ AML Platform — Sample Dataset (2,100 Customers)</title>
    <style>
        @page {{
            size: A3 landscape;
            margin: 15mm;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px;
            color: #1e293b;
            background: #ffffff;
        }}
        .header {{
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 30px 40px;
            border-radius: 16px;
            margin-bottom: 24px;
        }}
        .header h1 {{ margin: 0; font-size: 28px; font-weight: 800; }}
        .header p {{ margin: 6px 0 0; opacity: 0.85; font-size: 14px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px 20px;
            text-align: center;
        }}
        .stat-card .value {{ font-size: 28px; font-weight: 800; color: #4f46e5; }}
        .stat-card .label {{ font-size: 11px; color: #64748b; margin-top: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            color: #1e293b;
            margin: 24px 0 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
        }}
        th {{
            background: #f1f5f9;
            padding: 8px 10px;
            text-align: left;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #475569;
            border-bottom: 2px solid #cbd5e1;
        }}
        .footer {{
            margin-top: 24px;
            padding: 16px;
            text-align: center;
            font-size: 11px;
            color: #94a3b8;
            border-top: 1px solid #e2e8f0;
        }}
        .risk-summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }}
        .risk-box {{
            padding: 12px;
            border-radius: 10px;
            text-align: center;
        }}
        .risk-box .count {{ font-size: 24px; font-weight: 800; }}
        .risk-box .rlabel {{ font-size: 10px; font-weight: 700; margin-top: 2px; text-transform: uppercase; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 FalconIQ AI AML Platform — Sample Customer Dataset</h1>
        <p>Comprehensive AML/CFT Compliance Dataset • {len(customers):,} Customer Records • Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}</p>
        <p style="margin-top:4px;font-size:12px;opacity:0.7">Schema: customer_id, name, email, occupation, annual_income, risk_category, kyc_status, customer_segment, country, created_at, updated_at</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="value">{len(customers):,}</div>
            <div class="label">Total Customers</div>
        </div>
        <div class="stat-card">
            <div class="value">{len(set(c['country'] for c in customers))}</div>
            <div class="label">Countries</div>
        </div>
        <div class="stat-card">
            <div class="value">₹ {avg_income/100000:.1f}L</div>
            <div class="label">Avg Income</div>
        </div>
        <div class="stat-card">
            <div class="value">{kyc_counts.get('VERIFIED', 0):,}</div>
            <div class="label">KYC Verified</div>
        </div>
        <div class="stat-card">
            <div class="value" style="color:#ef4444">{risk_counts.get('HIGH', 0) + risk_counts.get('CRITICAL', 0)}</div>
            <div class="label">High+Critical Risk</div>
        </div>
        <div class="stat-card">
            <div class="value">{segment_counts.get('CORPORATE', 0)}</div>
            <div class="label">Corporate Entities</div>
        </div>
    </div>

    <div class="risk-summary">
        <div class="risk-box" style="background:#ecfdf520;border:1px solid #10b98130">
            <div class="count" style="color:#10b981">{risk_counts.get('LOW', 0):,}</div>
            <div class="rlabel" style="color:#10b981">Low Risk</div>
        </div>
        <div class="risk-box" style="background:#fffbeb20;border:1px solid #f59e0b30">
            <div class="count" style="color:#f59e0b">{risk_counts.get('MEDIUM', 0):,}</div>
            <div class="rlabel" style="color:#f59e0b">Medium Risk</div>
        </div>
        <div class="risk-box" style="background:#fef2f220;border:1px solid #ef444430">
            <div class="count" style="color:#ef4444">{risk_counts.get('HIGH', 0)}</div>
            <div class="rlabel" style="color:#ef4444">High Risk</div>
        </div>
        <div class="risk-box" style="background:#fef2f220;border:1px solid #dc262630">
            <div class="count" style="color:#dc2626">{risk_counts.get('CRITICAL', 0)}</div>
            <div class="rlabel" style="color:#dc2626">Critical Risk</div>
        </div>
    </div>

    <div class="section-title">📋 Complete Customer Records ({len(customers):,} Entries)</div>
    
    <table>
        <thead>
            <tr>
                <th>Customer ID</th>
                <th>Name / Entity</th>
                <th>Email</th>
                <th>Occupation</th>
                <th style="text-align:right">Annual Income</th>
                <th style="text-align:center">Risk</th>
                <th style="text-align:center">KYC Status</th>
                <th style="text-align:center">Segment</th>
                <th style="text-align:center">Country</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="footer">
        <strong>FalconIQ AI AML Platform</strong> — Confidential Sample Dataset — Generated for Testing & Development Purposes Only<br>
        Compatible with: Customer Master Data, Transaction History, Alert Records, and Reference Data modules<br>
        Fields: customer_id · name · email · occupation · annual_income · risk_category · kyc_status · customer_segment · country · created_at · updated_at
    </div>
</body>
</html>"""
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML report generated: {OUTPUT_HTML}")
    return OUTPUT_HTML


def convert_to_pdf(html_path):
    """Try multiple PDF conversion methods."""
    # Method 1: Try weasyprint
    try:
        from weasyprint import HTML
        HTML(filename=html_path).write_pdf(OUTPUT_PDF)
        print(f"✅ PDF generated via WeasyPrint: {OUTPUT_PDF}")
        return True
    except ImportError:
        pass
    
    # Method 2: Try pdfkit (wkhtmltopdf)
    try:
        import pdfkit
        pdfkit.from_file(html_path, OUTPUT_PDF, options={
            'page-size': 'A3',
            'orientation': 'Landscape',
            'margin-top': '10mm',
            'margin-bottom': '10mm',
            'encoding': 'UTF-8',
        })
        print(f"✅ PDF generated via pdfkit: {OUTPUT_PDF}")
        return True
    except (ImportError, Exception):
        pass
    
    # Method 3: Use macOS built-in cupsfilter or textutil
    try:
        import subprocess
        result = subprocess.run([
            '/usr/sbin/cupsfilter', html_path
        ], capture_output=True, timeout=120)
        if result.returncode == 0:
            with open(OUTPUT_PDF, 'wb') as f:
                f.write(result.stdout)
            print(f"✅ PDF generated via cupsfilter: {OUTPUT_PDF}")
            return True
    except Exception:
        pass
    
    return False


if __name__ == "__main__":
    print("📊 FalconIQ AML — CSV to PDF Converter")
    print("=" * 45)
    
    customers = read_csv()
    print(f"📄 Read {len(customers)} records from CSV")
    
    html_path = generate_html(customers)
    
    success = convert_to_pdf(html_path)
    
    if not success:
        print(f"\n⚠️  PDF libraries not available. Your dataset is ready in two formats:")
        print(f"   📄 CSV: {INPUT_CSV}")
        print(f"   🌐 HTML: {OUTPUT_HTML}")
        print(f"\n💡 To open the HTML as PDF on macOS:")
        print(f"   1. Open the HTML file in Safari/Chrome")
        print(f"   2. Press ⌘+P → Save as PDF")
        print(f"\n   Or install weasyprint: pip3 install weasyprint")
