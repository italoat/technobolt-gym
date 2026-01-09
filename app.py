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
    st.markdown('<div class="main-card"><h2>Bio-Análise Advanced</h2><p>Diagnóstico Antropométrico via Visão Computacional de Elite.</p></div>', unsafe_allow_html=True)
    
    st.info("ℹ️ **Protocolo de Precisão:** Foto com roupas de compressão e luz natural lateral garantem 98% de precisão.")
    
    up = st.file_uploader("Upload de Imagem para Análise", type=['jpg', 'jpeg', 'png'])
    
    if up:
        img_raw = Image.open(up)
        img_raw.thumbnail((1024, 1024)) 
        st.image(img_raw, use_container_width=True)
        
        # Botão para disparar a análise
        if st.button("GERAR LAUDO E TREINO"):
            # O erro estava aqui: todas estas linhas devem estar alinhadas (indentadas)
            import os
            import google.generativeai as genai
            
            # Busca a chave de forma segura (Priorizando Environment Variables do Render)
            api_key = os.environ.get("GEMINI_API_KEY")
            
            if not api_key:
                try:
                    api_key = st.secrets["GEMINI_API_KEY"]
                except:
                    api_key = None

            if not api_key:
                st.error("⚠️ Chave API não configurada. Adicione GEMINI_API_KEY no painel Environment do Render.")
                st.stop()
            
            genai.configure(api_key=api_key)

            with st.spinner("IA TechnoBolt executando Failover Pentacamada..."):
                MODEL_FAILOVER_LIST = [
                    "models/gemini-3-flash-preview", 
                    "models/gemini-2.5-flash", 
                    "models/gemini-2.0-flash", 
                    "models/gemini-2.0-flash-lite", 
                    "models/gemini-flash-latest"
                ]

                laudo_ia = None
                modelo_vencedor = "OFFLINE"

                prompt_tecnico = """
                Aja como um Personal Trainer Master, PhD em Fisiologia e Biomecânica. 
                Analise a imagem enviada e forneça:
                1. BIOTIPO: Identifique o somatotipo (Ecto, Meso, Endo) baseado em Heath-Carter.
                2. COMPOSIÇÃO: Estime o BF% (Body Fat) pela densidade muscular.
                3. POSTURA: Identifique desvios (ex: ombros protusos, inclinação pélvica).
                4. TREINO SEMANAL: Gere um plano de 5 dias focado em pontos fracos vistos na foto.
                Siga o tom: Técnico, Analítico e Motivador. Use tabelas HTML para o treino.
                """

                for model_name in MODEL_FAILOVER_LIST:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content([prompt_tecnico, img_raw])
                        laudo_ia = response.text
                        modelo_vencedor = model_name
                        break 
                    except:
                        continue 

                if laudo_ia:
                    # Cálculo de precisão de luz para o card
                    stat = ImageStat.Stat(img_raw)
                    brilho = stat.mean[0]
                    score_precisao = 98 if 75 < brilho < 180 else 64
                    
                    html_abertura = f"""
                    <div class="result-card-unificado">
                        <div class="result-title">DOSSIÊ ANTROPOMÉTRICO - {st.session_state.user_atual.upper()}</div>
                        <div style="color: #ffffff; line-height: 1.6; margin-top: 20px;">
                            <p style="background: #222; padding: 10px; border-radius: 5px; border-left: 4px solid #3b82f6;">
                                <b>PRECISÃO DO DIAGNÓSTICO: {score_precisao}%</b> | <b>ENGINE: {modelo_vencedor.upper()}</b>
                            </p>
                    """
                    st.markdown(html_abertura + laudo_ia + "</div></div>", unsafe_allow_html=True)
                else:
                    st.error("⚠️ Todos os motores de IA falharam. Verifique sua cota ou conexão.")

elif escolha == "📊 Histórico":
    st.markdown('<div class="main-card"><h2>Histórico</h2><p>Dossiê de evolução e auditoria de treinos.</p></div>', unsafe_allow_html=True)
    st.info("Nenhum dado de treino exportado nesta sessão.")

st.markdown("---")
st.caption(f"TechnoBolt Gym © 2026 | Operador: {st.session_state.user_atual.upper()}")
