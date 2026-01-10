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

# --- DESIGN SYSTEM TECHNOBOLT ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
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

def sanitizar_texto_pdf(texto):
    texto = texto.replace('**', '').replace('###', '').replace('##', '').replace('#', '')
    texto = texto.replace('•', '-').replace('✅', '[OK]').replace('📊', '').replace('🥗', '').replace('💊', '').replace('🏋️', '')
    texto = texto.replace('|', ' ').replace('--|--', ' ').replace('---', '')
    return texto

# --- CLASSE PDF ---
class TechnoBoltPDF(FPDF):
    def header(self):
        self.set_fill_color(10, 10, 10); self.rect(0, 0, 210, 45, 'F')
        self.set_xy(10, 15); self.set_font("Helvetica", "B", 26)
        self.set_text_color(59, 130, 246); self.cell(0, 10, "TECHNOBOLT GYM", ln=True, align="L")
        self.set_font("Helvetica", "I", 9); self.set_text_color(200, 200, 200)
        self.cell(0, 5, "INTELECTO ARTIFICIAL APLICADO À PERFORMANCE HUMANA", ln=True, align="L")
        self.set_draw_color(59, 130, 246); self.set_line_width(1); self.line(10, 38, 200, 38); self.ln(20)

    def footer(self):
        self.set_y(-15); self.set_font("Helvetica", "I", 8); self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Página {self.page_no()} | Laudo Tecnológico TechnoBolt | 2026", align="C")

def gerar_pdf_elite(nome, conteudo, titulo, data_analise):
    pdf = TechnoBoltPDF()
    pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    pdf.set_fill_color(240, 245, 255); pdf.set_draw_color(59, 130, 246); pdf.rect(10, 50, 190, 20, 'FD')
    pdf.set_xy(15, 52); pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 8, f"ATLETA: {nome.upper()} body"); pdf.cell(0, 8, f"DATA: {data_analise}", ln=True, align="R")
    pdf.ln(25); pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(59, 130, 246)
    pdf.cell(0, 10, titulo.upper(), ln=True); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    pdf.set_text_color(40, 40, 40); pdf.set_font("Helvetica", "", 10)
    texto_limpo = sanitizar_texto_pdf(conteudo)
    pdf.multi_cell(0, 7, texto_limpo.encode('latin-1', 'replace').decode('latin-1'))
    pdf_output = pdf.output(dest='S')
    return bytes(pdf_output) if not isinstance(pdf_output, str) else bytes(pdf_output, 'latin-1')

# --- MOTOR DE IA (PENTACAMADA) ---
def realizar_scan_phd(prompt_mestre, img_pil):
    img_byte_arr = io.BytesIO(); img_pil.save(img_byte_arr, format='JPEG')
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
USUARIOS_DB = {"admin": "admin123", "pedro.santana": "senha", "luiza.trovao": "senha", "anderson.bezerra": "senha", "fabricio.felix": "senha", "jackson.antonio": "senha", "italo.trovao": "senha", "julia.fernanda": "senha", "convidado": "senha", "patricie.medova": "senha", "teia.araujo": "senha"}
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    st.title("TechnoBolt Gym"); u = st.text_input("Usuário"); p = st.text_input("Senha", type="password")
    if st.button("AUTENTICAR"):
        if u in USUARIOS_DB and USUARIOS_DB[u] == p: st.session_state.logado = True; st.session_state.user_atual = u; st.rerun()
    st.stop()

# --- SIDEBAR ---
dados_salvos = carregar_dados(); user = st.session_state.user_atual
with st.sidebar:
    st.header(f"Olá, {user.split('.')[0].capitalize()}")
    if st.button("SAIR"): st.session_state.logado = False; st.rerun()
    st.divider()
    if user in dados_salvos: st.success(f"Análise salva: {dados_salvos[user]['data']}")
    nome_perfil = st.text_input("Nome", value=user.capitalize())
    idade = st.number_input("Idade", 12, 90, 25); altura = st.number_input("Altura (cm)", 100, 250, 175); peso = st.number_input("Peso (kg)", 30.0, 250.0, 80.0)
    objetivo = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    up = st.file_uploader("📸 Foto (Scanner)", type=['jpg', 'jpeg', 'png'])

