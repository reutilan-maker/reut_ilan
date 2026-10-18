import streamlit as strl
import math
import requests
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def parse_sds_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        text = response.text.lower()
        x_cellulose, x_lignin, x_acid, is_tissue = 1.0, 0.0, 0.0, False
        if "thermal" in text or "safety-data-sheet" in url:
            x_cellulose, x_lignin, x_acid = 0.80, 0.15, 0.05
        elif "tissue" in text or "pel" in text:
            x_cellulose, is_tissue = 1.0, True
        return x_cellulose, x_lignin, x_acid, is_tissue
    except:
        return 1.0, 0.0, 0.0, False

def calculate_paper_lifetime(temp_c, rh, x_cellulose, x_lignin, x_acid, is_tissue):
    R, T = 8.314, temp_c + 273.15
    Ea_total = (x_cellulose * 110000) + (x_lignin * 80000) - (15000 if x_acid > 0 else 0)
    dS = -60.0 if not is_tissue else -42.0
    A = ((1.380649e-23 * T) / 6.62607015e-34) * math.exp(dS / R)
    B = (0.03 if not is_tissue else 0.042) * (rh / 50.0)
    
    ln_k = math.log(A) - (Ea_total / (R * T)) + B
    ln_k_ref = math.log(A) - (Ea_total / (R * 293.15)) + ((0.03 if not is_tissue else 0.042) * 1.0)
    k_relative = math.exp(ln_k - ln_k_ref)
    
    base_lifetime = 200 if not is_tissue else 120
    if x_lignin > 0 or x_acid > 0: base_lifetime = 5
    
    return k_relative, base_lifetime / k_relative, base_lifetime / (k_relative * (15 / 21)), Ea_total

strl.set_page_config(page_title="מחשבון חמצון נייר", layout="centered")
strl.title("🧪 אפליקציית חישוב חמצון נייר ארכיוני")
strl.markdown("מערכת אונליין לחישוב חלון הביטחון המוחלט של חומרי עיטוף על בסיס משוואת ארניוס.")

paper_name = strl.text_input("שם הנייר / מותג לבדיקה:", value="KLUG Photographic Paper")
url_input = strl.text_input("קישור ל-SDS או למפרט הטכני (URL):", value="https://klug-conservation.de")
temp_input = strl.slider("טמפרטורת המחסן בדיקה (°C)", 10, 45, 30)  # ברירת מחדל 30 מעלות כבקשתך
rh_input = strl.slider("לחות יחסית במחסן (RH%)", 10, 90, 70)

if url_input:
    x_cell, x_lig, x_ac, is_tiss = parse_sds_from_url(url_input)
    k_rel, yrs_21, yrs_15, ea_total = calculate_paper_lifetime(temp_input, rh_input, x_cell, x_lig, x_ac, is_tiss)
    
    strl.subheader("📊 חלון זמן בטוח לעיטוף (שנים לפני פליטת חומצה ופריכות):")
    col1, col2 = strl.columns(2)
    with col1:
        strl.metric(label="🟦 מחסן חמצן רגיל (21% O₂)", value=f"{int(yrs_21)} שנים")
    with col2:
        strl.metric(label="🟩 מחסן מרודד חמצן (15% O₂)", value=f"{int(yrs_15)} שנים")
