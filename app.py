import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import time
import os
import re
import json
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TechnoBolt Gym Hub", layout="wide", page_icon="🏋️")

# --- DESIGN SYSTEM TECHNOBOLT (BLINDAGEM TOTAL) ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
    
    /* FIX DEFINITIVO DA SETA */
    [data-testid="stSidebarCollapseButton"] { color: transparent !important; font-size: 0px !important; }
    [data-testid="stSidebarCollapseButton"] span { display: none !important; }
    [data-testid="stSidebarCollapseButton"] svg { fill: #3b82f6 !important; visibility: visible !important; width: 28px !important; height: 28px !important; }

    .result-card-unificado { 
        background-color: #0a0a0a !important; 
        border-left: 6px solid #3b82f6;
        border-radius: 15px;
        padding: 25px;
        margin-top: 15px;
        border: 1px solid #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

# --- SISTEMA DE PERSISTÊNCIA (JSON) ---
DB_FILE = "technobolt_data.json"

def carregar_dados():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def salvar_analise(usuario, r1, r2, r3, r4, engine):
    dados = carregar_dados()
    dados[usuario] = {
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "r1": r1, "r2": r2, "r3": r3, "r4": r4, "engine": engine
    }
    with open(DB_FILE, "w") as f: json.dump(dados, f, indent=4)

# --- MOTOR DE PDF PROFISSIONAL ---
# --- CLASSE PDF DE ALTA PERFORMANCE (VISUAL MODERNO) ---
class TechnoBoltPDF(FPDF):
    def header(self):
        # Cabeçalho com Barra Lateral Azul
        self.set_fill_color(10, 10, 10)  # Fundo Quase Preto
        self.rect(0, 0, 210, 45, 'F')
        
        # Logo Texto
        self.set_xy(10, 15)
        self.set_font("Helvetica", "B", 26)
        self.set_text_color(59, 130, 246) # Azul TechnoBolt
        self.cell(0, 10, "TECHNOBOLT GYM", ln=True, align="L")
        
        # Subtítulo
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(200, 200, 200)
        self.cell(0, 5, "INTELECTO ARTIFICIAL APLICADO À PERFORMANCE HUMANA", ln=True, align="L")
        
        # Linha decorativa
        self.set_draw_color(59, 130, 246)
        self.set_line_width(1)
        self.line(10, 38, 200, 38)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Página {self.page_no()} | Laudo Tecnológico TechnoBolt v7.5 | 2026", align="C")

def gerar_pdf_elite(nome, conteudo, titulo, data_analise):
    pdf = TechnoBoltPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Caixa de Identificação do Atleta
    pdf.set_fill_color(240, 245, 255)
    pdf.set_draw_color(59, 130, 246)
    pdf.rect(10, 50, 190, 20, 'FD')
    
    pdf.set_xy(15, 52)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 8, f"ATLETA: {nome.upper()}")
    pdf.cell(0, 8, f"DATA DA ANÁLISE: {data_analise}", ln=True, align="R")
    
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(59, 130, 246)
    pdf.cell(0, 8, f"RELATÓRIO ESPECÍFICO: {titulo.upper()}")
    
    pdf.ln(25) # Espaço para o conteúdo

    # Estilização do Conteúdo
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "", 11)
    
    # Limpeza e Formatação do texto vindo da IA
    texto = conteudo.replace('**', '').replace('###', '').replace('##', '').replace('#', '')
    texto = texto.replace('*', '  • ') # Melhora o visual de tópicos
    
    # Renderização com espaçamento moderno
    pdf.multi_cell(0, 8, texto.encode('latin-1', 'replace').decode('latin-1'))
    
    # Selo Final
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(180, 180, 180)
    pdf.cell(0, 10, "-" * 50, ln=True, align="C")
    pdf.cell(0, 5, "DOCUMENTO ASSINADO DIGITALMENTE POR TECHNOBOLT CORE AI", align="C")
    
    return pdf.output(dest='S')


def gerar_pdf_elite(nome, conteudo, titulo, data_analise):
    pdf = TechnoBoltPDF()
    pdf.add_page(); pdf.ln(15)
    pdf.set_text_color(0,0,0); pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"{titulo.upper()} - {nome}", ln=True)
    pdf.set_font("Helvetica", "I", 10); pdf.cell(0, 5, f"Relatório gerado em: {data_analise}", ln=True)
    pdf.ln(10); pdf.set_font("Helvetica", "", 11)
    texto = conteudo.replace('**', '').replace('###', '').replace('*', '-')
    pdf.multi_cell(0, 7, texto.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S')

# --- MOTOR DE IA (PENTACAMADA) ---
def realizar_scan_phd(prompt_mestre, img_pil):
    img_byte_arr = io.BytesIO()
    img_pil.save(img_byte_arr, format='JPEG')
    img_blob = {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}
    
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") or st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    motores = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-2.0-flash-lite", "models/gemini-flash-latest"]

    for idx, key in enumerate(chaves):
        try:
            genai.configure(api_key=key)
            for m in motores:
                try:
                    model = genai.GenerativeModel(m)
                    response = model.generate_content([prompt_mestre, img_blob])
                    return response.text, f"CONTA {idx+1} - {m.upper()}"
                except: continue
        except: continue
    return None, "OFFLINE"

