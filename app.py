import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import time
import os
import gc
from fpdf import FPDF

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TechnoBolt Gym Hub", layout="wide", page_icon="🏋️")

# --- DESIGN SYSTEM TECHNOBOLT (ULTRA-BLINDAGEM BLACK & GRAY) ---
st.markdown("""
<style>
    /* 1. FUNDO PRETO TOTAL E FONTES BRANCAS */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #000000 !important;
    }
    
    html, body, [class*="st-"] { color: #ffffff !important; }
    h1, h2, h3, p, span, label, li { color: #ffffff !important; }

    /* 2. CORREÇÃO DE CAMPOS QUE FICAVAM BRANCOS (SELECT E UPLOAD) */
    /* Selectbox (Objetivo) */
    div[data-baseweb="select"] > div {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #333 !important;
    }
    
    /* Itens dentro da lista do Selectbox */
    div[role="listbox"] ul { background-color: #1a1a1a !important; }
    div[role="option"] { background-color: #1a1a1a !important; color: white !important; }
    div[role="option"]:hover { background-color: #3b82f6 !important; }

    /* File Uploader (Foto Bio Análise) */
    [data-testid="stFileUploader"] {
        background-color: #1a1a1a !important;
        border: 1px dashed #444 !important;
        padding: 10px !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploader"] section { background-color: #1a1a1a !important; }
    [data-testid="stFileUploader"] label { color: white !important; }

    /* 3. BOTÕES CINZA ESCURO (ANTI-DEFORMAÇÃO) */
    button, .stButton>button, .stDownloadButton>button {
        background-color: #333333 !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
        border-radius: 10px !important;
        min-height: 50px !important;
        width: 100% !important;
        display: block !important;
        font-weight: bold !important;
        text-transform: uppercase;
        margin-top: 10px !important;
        margin-bottom: 10px !important;
        transition: 0.3s;
    }
    button:hover { background-color: #444444 !important; border-color: #3b82f6 !important; }

    /* 4. INPUTS DE TEXTO */
    input {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #333 !important;
    }

    /* 5. CARDS DE RESULTADO */
    .result-card-unificado { 
        background-color: #111111 !important; 
        color: #ffffff !important; 
        padding: 25px; 
        border-radius: 15px; 
        border-top: 6px solid #3b82f6; 
        margin-top: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,1);
    }

    /* 6. ABAS */
    .stTabs [data-baseweb="tab-list"] { background-color: #000 !important; }
    .stTabs [data-baseweb="tab"] { color: #888 !important; }
    .stTabs [aria-selected="true"] { background-color: #333 !important; color: white !important; border-radius: 5px !important; }
</style>
""", unsafe_allow_html=True)

# --- USUÁRIOS ---
USUARIOS_DB = {
    "admin": "admin123", "pedro.santana": "senha", "luiza.trovao": "senha",
    "anderson.bezerra": "senha", "fabricio.felix": "senha", "jackson.antonio": "senha",
    "italo.trovao": "senha", "julia.fernanda": "senha", "convidado": "senha"
}

if "logado" not in st.session_state: st.session_state.logado = False
if "user_atual" not in st.session_state: st.session_state.user_atual = ""

# --- LOGIN ---
if not st.session_state.logado:
    st.markdown('<div class="main-card"><h1>TechnoBolt Gym</h1><p>Consultoria de Elite</p></div>', unsafe_allow_html=True)
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("AUTENTICAR"):
        if u in USUARIOS_DB and USUARIOS_DB[u] == p:
            st.session_state.logado = True
            st.session_state.user_atual = u
            st.rerun()
        else: st.error("Credenciais inválidas.")
    st.stop()

