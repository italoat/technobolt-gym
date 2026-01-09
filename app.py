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

# --- BANCO DE DADOS DE USUÁRIOS ---
USUARIOS_DB = {
    "admin": "admin123",
    "pedro.santana": "senha",
    "luiza.trovao": "senha",
    "anderson.bezerra": "senha",
    "fabricio.felix": "senha",
    "jackson.antonio": "senha",
    "italo.trovao": "senha",
    "julia.fernanda": "senha",
    "convidado": "senha"
}

# --- ESTADO INICIAL ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "user_atual" not in st.session_state:
    st.session_state.user_atual = ""

# --- DESIGN SYSTEM ---
st.markdown("""
<style>
    .main-card { background-color: #111; padding: 20px; border-radius: 15px; border-left: 5px solid #3b82f6; margin-bottom: 20px; }
    .result-card-unificado { 
        background-color: #1a1a1a !important; 
        color: #ffffff !important; 
        padding: 25px; 
        border-radius: 15px; 
        border-top: 6px solid #3b82f6; 
        margin-top: 20px;
    }
    .result-card-unificado * { color: #ffffff !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [aria-selected="true"] { background-color: #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.markdown('<div class="main-card"><h1>TechnoBolt Gym</h1><p>Acesse sua Consultoria de Elite</p></div>', unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if u in USUARIOS_DB and USUARIOS_DB[u] == p:
                st.session_state.logado = True
                st.session_state.user_atual = u
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
    st.stop()

# --- FUNÇÃO PDF ---
def gerar_pdf(nome, idade, altura, peso, imc, objetivo, conteudo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "TECHNOBOLT GYM - DOSSIÊ DE ELITE", ln=True, align="C")
    pdf.ln(10)
    pdf.set_fill_color(30, 30, 30)
    pdf.set_text_color(59, 130, 246)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f" ATLETA: {nome.upper()}", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Idade: {idade}a | Peso: {peso}kg | IMC: {imc:.2f}", ln=True, border='B')
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 10)
    # Limpeza de formatação para o PDF
    clean_text = conteudo.replace('#', '').replace('*', '').replace('>', '').replace('-', '•')
    pdf.multi_cell(0, 7, clean_text.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S')

# --- SIDEBAR (PERFIL + LOGOUT) ---
with st.sidebar:
    st.header(f"Bem-vindo, {st.session_state.user_atual.capitalize()}")
    if st.button("Sair/Logout"):
        st.session_state.logado = False
        st.rerun()
    st.divider()
    st.subheader("📋 Perfil Biométrico")
    nome = st.text_input("Nome Completo", value=st.session_state.user_atual.replace('.', ' ').capitalize())
    idade = st.number_input("Idade", 12, 90, 25)
    altura = st.number_input("Altura (cm)", 100, 250, 170)
    peso = st.number_input("Peso (kg)", 30.0, 250.0, 75.0)
    objetivo = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    up = st.file_uploader("📸 Foto Bio-Análise", type=['jpg', 'png', 'jpeg'])

# --- HUB DE INTELIGÊNCIA ---
if up and nome:
    try:
        bytes_data = up.getvalue()
        img_input = Image.open(io.BytesIO(bytes_data))
        img_raw = ImageOps.exif_transpose(img_input).convert("RGB")
        img_raw.thumbnail((600, 600), Image.Resampling.LANCZOS)
        gc.collect()
        
        imc = peso / ((altura/100)**2)
        api_key = os.environ.get("GEMINI_API_KEY") or (st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else None)
        if not api_key: st.stop()
        genai.configure(api_key=api_key)

        MODEL_FAILOVER_LIST = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-2.0-flash-lite", "models/gemini-flash-latest"]

        def processar(prompt):
            for model_name in MODEL_FAILOVER_LIST:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content([prompt, img_raw])
                    return response.text, model_name
                except: continue
            return "Erro nos motores.", "OFFLINE"

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino", "📜 Completo"])

        with tab1:
            p1 = f"RETORNE APENAS O CONTEÚDO TÉCNICO. PROIBIDO SAUDAÇÕES. Aja como PhD em Antropometria. Analise {nome}, {idade}a, IMC {imc:.2f}. Biotipo, BF% e Postura. Traduza termos técnicos entre parênteses."
            res1, eng1 = processar(p1)
            st.markdown(f'<div class="result-card-unificado"><div style="text-align:right; font-size:10px; color:#555;">ENGINE: {eng1}</div>{res1}</div>', unsafe_allow_html=True)
            st.download_button("Baixar PDF Avaliação", data=bytes(gerar_pdf(nome, idade, altura, peso, imc, objetivo, res1)), file_name="Avaliacao.pdf")

        with tab2:
            p2 = f"RETORNE APENAS O CONTEÚDO TÉCNICO. PROIBIDO SAUDAÇÕES. Aja como Nutricionista PhD. Objetivo: {objetivo}. GET, Macros e Alimentos p/ biotipo. Traduza termos técnicos entre parênteses."
            res2, eng2 = processar(p2)
            st.markdown(f'<div class="result-card-unificado"><div style="text-align:right; font-size:10px; color:#555;">ENGINE: {eng2}</div>{res2}</div>', unsafe_allow_html=True)
            st.download_button("Baixar PDF Nutrição", data=bytes(gerar_pdf(nome, idade, altura, peso, imc, objetivo, res2)), file_name="Nutricao.pdf")

        with tab3:
            p3 = f"RETORNE APENAS O CONTEÚDO TÉCNICO. PROIBIDO SAUDAÇÕES. Especialista em Suplementação. Indique 3 suplementos p/ {objetivo} e este perfil. Justifique (Nexo Metabólico) e traduza termos técnicos entre parênteses."
            res3, eng3 = processar(p3)
            st.markdown(f'<div class="result-card-unificado"><div style="text-align:right; font-size:10px; color:#555;">ENGINE: {eng3}</div>{res3}</div>', unsafe_allow_html=True)
            st.download_button("Baixar PDF Suplementos", data=bytes(gerar_pdf(nome, idade, altura, peso, imc, objetivo, res3)), file_name="Suplementos.pdf")

        with tab4:
            p4 = f"RETORNE APENAS O CONTEÚDO TÉCNICO. PROIBIDO SAUDAÇÕES. Personal Trainer PhD. Monte treino de 7 dias p/ {objetivo}. Para CADA exercício: Justificativa Técnica, Alternativa de Substituição e tradução de termos técnicos entre parênteses."
            res4, eng4 = processar(p4)
            st.markdown(f'<div class="result-card-unificado"><div style="text-align:right; font-size:10px; color:#555;">ENGINE: {eng4}</div>{res4}</div>', unsafe_allow_html=True)
            st.download_button("Baixar PDF Treino", data=bytes(gerar_pdf(nome, idade, altura, peso, imc, objetivo, res4)), file_name="Treino.pdf")

        with tab5:
            completo = f"# AVALIAÇÃO\n{res1}\n\n# NUTRIÇÃO\n{res2}\n\n# SUPLEMENTOS\n{res3}\n\n# TREINO\n{res4}"
            st.markdown(f'<div class="result-card-unificado">{completo}</div>', unsafe_allow_html=True)
            st.download_button("BAIXAR DOSSIÊ COMPLETO", data=bytes(gerar_pdf(nome, idade, altura, peso, imc, objetivo, completo)), file_name=f"Dossie_{nome}.pdf")

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
else:
    st.info("Preencha os dados e anexe a foto na barra lateral.")
