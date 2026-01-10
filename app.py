import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import time
import os
import gc
from fpdf import FPDF
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TechnoBolt Gym Hub", layout="wide", page_icon="🏋️")

# --- DESIGN SYSTEM TECHNOBOLT (BLINDAGEM TOTAL ANTI-ERRO) ---
st.markdown("""
<style>
    /* 1. FUNDO E FONTES */
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; color: #ffffff !important; }

    /* 2. FIX DEFINITIVO DA SETA (OCULTA O TEXTO "KEYBOARD_DOUBLE...") */
    [data-testid="stSidebarCollapseButton"] {
        color: transparent !important;
        font-size: 0px !important;
        background-color: transparent !important;
        border: none !important;
    }
    [data-testid="stSidebarCollapseButton"] span {
        display: none !important; 
    }
    [data-testid="stSidebarCollapseButton"] svg {
        fill: #3b82f6 !important;
        visibility: visible !important;
        width: 28px !important;
        height: 28px !important;
    }

    /* 3. BOTÕES E CARDS */
    .stButton > button, .stDownloadButton > button {
        background-color: #333333 !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
        border-radius: 12px !important;
        min-height: 50px !important;
        width: 100% !important;
        font-weight: 700 !important;
        text-transform: uppercase;
    }
    
    .result-card-unificado { 
        background-color: #0a0a0a !important; 
        border-left: 6px solid #3b82f6;
        border-radius: 15px;
        padding: 25px;
        margin-top: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.8);
    }
</style>
""", unsafe_allow_html=True)

# --- LIMPEZA DE TEXTO PARA PDF ---
def limpar_texto(texto):
    texto = texto.replace('**', '').replace('###', '').replace('##', '').replace('#', '')
    texto = texto.replace('*', '•')
    texto = re.sub(r'\n\s*\n', '\n', texto)
    return texto.strip()

# --- GERAÇÃO DE PDF PROFISSIONAL ---
class TechnoBoltPDF(FPDF):
    def header(self):
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, 210, 35, 'F')
        self.set_text_color(59, 130, 246)
        self.set_font("Helvetica", "B", 22)
        self.cell(0, 15, "TECHNOBOLT GYM", ln=True, align="C")
        self.ln(10)