# --- LOGIN ---
USUARIOS_DB = {
    "admin": "admin123", "pedro.santana": "senha", "luiza.trovao": "senha",
    "anderson.bezerra": "senha", "fabricio.felix": "senha", "jackson.antonio": "senha",
    "italo.trovao": "senha", "julia.fernanda": "senha", "convidado": "senha"
}
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("TechnoBolt Gym")
    u = st.text_input("Usuário"); p = st.text_input("Senha", type="password")
    if st.button("AUTENTICAR"):
        if u in USUARIOS_DB and USUARIOS_DB[u] == p:
            st.session_state.logado = True; st.session_state.user_atual = u; st.rerun()
    st.stop()

# --- SIDEBAR ---
dados_salvos = carregar_dados()
user = st.session_state.user_atual

with st.sidebar:
    st.header(f"Olá, {user.split('.')[0].capitalize()}")
    if st.button("SAIR"): st.session_state.logado = False; st.rerun()
    st.divider()
    nome_perfil = st.text_input("Nome", value=user.capitalize())
    idade = st.number_input("Idade", 12, 90, 25)
    altura = st.number_input("Altura (cm)", 100, 250, 175)
    peso = st.number_input("Peso (kg)", 30.0, 250.0, 80.0)
    objetivo = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    up = st.file_uploader("📸 Nova Foto (Atualizar Análise)", type=['jpg', 'jpeg', 'png'])

# --- PROCESSAMENTO ---
if up and nome_perfil:
    img_raw = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
    img_raw.thumbnail((600, 600))
    imc = peso / ((altura/100)**2)
    
    if st.button("🚀 INICIAR ESCANEAMENTO PHD"):
        with st.status("🧬 PROCESSANDO PROTOCOLO TECHNOBOLT..."):
            # --- PROMPT MESTRE COM TODAS AS ESPECIALIDADES RESTAURADAS ---
            prompt = f"""
            VOCÊ É UM CONSELHO DE ESPECIALISTAS PHD DA TECHNOBOLT GYM. 
            ANÁLISE PARA: {nome_perfil} | OBJETIVO: {objetivo} | IMC: {imc:.2f}

            FORNEÇA 4 RELATÓRIOS TÉCNICOS SEPARADOS POR '[DIVISOR]':

            1. AVALIAÇÃO ANTROPOMÉTRICA: PhD em Antropometria formado com: Certificação Internacional ISAK (Níveis 1 a 4), Cineantropometria Avançada, Ultrassonografia, Bioimpedância Tetrapolar, Especialização em Bioestatística, Padronização de Medidas, Interpretação de DXA e Crescimento Humano. Determine Biotipo, BF% e Postura.
            
            2. PLANEJAMENTO NUTRICIONAL: Nutricionista PhD formado com: Pós-graduação em Nutrição Esportiva, Clínica e Funcional, Fitoterapia, Bioquímica do Metabolismo, Gastronomia Funcional, Nutrigenética e Planejamento Dietético Avançado. Determine GET, Macros e Plano Alimentar.

            3. PROTOCOLO DE SUPLEMENTAÇÃO: Especialista PhD em Suplementação Esportiva, Farmacologia do Exercício, Bioquímica Aplicada, Fitoterapia na Performance e Mecanismos Moleculares. Indique 3 a 10 suplementos via Nexo Metabólico.

            4. PRESCRIÇÃO DE TREINO: Personal Trainer PhD em Biomecânica e Cinesiologia, Fisiologia do Exercício, Metodologia de Periodização, Musculação Avançada, LPO e HIIT. 
               PRESCREVA TREINO DE 7 DIAS. MAXIMIZE RESULTADOS: 8 a 10 exercícios por dia. 
               PARA CADA EXERCÍCIO INCLUA: Nome, Séries, Repetições e a JUSTIFICATIVA BIOMECÂNICA DETALHADA.

            REGRAS: Use tópicos curtos. Proibido saudações. Use linguagem de elite.
            """
            res, eng = realizar_scan_phd(prompt, img_raw)
            if res:
                partes = res.split('[DIVISOR]')
                salvar_analise(user, partes[0], partes[1], partes[2], partes[3], eng)
                st.rerun()

# --- EXIBIÇÃO ---
if user in dados_salvos:
    d = dados_salvos[user]
    st.info(f"📅 Última análise realizada em: {d['data']}")
    tabs = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino", "📜 Dossiê"])
    
    for i, titulo in enumerate(["Avaliação", "Nutrição", "Suplementos", "Treino"]):
        conteudo = d[f"r{i+1}"]
        with tabs[i]:
            st.markdown(f"<div class='result-card-unificado'>{conteudo}</div>", unsafe_allow_html=True)
            st.download_button(f"📥 Baixar {titulo}", data=gerar_pdf_elite(nome_perfil, conteudo, titulo, d['data']), file_name=f"{titulo}_TechnoBolt.pdf")
    
    with tabs[4]:
        completo = f"{d['r1']}\n{d['r2']}\n{d['r3']}\n{d['r4']}"
        st.markdown(f"<div class='result-card-unificado'>{completo}</div>", unsafe_allow_html=True)
        st.download_button("📥 BAIXAR DOSSIÊ COMPLETO", data=gerar_pdf_elite(nome_perfil, completo, "Dossiê Completo", d['data']), file_name="Dossie_TechnoBolt.pdf")
else:
    st.markdown("<div class='result-card-unificado' style='text-align:center;'>Aguardando Upload para Primeira Análise</div>", unsafe_allow_html=True)
