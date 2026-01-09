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

# --- DESIGN SYSTEM TECHNOBOLT (Blindado para iPhone/Android/PC) ---
st.markdown("""
<style>
    /* --- BLINDAGEM TOTAL DE BOTÕES --- */
    
    /* Botão Padrão e Botão de Download */
    button, .stButton>button, .stDownloadButton>button {
        background-color: #3b82f6 !important; /* Azul TechnoBolt */
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        width: 100% !important; /* Faz o botão ocupar a largura disponível no mobile */
        margin-bottom: 10px !important;
    }

    /* Efeito de Hover (Passar o mouse) */
    button:hover, .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #2563eb !important; /* Azul mais escuro no hover */
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-2px) !important;
    }

    /* Botões dentro da Barra Lateral (Sidebar) */
    [data-testid="stSidebar"] button {
        background-color: #222 !important;
        border: 1px solid #3b82f6 !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: #3b82f6 !important;
    }

    /* Ajuste para o texto não sumir em botões brancos residuais */
    .stBaseButton-secondary {
        background-color: #222 !important;
        color: white !important;
    }

    /* Forçar ícones dentro de botões a serem brancos */
    button p, button svg {
        color: white !important;
        fill: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.markdown('<div class="main-card"><h1>TechnoBolt Gym</h1><p>Acesse sua Consultoria de Elite</p></div>', unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("AUTENTICAR"):
            if u in USUARIOS_DB and USUARIOS_DB[u] == p:
                st.session_state.logado = True
                st.session_state.user_atual = u
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
    st.stop()

# --- FUNÇÃO DE GERAÇÃO DE PDF PROFISSIONAL ---
def gerar_pdf(nome, idade, altura, peso, imc, objetivo, conteudo, titulo_doc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"TECHNOBOLT GYM - {titulo_doc}", ln=True, align="C")
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, f"Data: {time.strftime('%d/%m/%Y')} | Atleta: {nome}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_fill_color(30, 30, 30); pdf.set_text_color(59, 130, 246)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f" PERFIL ANALISADO: {nome.upper()}", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Idade: {idade}a | Estatura: {altura}cm | Massa: {peso}kg | IMC: {imc:.2f}", ln=True, border='B')
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 10)
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

# --- HUB DE INTELIGÊNCIA PENTACAMADA ---
if up and nome:
    try:
        # Buffer Anti-Logout e Otimização Mobile
        bytes_data = up.getvalue()
        img_input = Image.open(io.BytesIO(bytes_data))
        img_raw = ImageOps.exif_transpose(img_input).convert("RGB")
        img_raw.thumbnail((600, 600), Image.Resampling.LANCZOS)
        gc.collect()
        
        imc = peso / ((altura/100)**2)
        api_key = os.environ.get("GEMINI_API_KEY") or (st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else None)
        if not api_key: st.stop()
        genai.configure(api_key=api_key)

        # SEUS MOTORES PENTACAMADA
        MODEL_FAILOVER_LIST = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-2.0-flash-lite", "models/gemini-flash-latest"]

        def processar_ia(prompt):
            for model_name in MODEL_FAILOVER_LIST:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content([prompt, img_raw])
                    return response.text, model_name
                except: continue
            return "Erro nos motores.", "OFFLINE"

        # --- POPUP DE ESCANEAMENTO BIOMÉTRICO ---
        with st.empty():
            # GIF de Scanner Futurista
            gif_url = "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJqZ3R3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3bmZ3JlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKMGpxx303Z3o9G/giphy.gif"
            st.markdown(f"""
                <div style="text-align:center; padding:30px; background:rgba(0,0,0,0.9); border-radius:20px; border:2px solid #3b82f6; box-shadow: 0 0 20px #3b82f6;">
                    <img src="{gif_url}" width="220" style="filter: hue-rotate(180deg); margin-bottom:15px; border-radius:50%;">
                    <h2 class="scanning-text">ESCANEANDO PADRÕES BIOMÉTRICOS...</h2>
                    <p style="color:#ffffff; font-size:14px; opacity:0.8;">A IA TechnoBolt está mapeando seu nexo metabólico e biomecânico.</p>
                    <audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-20.mp3" type="audio/mpeg"></audio>
                </div>
            """, unsafe_allow_html=True)

            # Chamadas dos Especialistas em Background
            p1 = f"RETORNE APENAS O CONTEÚDO TÉCNICO. PROIBIDO SAUDAÇÕES. Aja como PhD em Antropometria. Analise {nome}, {idade}a, IMC {imc:.2f}. Determine Biotipo, BF% e Postura. Traduza termos técnicos entre parênteses."
            res1, eng1 = processar_ia(p1)
            
            p2 = f"RETORNE APENAS O CONTEÚDO TÉCNICO. PROIBIDO SAUDAÇÕES. Aja como Nutricionista PhD. Objetivo: {objetivo}. Determine GET, Macros e Alimentos p/ biotipo. Traduza termos técnicos entre parênteses."
            res2, eng2 = processar_ia(p2)
            
            p3 = f"RETORNE APENAS O CONTEÚDO TÉCNICO. PROIBIDO SAUDAÇÕES. Especialista em Suplementação. Indique 3 suplementos p/ {objetivo} e este perfil. Justifique (Nexo Metabólico) e traduza termos técnicos entre parênteses."
            res3, eng3 = processar_ia(p3)
            
            p4 = f"RETORNE APENAS O CONTEÚDO TÉCNICO. PROIBIDO SAUDAÇÕES. Personal Trainer PhD. Monte treino de 7 dias p/ {objetivo}. Para CADA exercício: Justificativa Técnica, Alternativa de Substituição e tradução de termos técnicos entre parênteses."
            res4, eng4 = processar_ia(p4)
            
            time.sleep(1.5) # Tempo para imersão no scanner
            st.empty() # Remove o scanner

        # --- EXIBIÇÃO EM ABAS (CARDS DE ELITE) ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino", "📜 Completo"])

        with tab1:
            st.markdown(f'<div class="result-card-unificado"><div class="engine-tag">ENGINE: {eng1}</div>{res1}</div>', unsafe_allow_html=True)
            st.download_button("📥 Baixar PDF Avaliação", data=bytes(gerar_pdf(nome, idade, altura, peso, imc, objetivo, res1, "AVALIAÇÃO")), file_name="Avaliacao.pdf")

        with tab2:
            st.markdown(f'<div class="result-card-unificado"><div class="engine-tag">ENGINE: {eng2}</div>{res2}</div>', unsafe_allow_html=True)
            st.download_button("📥 Baixar PDF Nutrição", data=bytes(gerar_pdf(nome, idade, altura, peso, imc, objetivo, res2, "NUTRIÇÃO")), file_name="Nutricao.pdf")

        with tab3:
            st.markdown(f'<div class="result-card-unificado"><div class="engine-tag">ENGINE: {eng3}</div>{res3}</div>', unsafe_allow_html=True)
            st.download_button("📥 Baixar PDF Suplementos", data=bytes(gerar_pdf(nome, idade, altura, peso, imc, objetivo, res3, "SUPLEMENTAÇÃO")), file_name="Suplementos.pdf")

        with tab4:
            st.markdown(f'<div class="result-card-unificado"><div class="engine-tag">ENGINE: {eng4}</div>{res4}</div>', unsafe_allow_html=True)
            st.download_button("📥 Baixar PDF Treino", data=bytes(gerar_pdf(nome, idade, altura, peso, imc, objetivo, res4, "TREINAMENTO")), file_name="Treino.pdf")

        with tab5:
            full = f"# AVALIAÇÃO\n{res1}\n\n# NUTRIÇÃO\n{res2}\n\n# SUPLEMENTAÇÃO\n{res3}\n\n# TREINO\n{res4}"
            st.markdown(f'<div class="result-card-unificado"><div class="engine-tag">DOSSIÊ UNIFICADO</div>{full}</div>', unsafe_allow_html=True)
            st.download_button("📥 BAIXAR RELATÓRIO COMPLETO", data=bytes(gerar_pdf(nome, idade, altura, peso, imc, objetivo, full, "DOSSIÊ COMPLETO")), file_name=f"Dossie_{nome}.pdf")

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
else:
    st.info("Complete seu perfil e anexe a foto na barra lateral para iniciar o escaneamento.")
