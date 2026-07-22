from fpdf import FPDF
import pandas as pd
import io

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'InfraPulse Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_region_pdf(df: pd.DataFrame, filters_text: str = "") -> bytes:
    pdf = PDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Filtered View Summary", 0, 1)
    
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 10, f"Filters applied: {filters_text}")
    pdf.cell(0, 10, f"Total bridges shown: {len(df)}", 0, 1)
    if not df.empty:
        pdf.cell(0, 10, f"Average Risk Score: {df['risk_score'].mean():.1f}", 0, 1)
    pdf.ln(5)
    
    if df.empty:
        pdf.cell(0, 10, "No data available for these filters.", 0, 1)
        return bytes(pdf.output())
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Top 20 Highest-Risk Bridges:", 0, 1)
    
    pdf.set_font("Arial", 'B', 9)
    col_width = pdf.epw / 6
    headers = ['ID', 'Region', 'Class', 'Tier', 'Score', 'Priority']
    
    for header in headers:
        pdf.cell(col_width, 10, header, border=1, align='C')
    pdf.ln()
    
    pdf.set_font("Arial", '', 8)
    top_20 = df.sort_values('risk_score', ascending=False).head(20)
    
    for _, row in top_20.iterrows():
        name = str(row.get('Name', ''))[:20]
        region = str(row.get('REGION_PHYS', ''))[:15]
        s_class = str(row.get('CD_STATE_CLASS', ''))[:10]
        tier = str(row.get('risk_tier', ''))
        score = f"{row.get('risk_score', 0):.1f}"
        priority = str(row.get('inspection_priority', ''))[:15]
        
        pdf.cell(col_width, 10, name, border=1)
        pdf.cell(col_width, 10, region, border=1)
        pdf.cell(col_width, 10, s_class, border=1, align='C')
        pdf.cell(col_width, 10, tier, border=1, align='C')
        pdf.cell(col_width, 10, score, border=1, align='C')
        pdf.cell(col_width, 10, priority, border=1)
        pdf.ln()

    return bytes(pdf.output())

def generate_bridge_pdf(bridge_row: pd.Series) -> bytes:
    pdf = PDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Bridge Profile: {bridge_row.get('Name', 'Unknown')}", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 11)
    
    def add_field(label, value):
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(50, 10, f"{label}:", 0, 0)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 10, str(value), 0, 1)
        
    add_field("Region", bridge_row.get('REGION_PHYS', 'N/A'))
    add_field("Road Class", bridge_row.get('CD_STATE_CLASS', 'N/A'))
    add_field("Risk Score", f"{bridge_row.get('risk_score', 0):.1f}")
    add_field("Risk Tier", bridge_row.get('risk_tier', 'N/A'))
    add_field("Inspection Priority", bridge_row.get('inspection_priority', 'N/A'))
    
    flood = "Yes" if bridge_row.get('flood_affected_2022') else "No"
    add_field("Oct 2022 Flood Affected", flood)
    
    return bytes(pdf.output())
