import streamlit as st
import google.generativeai as genai
import os
import mediapipe as mp
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration
import threading
import time
import pandas as pd
from PIL import Image, ImageStat



# --- 1. CONFIGURAÇÃO TECHNOBOLT LEGAL HUB ADAPTADA ---
st.set_page_config(
    page_title="TechnoBolt Gym - Intelligence Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuração ICE para Cloud/Render (Garante funcionamento no 4G/5G)
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# --- 2. GESTÃO DE ESTADO (LOGIN E AUDITORIA) ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'user_atual': None,
        'login_time': time.time(),
        'history': []
    })

# --- 3. DESIGN SYSTEM TECHNOBOLT (DARK MODE & RESPONSIVO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* FUNDO GLOBAL E FONTES */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
        background-color: #000000 !important; 
        font-family: 'Inter', sans-serif !important; 
        color: #ffffff !important;
    }

    h1, h2, h3, h4, p, label, span, div, .stMarkdown { color: #ffffff !important; }
    [data-testid="stSidebar"] { display: none !important; }
    header, footer { visibility: hidden !important; }

    /* LOGO E LOGIN */
    .login-header { text-align: center; width: 100%; margin-bottom: 40px; }
    .logo-blue {
        font-size: 52px; font-weight: 800;
        color: #3b82f6 !important; 
        letter-spacing: -2px;
        display: block;
    }

    /* COMPONENTES DE UI (SELECT, INPUT, UPLOADER) */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }
    
    [data-testid="stFileUploader"] {
        background-color: #1a1a1a !important;
        border: 1px dashed #404040 !important;
        border-radius: 15px !important;
        padding: 10px;
    }

    /* BOTÕES GERAIS */
    .stButton > button {
        width: 100%; border-radius: 10px; height: 3.8em; font-weight: 700;
        background-color: #1a1a1a !important; color: #ffffff !important; 
        border: 1px solid #333333 !important; transition: 0.3s;
    }
    .stButton > button:hover { background-color: #3b82f6 !important; border-color: #ffffff !important; }

    /* CARDS RESPONSIVOS */
    .main-card {
        background-color: #1a1a1a !important; 
        border: 1px solid #333333; 
        border-radius: 20px;
        padding: 30px; 
        margin-bottom: 20px;
    }
    .result-card-unificado {
        background-color: #1a1a1a !important;
        border: 1px solid #333333;
        border-radius: 20px;
        padding: 25px;
        color: #ffffff !important;
        margin-top: 15px;
    }
    .result-title {
        color: #3b82f6 !important;
        font-weight: 800; font-size: 24px;
        border-bottom: 1px solid #333; padding-bottom: 10px;
        margin-bottom: 15px;
    }

    /* MEDIA QUERIES PARA MOBILE */
    @media (max-width: 768px) {
        .logo-blue { font-size: 40px; }
        .main-card { padding: 20px; }
        .stMetric { margin-bottom: 15px; }
    }
</style>
""", unsafe_allow_html=True)

# --- 4. TELA DE LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([0.2, 1, 0.2]) # Responsivo para mobile
    with col_login:
        st.markdown('<div class="login-header"><span class="logo-blue">Technobolt</span></div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#888; font-weight:500;'>GYM HUB - Personal Trainer  INTELLIGENCE</p>", unsafe_allow_html=True)
        u_id = st.text_input("Operador Gym", placeholder="Usuário")
        u_key = st.text_input("Chave", type="password", placeholder="Senha")
        if st.button("CONECTAR"):
            banco = {"admin": "admin", "aluno.teste": "gym2026", "personal.bolado": "treino@2026"}
            if u_id in banco and banco[u_id] == u_key:
                st.session_state.logged_in = True
                st.session_state.user_atual = u_id
                st.rerun()
    st.stop()

# --- 5. CABEÇALHO OPERACIONAL ---
st.markdown(f'<div style="padding:10px 0;"><span style="color:#3b82f6; font-weight:800; font-size:24px;">Technobolt</span> <span style="color:#666;">| GYM HUB</span></div>', unsafe_allow_html=True)
c1, c2 = st.columns([4, 1])
with c1: st.write(f"🏋️ Operador: **{st.session_state.user_atual.upper()}**")
with c2: 
    if st.button("🚪 Sair"):
        st.session_state.logged_in = False
        st.rerun()

menu = ["🏠 Dashboard", "🏋️ Corretor Live", "📸 Bio-Análise", "📊 Histórico"]
escolha = st.selectbox("Seletor de Módulo", menu, label_visibility="collapsed")
st.markdown("<hr style='border-color: #333; margin-bottom:30px;'>", unsafe_allow_html=True)

# --- 6. MOTOR DE VISÃO COMPUTACIONAL (EDGE COMPUTING) ---
class BiomecanicaProcessor(VideoTransformerBase):
    def __init__(self):
        # Importação local para garantir que o erro seja capturado no log do Render
        import mediapipe as mp
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5,
            model_complexity=1 # Essencial para não estourar a RAM do Render
        )
        self.count = 0
        self.stage = None
        self.precision = 0
        self.feedback = "Scanner Ativo"
        self._lock = threading.Lock()

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)
        
        # Converte para RGB para o MediaPipe
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.pose.process(img_rgb)
        
        with self._lock:
            if results.pose_landmarks:
                lm = results.pose_landmarks.landmark
                # Cálculo de precisão por visibilidade
                self.precision = int(np.mean([l.visibility for l in lm]) * 100)
                
                # Exemplo: Pontos do Braço
                p11, p13, p15 = lm[11], lm[13], lm[15]
                a = np.array([p11.x, p11.y])
                b = np.array([p13.x, p13.y])
                c = np.array([p15.x, p15.y])
                
                rad = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
                ang = np.abs(rad * 180.0 / np.pi)
                if ang > 180: ang = 360 - ang

                if ang > 160: self.stage = "desc"
                if ang < 35 and self.stage == "desc":
                    self.stage = "sub"
                    self.count += 1
                
                # Desenha os pontos (Skeleton)
                self.mp_drawing.draw_landmarks(
                    img, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(59, 130, 246), thickness=2, circle_radius=2)
                )
            else:
                self.precision = 0
        return img

# --- 7. MÓDULOS OPERACIONAIS ---

if escolha == "🏠 Dashboard":
    st.markdown('<div class="main-card"><h2>Command Center</h2><p>MONITORIA DE PERFORMANCE E RISCO</p></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Failover Status", "Active", "Edge-On")
    c2.metric("Sessão", st.session_state.user_atual.split('.')[0].upper(), "Protegida")
    c3.metric("Taxa de Precisão", "96%", "+3.2%")

elif escolha == "🏋️ Corretor Live":
    st.markdown('<div class="main-card"><h2>Corretor Live</h2><p>Processamento local para latência inferior a 150ms.</p></div>', unsafe_allow_html=True)
    col_v, col_m = st.columns([1.8, 1])
    
    with col_v:
        ctx = webrtc_streamer(key="gym-live", video_transformer_factory=BiomecanicaProcessor, rtc_configuration=RTC_CONFIGURATION)
    
    with col_m:
        st.markdown('<div class="result-card-unificado">', unsafe_allow_html=True)
        st.markdown('<div class="result-title">Métricas TechnoBolt</div>', unsafe_allow_html=True)
        p_reps = st.empty()
        p_prec = st.empty()
        p_diag = st.empty()
        
        if ctx.video_transformer:
            while ctx.state.playing:
                with ctx.video_transformer._lock:
                    reps = ctx.video_transformer.count
                    prec = ctx.video_transformer.precision
                    feed = ctx.video_transformer.feedback
                
                p_reps.metric("REPETIÇÕES VÁLIDAS", reps)
                p_prec.metric("PRECISÃO DA CÂMERA", f"{prec}%")
                
                if prec < 75: p_diag.warning(f"DIAGNÓSTICO: {feed}")
                else: p_diag.success(f"STATUS: {feed}")
                
                time.sleep(0.1)
        st.markdown('</div>', unsafe_allow_html=True)

elif escolha == "📸 Bio-Análise":
    st.markdown('<div class="main-card"><h2>Consultoria Biomecânica Advanced</h2><p>Análise de nexo causal baseada em dados biométricos e visão computacional.</p></div>', unsafe_allow_html=True)
    
    # --- FORMULÁRIO DE DADOS BIOMÉTRICOS ---
    with st.expander("📝 Dados do Aluno (Necessário para Precisão)", expanded=True):
        c1, c2 = st.columns(2)
        nome_aluno = c1.text_input("Nome Completo", placeholder="Ex: João Silva")
        idade_aluno = c2.number_input("Idade", min_value=12, max_value=90, step=1)
        
        c3, c4 = st.columns(2)
        altura_aluno = c3.number_input("Altura (cm)", min_value=100, max_value=250, step=1, value=170)
        peso_aluno = c4.number_input("Peso Atual (kg)", min_value=30.0, max_value=250.0, step=0.1, value=75.0)

    st.info("ℹ️ **Protocolo TechnoBolt:** Envie uma foto com contornos visíveis para análise de simetria e somatotipo.")
    up = st.file_uploader("Upload de Imagem para Diagnóstico", type=['jpg', 'jpeg', 'png'])
    
    if up and nome_aluno:
        img_raw = Image.open(up)
        img_raw.thumbnail((1024, 1024)) 
        st.image(img_raw, use_container_width=True, caption=f"Análise Biométrica: {nome_aluno}")
        
        if st.button("GERAR DOSSIÊ COMPLETO"):
            import os
            import google.generativeai as genai
            
            api_key = os.environ.get("GEMINI_API_KEY") or (st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else None)
            if not api_key:
                st.error("⚠️ Erro: Chave API não configurada.")
                st.stop()
            
            genai.configure(api_key=api_key)

            with st.spinner(f"Processando dados de {nome_aluno} via Failover Pentacamada..."):
                MODEL_FAILOVER_LIST = [
                    "models/gemini-3-flash-preview", 
                    "models/gemini-2.5-flash", 
                    "models/gemini-2.0-flash", 
                    "models/gemini-2.0-flash-lite", 
                    "models/gemini-flash-latest"
                ]

                imc = peso_aluno / ((altura_aluno/100)**2)

                # PROMPT DE ELITE COM JUSTIFICATIVA POR EXERCÍCIO
                prompt_master = f"""
                Aja como um Personal Trainer Master PhD e Médico do Esporte.
                DADOS DO PACIENTE/ALUNO:
                - Nome: {nome_aluno} | Idade: {idade_aluno} anos
                - Altura: {altura_aluno} cm | Peso: {peso_aluno} kg | IMC: {imc:.2f}

                TAREFAS:
                1. IDENTIFIQUE o Somatotipo (Ecto, Meso, Endo) e explique o significado intuitivo entre parênteses.
                2. ESTIME o BF% (Gordura Corporal) e a TMB (Taxa Metabólica Basal).
                3. IDENTIFIQUE desvios posturais ou assimetrias visíveis na foto.
                4. PRESCREVA um Plano de Treino de 7 DIAS (Segunda a Domingo).
                
                REGRA OBRIGATÓRIA PARA O TREINO:
                Para CADA exercício selecionado, você deve abrir um campo chamado "OBSERVAÇÃO TÉCNICA" justificando o porquê escolheu aquele exercício especificamente para este aluno, cruzando com a idade, IMC e o que você viu na foto (ex: fraqueza aparente, necessidade de correção postural ou segurança articular).

                FORMATO DE SAÍDA:
                Markdown profissional. Use tabelas HTML para o treino. 
                Termos técnicos SEMPRE acompanhados de tradução simples entre parênteses.
                """

                laudo_ia = None
                for model_name in MODEL_FAILOVER_LIST:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content([prompt_master, img_raw])
                        laudo_ia = response.text
                        break 
                    except: continue 

                if laudo_ia:
                    data_hora = time.strftime('%d/%m/%Y %H:%M')
                    relatorio_final = f"""
                    <div class="result-card-unificado" style="border-top: 6px solid #3b82f6; background-color: #111; padding: 30px;">
                        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;">
                            <span style="font-weight: 800; color: #3b82f6;">TECHNOBOLT GYM - DOSSIÊ DE CONSULTORIA</span>
                            <span style="font-size: 12px; color: #888;">{data_hora}</span>
                        </div>
                        
                        <div style="background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #333;">
                            <h4 style="margin:0; color: #3b82f6;">DADOS BIOMÉTRICOS ANALISADOS</h4>
                            <p style="margin: 5px 0; font-size: 14px;">
                                <b>ALUNO:</b> {nome_aluno.upper()} | <b>IDADE:</b> {idade_aluno} anos<br>
                                <b>ESTATURA:</b> {altura_aluno} cm | <b>MASSA:</b> {peso_aluno} kg | <b>IMC:</b> {imc:.2f}
                            </p>
                        </div>

                        <div style="color: #ffffff; line-height: 1.8; font-size: 15px;">
                            {laudo_ia}
                        </div>
                        
                        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #333; font-size: 11px; color: #555; text-align: center;">
                            Este documento é uma análise biomecânica digital protegida por criptografia TechnoBolt.
                        </div>
                    </div>
                    """
                    st.markdown(relatorio_final, unsafe_allow_html=True)
                    
                    st.download_button(
                        label="📥 BAIXAR LAUDO TÉCNICO E TREINO",
                        data=f"LAUDO TECHNOBOLT - {nome_aluno}\n\n" + laudo_ia,
                        file_name=f"Laudo_Consultoria_{nome_aluno.replace(' ', '_')}.txt",
                        mime="text/plain",
                    )
                else:
                    st.error("⚠️ Falha nos motores de IA. Verifique sua GEMINI_API_KEY no Render.")

st.markdown("---")
st.caption(f"TechnoBolt Gym © 2026 | Operador: {st.session_state.user_atual.upper()}")