# --- PDF ---
def gerar_pdf(nome, idade, altura, peso, imc, objetivo, conteudo, titulo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"TECHNOBOLT GYM - {titulo}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f" ATLETA: {nome.upper()}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Idade: {idade}a | Peso: {peso}kg | IMC: {imc:.2f} | Objetivo: {objetivo}", ln=True, border='B')
    pdf.ln(5)
    clean_text = conteudo.replace('#', '').replace('*', '').replace('>', '').replace('-', '•')
    pdf.multi_cell(0, 7, clean_text.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S')

# --- SIDEBAR ---
with st.sidebar:
    st.header(f"Olá, {st.session_state.user_atual.split('.')[0].capitalize()}")
    if st.button("SAIR/LOGOUT"):
        st.session_state.logado = False
        st.rerun()
    st.divider()
    nome_perfil = st.text_input("Nome Completo", value=st.session_state.user_atual.replace('.', ' ').capitalize())
    idade = st.number_input("Idade", 12, 90, 25)
    altura = st.number_input("Altura (cm)", 100, 250, 170)
    peso = st.number_input("Peso (kg)", 30.0, 250.0, 75.0)
    objetivo = st.selectbox("Objetivo Principal", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    up = st.file_uploader("📸 Foto Bio Análise", type=['jpg', 'png', 'jpeg'])

# --- PROCESSAMENTO ---
if up and nome_perfil:
    try:
        bytes_data = up.getvalue()
        img_raw = ImageOps.exif_transpose(Image.open(io.BytesIO(bytes_data))).convert("RGB")
        img_raw.thumbnail((600, 600), Image.Resampling.LANCZOS)
        gc.collect()
        
        imc = peso / ((altura/100)**2)
        api_key = os.environ.get("GEMINI_API_KEY") or (st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else None)
        if not api_key: st.stop()
        genai.configure(api_key=api_key)

        MOTORES = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-2.0-flash-lite", "models/gemini-flash-latest"]

        def processar(prompt):
            for m in MOTORES:
                try:
                    model = genai.GenerativeModel(m)
                    response = model.generate_content([prompt, img_raw])
                    return response.text, m
                except: continue
            return "Erro nos motores.", "OFFLINE"

        with st.empty():
            gif_url = "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJqZ3R3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3JlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKMGpxx303Z3o9G/giphy.gif"
            st.markdown(f"""
                <div style="text-align:center; padding:30px; background:rgba(0,0,0,0.9); border-radius:20px; border:2px solid #3b82f6; box-shadow: 0 0 20px #3b82f6;">
                    <img src="{gif_url}" width="200" style="filter: hue-rotate(180deg); margin-bottom:15px; border-radius:50%;">
                    <h2 style="color:#3b82f6; letter-spacing: 2px; animation: blink 1.5s infinite;">ESCANEANDO BIOMETRIA...</h2>
                    <audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-20.mp3" type="audio/mpeg"></audio>
                </div>
                <style>@keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} 100% {{ opacity: 1; }} }}</style>
            """, unsafe_allow_html=True)

            r1, e1 = processar(f"RETORNE APENAS CONTEÚDO TÉCNICO. PhD em Antropometria. Analise {nome_perfil}, {idade}a, IMC {imc:.2f}. Biotipo, BF%, Postura. Use parênteses para intuitivo.")
            r2, e2 = processar(f"RETORNE APENAS CONTEÚDO TÉCNICO. Nutricionista PhD. Objetivo {objetivo}. GET, Macros e Dieta. Use parênteses.")
            r3, e3 = processar(f"RETORNE APENAS CONTEÚDO TÉCNICO. Suplementação Esportiva. 3 suplementos p/ {objetivo}. Use parênteses.")
            r4, e4 = processar(f"RETORNE APENAS CONTEÚDO TÉCNICO. Personal Trainer PhD. Treino 7 dias p/ {objetivo}. Justificativa e Substitutos. Use parênteses.")
            
            time.sleep(1)
            st.empty()

        tabs = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino", "📜 Completo"])

        with tabs[0]:
            st.markdown(f'<div class="result-card-unificado"><small>{e1}</small><br>{r1}</div>', unsafe_allow_html=True)
            st.download_button("PDF Avaliação", data=bytes(gerar_pdf(nome_perfil, idade, altura, peso, imc, objetivo, r1, "AVALIAÇÃO")), file_name="Avaliacao.pdf")
        with tabs[1]:
            st.markdown(f'<div class="result-card-unificado"><small>{e2}</small><br>{r2}</div>', unsafe_allow_html=True)
            st.download_button("PDF Nutrição", data=bytes(gerar_pdf(nome_perfil, idade, altura, peso, imc, objetivo, r2, "NUTRIÇÃO")), file_name="Nutricao.pdf")
        with tabs[2]:
            st.markdown(f'<div class="result-card-unificado"><small>{e3}</small><br>{r3}</div>', unsafe_allow_html=True)
            st.download_button("PDF Suplementos", data=bytes(gerar_pdf(nome_perfil, idade, altura, peso, imc, objetivo, r3, "SUPLEMENTOS")), file_name="Suplementos.pdf")
        with tabs[3]:
            st.markdown(f'<div class="result-card-unificado"><small>{e4}</small><br>{r4}</div>', unsafe_allow_html=True)
            st.download_button("PDF Treino", data=bytes(gerar_pdf(nome_perfil, idade, altura, peso, imc, objetivo, r4, "TREINO")), file_name="Treino.pdf")
        with tabs[4]:
            full = f"# AVALIAÇÃO\n{r1}\n\n# NUTRIÇÃO\n{r2}\n\n# SUPLEMENTOS\n{r3}\n\n# TREINO\n{r4}"
            st.markdown(f'<div class="result-card-unificado">{full}</div>', unsafe_allow_html=True)
            st.download_button("BAIXAR DOSSIÊ", data=bytes(gerar_pdf(nome_perfil, idade, altura, peso, imc, objetivo, full, "DOSSIÊ")), file_name="Dossie.pdf")

    except Exception as e: st.error(f"Erro: {e}")
else: st.info("Preencha o perfil e anexe a foto na barra lateral.")