def gerar_pdf_elite(nome, idade, altura, peso, imc, objetivo, conteudo, titulo):
    pdf = TechnoBoltPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"  DOSSIÊ TÉCNICO: {titulo.upper()}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 11)
    texto_limpo = limpar_texto(conteudo)
    pdf.multi_cell(0, 7, texto_limpo.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S')

# --- SISTEMA DE LOGIN ---
USUARIOS_DB = {
    "admin": "admin123", "pedro.santana": "senha", "luiza.trovao": "senha",
    "anderson.bezerra": "senha", "fabricio.felix": "senha", "jackson.antonio": "senha",
    "italo.trovao": "senha", "julia.fernanda": "senha", "convidado": "senha"
}
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("TechnoBolt Gym")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("AUTENTICAR"):
        if u in USUARIOS_DB and USUARIOS_DB[u] == p:
            st.session_state.logado = True
            st.session_state.user_atual = u
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.header(f"Olá, {st.session_state.user_atual.capitalize()}")
    if st.button("SAIR"): st.session_state.logado = False; st.rerun()
    st.divider()
    nome_perfil = st.text_input("Nome Completo", value=st.session_state.user_atual.capitalize())
    idade = st.number_input("Idade", 12, 90, 25)
    altura = st.number_input("Altura (cm)", 100, 250, 175)
    peso = st.number_input("Peso (kg)", 30.0, 250.0, 80.0)
    objetivo = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    up = st.file_uploader("📸 Foto para Análise", type=['jpg', 'jpeg', 'png'])

# --- MOTOR PENTACAMADA COM TRATAMENTO "BLOB" (CORRIGE BYTEARRAY) ---
def processar_elite(prompt, img_pil):
    # Converte PIL para bytes estruturados (Blob) para evitar erro de classe binária
    img_byte_arr = io.BytesIO()
    img_pil.save(img_byte_arr, format='JPEG')
    img_blob = {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}

    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") or st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    
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
                    response = model.generate_content([prompt, img_blob])
                    return limpar_texto(response.text), f"CONTA {idx+1} - {m.upper()}"
                except Exception as e:
                    if "429" in str(e): break
                    continue
        except: continue
    return "Erro Crítico: Todas as contas atingiram o limite.", "OFFLINE"

# --- FLUXO DE PROCESSAMENTO ---
if up and nome_perfil:
    try:
        img_raw = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        img_raw.thumbnail((600, 600))
        # Cálculo de IMC para o laudo: $IMC = \frac{peso}{altura^2}$
        imc = peso / ((altura/100)**2)

        with st.empty():
            st.markdown(f"""
                <div style="text-align:center; padding:40px; background: rgba(10, 10, 10, 0.95); border-radius:20px; border: 2px solid #3b82f6;">
                    <img src="https://i.gifer.com/Y1y6.gif" width="280" style="border-radius:15px; margin-bottom:25px;">
                    <h2 style="color:#3b82f6; letter-spacing: 4px; font-weight: 800;">ESCANEANDO BIOMETRIA...</h2>
                </div>
            """, unsafe_allow_html=True)
            
            p_base = "RETORNE APENAS DADOS TÉCNICOS. PROIBIDO SAUDAÇÕES OU MARCAÇÕES ##. Use tópicos curtos."
            
            # --- SEUS PROMPTS ORIGINAIS RESTAURADOS INTEGRALMENTE ---
            
            # 1. ANTROPOMETRIA
            r1, e1 = processar_elite(f"{p_base} Aja como PhD em Antropometria formado e que faz uso dos seguintes cursos: Certificação Internacional ISAK (Níveis 1 a 4), Curso de Cineantropometria Avançada, Avaliação da Composição Corporal por Ultrassonografia, Bioimpedância Tetrapolar e Clínica, Anatomia Palpatória e Funcional, Especialização em Bioestatística Aplicada à Saúde, Avaliação Antropométrica de Populações Especiais, Ergonomia e Biometria, Padronização de Medidas Antropométricas, Interpretação de DXA e Tomografia para Composição Corporal, Crescimento e Desenvolvimento Humano para entregar um serviço de qualidade. Analise {nome_perfil}, {idade}a, IMC {imc:.2f}. Determine Biotipo, BF% e Postura. Traduza termos técnicos.", img_raw)
            time.sleep(2)
            
            # 2. NUTRIÇÃO
            r2, e2 = processar_elite(f"{p_base} Aja como Nutricionista PhD que é formado e faz uso dos seguintes cursos: Pós-graduação em Nutrição Esportiva, Especialização em Nutrição Clínica e Funcional, Curso de Interpretação de Exames Laboratoriais, Fitoterapia Aplicada à Nutrição, Nutrição no Emagrecimento e Hipertrofia, Bioquímica do Metabolismo, Nutrição Comportamental, Gastronomia Funcional, Nutrigenética e Nutrigenômica, Planejamento Dietético Avançado e Cálculo de Dietas, Nutrição nas Patologias Metabólicas, Estratégias Nutricionais para Endurance, para compor as dietas. Objetivo {objetivo}. Determine GET, Macros e Plano Alimentar p/ biotipo.", img_raw)
            time.sleep(2)
            
            # 3. SUPLEMENTAÇÃO
            r3, e3 = processar_elite(f"{p_base} Especialista em Suplementação que é formado e faz uso dos seguintes cursos: Especialização em Suplementação Esportiva e Recursos Ergogênicos, Farmacologia do Exercício, Bioquímica Aplicada à Suplementação, Curso de Fitoterapia na Performance, Suplementação para Grupos Especiais (Idosos e Atletas de Elite), Atualização em Proteínas e Aminoácidos, Nutrologia Esportiva, Farmácia Clínica voltada ao Esporte, Mecanismos Moleculares da Suplementação, Atualização em Vitaminas e Minerais Quelatados, para propor a suplementação de seus clientes. Indique de 3 a 10 suplementos que considere necessário. Caso considere menos que os 10 suplementos, indique o que achar util para o aluno p/ {objetivo}. Justifique via Nexo Metabólico.", img_raw)
            time.sleep(2)
            
            # 4. TREINO
            r4, e4 = processar_elite(f"{p_base} Personal Trainer PhD, formado e que faz uso dos seguintes cursos:Pós-graduação em Biomecânica e Cinesiologia Aplicada, Especialização em Fisiologia do Exercício, Metodologia da Preparação Física e Periodização, Musculação e Treinamento de Força Avançado, Treinamento Funcional, Reabilitação de Lesões e Traumatologia Esportiva, Prescrição de Exercícios para Grupos Especiais (Idosos, Gestantes e Patologias), Avaliação Física e Antropometria, Nutrição Esportiva aplicada ao Treinamento, Treinamento de Alta Performance, Curso de Levantamento de Peso Olímpico (LPO), Treinamento Intervalado de Alta Intensidade (HIIT), Cinesiologia da Musculação ao montar os treinos. Treino 7 dias p/ {objetivo}. Inclua justificativa biomecânica e substitutos.", img_raw)
            st.empty()

        tabs = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino", "📜 Dossiê"])
        
        def render_tab(res, eng, titulo):
            st.markdown(f"<div class='result-card-unificado'><small style='color:#3b82f6;'>{eng}</small><br><strong>{titulo}</strong><br><br>{res}</div>", unsafe_allow_html=True)
            st.download_button(f"📥 Baixar {titulo}", data=gerar_pdf_elite(nome_perfil, idade, altura, peso, imc, objetivo, res, titulo), file_name=f"{titulo}.pdf")

        with tabs[0]: render_tab(r1, e1, "Avaliação Corporal")
        with tabs[1]: render_tab(r2, e2, "Planejamento Nutricional")
        with tabs[2]: render_tab(r3, e3, "Protocolo de Suplementação")
        with tabs[3]: render_tab(r4, e4, "Prescrição de Treinamento")
        with tabs[4]:
            dossie = f"AVALIAÇÃO:\n{r1}\n\nNUTRIÇÃO:\n{r2}\n\nSUPLEMENTAÇÃO:\n{r3}\n\nTREINO:\n{r4}"
            st.markdown(f"<div class='result-card-unificado'>{dossie}</div>", unsafe_allow_html=True)
            st.download_button("📥 BAIXAR DOSSIÊ", data=gerar_pdf_elite(nome_perfil, idade, altura, peso, imc, objetivo, dossie, "Dossiê"), file_name="Dossie.pdf")

    except Exception as e: st.error(f"Erro Crítico: {e}")

else:
    # --- TELA INICIAL (RESTAURADA) ---
    st.markdown("""
        <div class="result-card-unificado" style="text-align:center;">
            <div style="font-size: 50px; margin-bottom: 20px;">👤</div>
            <h2 style="color:#3b82f6; letter-spacing: 2px;">TECHNOBOLT GYM HUB</h2>
            <p style="color:#888; font-size:16px;">Aguardando entrada de dados na barra lateral...</p>
        </div>
    """, unsafe_allow_html=True)