# --- PROCESSAMENTO ---
if up and nome_perfil:
    img_raw = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
    img_raw.thumbnail((600, 600)); imc = peso / ((altura/100)**2)
    if st.button("🚀 INICIAR ESCANEAMENTO PHD"):
        with st.status("🧬 PROCESSANDO PROTOCOLO TECHNOBOLT..."):
            prompt = f"""VOCÊ É UM CONSELHO DE ESPECIALISTAS PHD DA TECHNOBOLT GYM. ANÁLISE PARA: {nome_perfil} | OBJETIVO: {objetivo} | IMC: {imc:.2f}
            
            FORNEÇA 4 RELATÓRIOS TÉCNICOS SEPARADOS RIGOROSAMENTE PELA TAG '[DIVISOR]':

            1. AVALIAÇÃO ANTROPOMÉTRICA: Aja como PhD em Antropometria formado com Certificação Internacional ISAK (Níveis 1 a 4), Cineantropometria Avançada, Ultrassonografia, Bioimpedância Tetrapolar, Especialização em Bioestatística, Padronização de Medidas, Interpretação de DXA e Tomografia para Composição Corporal e Crescimento Humano. Determine Biotipo, BF% e Postura.
            
            2. PLANEJAMENTO NUTRICIONAL: Aja como Nutricionista PhD formado com Pós-graduação em Nutrição Esportiva, Clínica e Funcional, Fitoterapia, Bioquímica do Metabolismo, Gastronomia Funcional, Nutrigenética e Planejamento Dietético Avançado. Determine GET, Macros e Plano Alimentar.

            3. PROTOCOLO DE SUPLEMENTAÇÃO: Aja como Especialista PhD em Suplementação Esportiva, Farmacologia do Exercício, Bioquímica Aplicada, Fitoterapia na Performance e Mecanismos Moleculares. Indique de 3 a 10 suplementos via Nexo Metabólico.

            4. PRESCRIÇÃO DE TREINO: Aja como Personal Trainer PhD em Biomecânica e Cinesiologia, Fisiologia do Exercício, Metodologia da Preparação Física, Musculação Avançada, LPO e HIIT. Prescreva treino de 7 dias com 8 a 10 exercícios por dia. 
               ESTRUTURA: NOME DO EXERCÍCIO | SÉRIES | REPETIÇÕES | JUSTIFICATIVA BIOMECÂNICA DETALHADA.
               IMPORTANTE: NÃO USE TABELAS MARKDOWN. Use listas numeradas.
            
            REGRAS: Use tópicos curtos. Proibido saudações. Linguagem de Elite. Coloque a tag '[DIVISOR]' exatamente entre os blocos."""
            
            res, eng = realizar_scan_phd(prompt, img_raw)
            if res:
                partes = res.split('[DIVISOR]')
                # Atribuição rigorosa para garantir ordem correta nas abas
                p1 = partes[0] if len(partes) > 0 else "Erro na Avaliação"
                p2 = partes[1] if len(partes) > 1 else "Erro na Nutrição"
                p3 = partes[2] if len(partes) > 2 else "Erro na Suplementação"
                p4 = partes[3] if len(partes) > 3 else "Erro no Treino"
                salvar_analise(user, p1, p2, p3, p4, eng); st.rerun()

# --- EXIBIÇÃO ---
if user in dados_salvos:
    d = dados_salvos[user]
    tabs = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino", "📜 Dossiê"])
    
    conteudos = [d['r1'], d['r2'], d['r3'], d['r4']]
    titulos = ["Avaliacao", "Nutricao", "Suplementos", "Treino"]
    
    for idx, tab in enumerate(tabs[:4]):
        with tab:
            st.markdown(f"<div class='result-card-unificado'>{conteudos[idx]}</div>", unsafe_allow_html=True)
            pdf_data = gerar_pdf_elite(nome_perfil, conteudos[idx], titulos[idx], d['data'])
            st.download_button(label=f"📥 Baixar PDF {titulos[idx]}", data=pdf_data, file_name=f"{titulos[idx]}_TechnoBolt.pdf", mime="application/pdf", key=f"btn_{idx}")
    
    with tabs[4]:
        completo = f"{d['r1']}\n\n{d['r2']}\n\n{d['r3']}\n\n{d['r4']}"
        st.markdown(f"<div class='result-card-unificado'>{completo}</div>", unsafe_allow_html=True)
        pdf_full = gerar_pdf_elite(nome_perfil, completo, "Dossie Completo", d['data'])
        st.download_button(label="📥 BAIXAR DOSSIÊ COMPLETO", data=pdf_full, file_name="Dossie_TechnoBolt.pdf", mime="application/pdf", key="btn_full")
else:
    st.markdown("<div class='result-card-unificado' style='text-align:center;'>Aguardando Upload para Primeira Análise</div>", unsafe_allow_html=True)
