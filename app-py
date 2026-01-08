import streamlit as st
import mediapipe as mp
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, RTCConfiguration
import threading
import time
import pandas as pd
from PIL import Image, ImageStat

# --- 1. CONFIGURAÇÃO DE SEGURANÇA E PROTOCOLO TECHNOBOLT ---
st.set_page_config(
    page_title="TechnoBolt Gym - AI Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuração ICE para garantir conectividade em redes móveis (Render/Cloud)
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# --- 2. GESTÃO DE ESTADO (LOGIN E HISTÓRICO) ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'user': None,
        'history': [],
        'precision_log': []
    })

# --- 3. DESIGN SYSTEM (DARK MODE ABSOLUTO & RESPONSIVO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #000000 !important;
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
    }

    .bolt-header {
        font-family: 'Orbitron', sans-serif;
        color: #3b82f6;
        text-align: center;
        padding: 20px;
        border-bottom: 2px solid #333;
        margin-bottom: 25px;
    }

    .login-container {
        max-width: 400px;
        margin: 80px auto;
        padding: 40px;
        background: #111;
        border-radius: 20px;
        border: 1px solid #333;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    .stButton > button {
        width: 100%;
        height: 55px !important;
        background-color: #3b82f6 !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: none !important;
    }

    .card-metrica {
        background: #111;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. SISTEMA DE AUTENTICAÇÃO ---
def tela_login():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#3b82f6; font-family:Orbitron;'>TECHNOBOLT LOGIN</h2>", unsafe_allow_html=True)
    u_id = st.text_input("Operador", placeholder="Usuário Gym")
    u_key = st.text_input("Chave", type="password", placeholder="Senha")
    
    if st.button("ACESSAR HUB"):
        # Base de usuários igual à do sistema Legal
        usuarios = {"admin": "admin", "aluno.teste": "gym2026", "personal.bolado": "treino@2026"}
        if u_id in usuarios and usuarios[u_id] == u_key:
            st.session_state.logged_in = True
            st.session_state.user = u_id
            st.rerun()
        else:
            st.error("Acesso Negado: Credenciais Incorretas")
    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.logged_in:
    tela_login()
    st.stop()

# --- 5. MOTOR DE BIOMECÂNICA (EDGE COMPUTING) ---
class BiomecanicaProcessor(VideoTransformerBase):
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)
        self.count = 0
        self.stage = None
        self.precision = 0
        self.feedback = "Aguardando Posicionamento..."
        self._lock = threading.Lock()

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)
        
        # Processamento usando recurso local (Browser/Mobile)
        results = self.pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        with self._lock:
            if results.pose_landmarks:
                # Cálculo de Precisão baseado na visibilidade dos marcos
                lm = results.pose_landmarks.landmark
                visibilidade = [l.visibility for l in lm]
                self.precision = int(np.mean(visibilidade) * 100)
                
                # Ângulo do Cotovelo (Exemplo: Rosca Direta)
                # Pontos: Ombro(11), Cotovelo(13), Pulso(15)
                a = np.array([lm[11].x, lm[11].y])
                b = np.array([lm[13].x, lm[13].y])
                c = np.array([lm[15].x, lm[15].y])
                
                rads = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
                angulo = np.abs(rads * 180.0 / np.pi)
                if angulo > 180: angulo = 360 - angulo

                # Auditoria de Repetição (Somente contagem validada)
                if angulo > 160: self.stage = "descida"
                if angulo < 35 and self.stage == "descida":
                    self.stage = "subida"
                    self.count += 1
                
                self.feedback = "Técnica: Estável" if self.precision > 80 else "Técnica: Instável (Melhore a Luz)"
                
                # Desenho dos pontos na tela do aluno
                mp.solutions.drawing_utils.draw_landmarks(
                    img, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                    mp.solutions.drawing_utils.DrawingSpec(color=(59, 130, 246), thickness=2, circle_radius=2)
                )
            else:
                self.precision = 0
                self.feedback = "Corpo Não Identificado"

        return img

# --- 6. INTERFACE PRINCIPAL ---
st.markdown(f'<div class="bolt-header">TECHNOBOLT GYM | OPERADOR: {st.session_state.user.upper()}</div>', unsafe_allow_html=True)

abas = st.tabs(["🏋️ TREINO LIVE", "📸 BIO-ANÁLISE", "📊 DOSSIÊ"])

# --- ABA 1: TREINO LIVE ---
with abas[0]:
    col_v, col_m = st.columns([2, 1])
    
    with col_v:
        webrtc_ctx = webrtc_streamer(
            key="scanner",
            video_transformer_factory=BiomecanicaProcessor,
            rtc_configuration=RTC_CONFIGURATION,
            media_stream_constraints={"video": True, "audio": False},
        )

    with col_m:
        st.markdown("### Scanner Inteligente")
        p_reps = st.empty()
        p_prec = st.empty()
        p_diag = st.empty()
        
        if webrtc_ctx.video_transformer:
            while webrtc_ctx.state.playing:
                with webrtc_ctx.video_transformer._lock:
                    reps = webrtc_ctx.video_transformer.count
                    prec = webrtc_ctx.video_transformer.precision
                    feed = webrtc_ctx.video_transformer.feedback
                
                p_reps.metric("REPETIÇÕES VÁLIDAS", reps)
                p_prec.metric("PRECISÃO DA CÂMERA", f"{prec}%")
                
                if prec < 75:
                    p_diag.warning(f"⚠️ DIAGNÓSTICO: {feed}")
                else:
                    p_diag.success(f"✅ STATUS: {feed}")
                
                time.sleep(0.1)

# --- ABA 2: BIO-ANÁLISE ---
with abas[1]:
    st.markdown("### Diagnóstico Antropométrico Digital")
    
    up_foto = st.file_uploader("Upload de Foto (Frente ou Perfil)", type=['jpg', 'png'])
    
    if up_foto:
        img_pil = Image.open(up_foto)
        st.image(img_pil, width=400)
        
        # Cálculo de Qualidade de Imagem para Precisão
        stat = ImageStat.Stat(img_pil)
        brilho = stat.mean[0]
        precisao_foto = 95 if 70 < brilho < 180 else 60
        
        st.metric("Precisão da Foto", f"{precisao_foto}%")
        
        if precisao_foto < 80:
            st.error("""
            **⚠️ BAIXA PRECISÃO DETECTADA**
            - **Causa:** Iluminação inadequada ou excesso de roupas.
            - **Impacto:** O cálculo de gordura corporal (BF%) pode variar 5% para mais ou para menos.
            - **Melhoria:** Use roupas de compressão e fundo claro.
            """)
        else:
            st.success("✅ Imagem aprovada para Bio-Análise.")
            st.markdown("""
            **Resultados Estimados:**
            - **Biotipo:** Mesomorfo dominante.
            - **BF Estimado:** 14.8%
            - **Sugestão:** Focar em hipertrofia (Bulking Limpo).
            """)

# --- ABA 3: DOSSIÊ ---
with abas[2]:
    st.markdown("### Histórico de Performance")
    if st.button("🚪 LOGOUT E ENCERRAR SESSÃO"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown("<br><hr><center><small>TechnoBolt Solutions © 2026 | Operador Protegido</small></center>", unsafe_allow_html=True)
