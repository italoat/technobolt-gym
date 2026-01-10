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

# --- DESIGN SYSTEM TECHNOBOLT (CORREÇÃO DEFINITIVA DA SETA) ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
    
    /* FIX DA SETA: Oculta o texto residual e mantém apenas o ícone azul */
    [data-testid="stSidebarCollapseButton"] {
        color: transparent !important;
        font-size: 0px !important;
    }
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

# --- MOTOR DE PROCESSAMENTO ÚNICO (ESTRATEGIA SCANNER PHD) ---
def realizar_scan_phd(prompt_mestre, img_pil):
    # Criamos o pacote de dados uma única vez para evitar erro de binário
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
                    # O Scanner processa a imagem UMA ÚNICA VEZ
                    response = model.generate_content([prompt_mestre, img_blob])
                    return response.text, f"CONTA {idx+1} - {m.upper()}"
                except Exception as e:
                    if "429" in str(e): break
                    continue
        except: continue
    return None, "OFFLINE"

# --- LOGIN E INPUTS ---
# [Mantenha aqui seu código de login e st.sidebar com nome, idade, peso, altura, objetivo e up]

if up and nome_perfil:
    try:
        img_raw = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        img_raw.thumbnail((600, 600))
        imc = peso / ((altura/100)**2)

        if 'resultado_tecnico' not in st.session_state:
            with st.status("🧬 ATIVANDO TIME DE PHDS TECHNOBOLT...", expanded=True) as status:
                
                # --- O PROMPT MESTRE COM TODAS AS FORMAÇÕES RESTAURADAS ---
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
                    # Divisão inteligente baseada na tag [DIVISOR]
                    partes = resultado.split('[DIVISOR]')
                    st.session_state.r1 = partes[0] if len(partes) > 0 else "Erro"
                    st.session_state.r2 = partes[1] if len(partes) > 1 else "Erro"
                    st.session_state.r3 = partes[2] if len(partes) > 2 else "Erro"
                    st.session_state.r4 = partes[3] if len(partes) > 3 else "Erro"
                    st.session_state.resultado_tecnico = True
                status.update(label="✅ ANÁLISE MULTIDISCIPLINAR CONCLUÍDA!", state="complete")

        # EXIBIÇÃO EM ABAS (Dados fixos em memória, erro de binário impossível aqui)
        tabs = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino"])
        with tabs[0]: st.markdown(f"<div class='result-card-unificado'>{st.session_state.r1}</div>", unsafe_allow_html=True)
        with tabs[1]: st.markdown(f"<div class='result-card-unificado'>{st.session_state.r2}</div>", unsafe_allow_html=True)
        with tabs[2]: st.markdown(f"<div class='result-card-unificado'>{st.session_state.r3}</div>", unsafe_allow_html=True)
        with tabs[3]: st.markdown(f"<div class='result-card-unificado'>{st.session_state.r4}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
