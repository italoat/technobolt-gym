import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import time
import os
import re
from fpdf import FPDF

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TechnoBolt Gym Hub", layout="wide", page_icon="🏋️")

# --- DESIGN SYSTEM TECHNOBOLT (BLINDAGEM TOTAL) ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
    
    /* FIX DA SETA: Oculta texto Keyboard_double_arrow... */
    [data-testid="stSidebarCollapseButton"] { color: transparent !important; font-size: 0px !important; }
    [data-testid="stSidebarCollapseButton"] span { display: none !important; }
    [data-testid="stSidebarCollapseButton"] svg {
        fill: #3b82f6 !important;
        visibility: visible !important;
        width: 28px !important;
        height: 28px !important;
    }

    .result-card-unificado { 
        background-color: #0a0a0a !important; 
        border-left: 6px solid #3b82f6;
        border-radius: 15px;
        padding: 25px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- MOTOR DE PROCESSAMENTO (ANÁLISE ÚNICA) ---
def realizar_scan_phd(prompt_mestre, img_pil):
    # Converte imagem uma única vez para evitar NameError e Bytearray error
    img_byte_arr = io.BytesIO()
    img_pil.save(img_byte_arr, format='JPEG')
    img_blob = {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}

    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") or st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    
    # SEUS MOTORES INTOCÁVEIS
    motores = [
        "models/gemini-3-flash-preview", 
        "models/gemini-2.5-flash", 
        "models/gemini-2.0-flash", 
        "models/gemini-2.0-flash-lite", 
        "models/gemini-flash-latest"
    ]

    for idx, key in enumerate(chaves):
        try:
            genai.configure(api_key=key)
            for m in motores:
                try:
                    model = genai.GenerativeModel(m)
                    response = model.generate_content([prompt_mestre, img_blob])
                    return response.text, f"CONTA {idx+1} - {m.upper()}"
                except Exception as e:
                    if "429" in str(e): break
                    continue
        except: continue
    return None, "OFFLINE"

# --- SISTEMA DE LOGIN ---
USUARIOS_DB = {
    "admin": "admin123", "pedro.santana": "senha", "luiza.trovao": "senha",
    "anderson.bezerra": "senha", "fabricio.felix": "senha", "jackson.antonio": "senha",
    "italo.trovao": "senha", "julia.fernanda": "senha", "convidado": "senha"
}
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.markdown('<div><h1>TechnoBolt Gym</h1><p>Consultoria de Elite</p></div>', unsafe_allow_html=True)
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("AUTENTICAR"):
        if u in USUARIOS_DB and USUARIOS_DB[u] == p:
            st.session_state.logado = True
            st.session_state.user_atual = u
            st.rerun()
    st.stop()

# --- SIDEBAR (DEFINIÇÃO DAS VARIÁVEIS ANTES DO USO) ---
with st.sidebar:
    st.header(f"Olá, {st.session_state.user_atual.split('.')[0].capitalize()}")
    if st.button("SAIR"): st.session_state.logado = False; st.rerun()
    st.divider()
    nome_perfil = st.text_input("Nome Completo", value=st.session_state.user_atual.capitalize())
    idade = st.number_input("Idade", 12, 90, 25)
    altura = st.number_input("Altura (cm)", 100, 250, 175)
    peso = st.number_input("Peso (kg)", 30.0, 250.0, 80.0)
    objetivo = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    # AQUI DEFINIMOS 'up' PARA EVITAR O NAMEERROR
    up = st.file_uploader("📸 Foto para Análise", type=['jpg', 'jpeg', 'png'])

# --- FLUXO DE PROCESSAMENTO ---
if up and nome_perfil:
    try:
        img_raw = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        img_raw.thumbnail((600, 600))
        imc = peso / ((altura/100)**2)

        if 'resultado_tecnico' not in st.session_state:
            with st.status("🧬 ATIVANDO TIME DE PHDS TECHNOBOLT...", expanded=True) as status:
                # O PROMPT MESTRE COM TODAS AS FORMAÇÕES RESTAURADAS
                prompt_mestre = f"""
                VOCÊ É UM CONSELHO DE ESPECIALISTAS PHD DA TECHNOBOLT GYM. 
                ANÁLISE PARA O ATLETA: {nome_perfil} | OBJETIVO: {objetivo} | IMC: {imc:.2f}

                FORNEÇA 4 RELATÓRIOS TÉCNICOS SEPARADOS RIGOROSAMENTE PELA TAG '[DIVISOR]':

                1. AVALIAÇÃO ANTROPOMÉTRICA: Aja como PhD formado com Certificação Internacional ISAK (Níveis 1 a 4), Cineantropometria Avançada, Ultrassonografia, DXA e Bioestatística. Determine Biotipo, BF% e Postura.
                
                2. PLANEJAMENTO NUTRICIONAL: Aja como Nutricionista PhD especialista em Nutrição Esportiva, Clínica e Funcional, Fitoterapia e Nutrigenômica. Determine GET, Macros e Plano Alimentar.

                3. PROTOCOLO DE SUPLEMENTAÇÃO: Aja como Especialista PhD em Suplementação Esportiva e Farmacologia do Exercício. Indique 3 a 10 suplementos com base no Nexo Metabólico.

                4. PRESCRIÇÃO DE TREINO: Aja como Personal Trainer PhD em Biomecânica, Fisiologia do Exercício e LPO. Forneça treino de 7 dias com justificativa biomecânica.

                REGRAS: Use tópicos curtos. Proibido saudações. Use linguagem de elite.
                """
                
                resultado, engine = realizar_scan_phd(prompt_mestre, img_raw)
                
                if resultado:
                    partes = resultado.split('[DIVISOR]')
                    st.session_state.r1 = partes[0] if len(partes) > 0 else "Análise indisponível."
                    st.session_state.r2 = partes[1] if len(partes) > 1 else "Análise indisponível."
                    st.session_state.r3 = partes[2] if len(partes) > 2 else "Análise indisponível."
                    st.session_state.r4 = partes[3] if len(partes) > 3 else "Análise indisponível."
                    st.session_state.resultado_tecnico = True
                status.update(label="✅ ANÁLISE CONCLUÍDA!", state="complete")

        # EXIBIÇÃO EM ABAS
        tabs = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino"])
        with tabs[0]: st.markdown(f"<div class='result-card-unificado'>{st.session_state.r1}</div>", unsafe_allow_html=True)
        with tabs[1]: st.markdown(f"<div class='result-card-unificado'>{st.session_state.r2}</div>", unsafe_allow_html=True)
        with tabs[2]: st.markdown(f"<div class='result-card-unificado'>{st.session_state.r3}</div>", unsafe_allow_html=True)
        with tabs[3]: st.markdown(f"<div class='result-card-unificado'>{st.session_state.r4}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
else:
    st.markdown("""
        <div class="result-card-unificado" style="text-align:center;">
            <div style="font-size: 50px; margin-bottom: 20px;">👤</div>
            <h2 style="color:#3b82f6; letter-spacing: 2px;">TECHNOBOLT GYM HUB</h2>
            <p style="color:#888; font-size:16px;">Aguardando entrada de dados na barra lateral...</p>
        </div>
    """, unsafe_allow_html=True)
