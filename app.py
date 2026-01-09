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

# --- DESIGN SYSTEM TECHNOBOLT (BLACK & GRAY ELITE) ---
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #000000 !important;
    }
    html, body, [class*="st-"] { color: #ffffff !important; font-family: 'Inter', sans-serif; }
    
    /* Botões de Ação */
    .stButton > button, .stDownloadButton > button {
        background-color: #333333 !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
        border-radius: 12px !important;
        min-height: 55px !important;
        width: 100% !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: 0.4s;
    }
    .stButton > button:hover { background-color: #3b82f6 !important; border-color: #3b82f6 !important; transform: translateY(-2px); }

    /* Inputs e Selects */
    input, div[data-baseweb="select"] > div, [data-testid="stFileUploader"] {
        background-color: #111111 !important;
        color: white !important;
        border: 1px solid #222 !important;
        border-radius: 10px !important;
    }

    /* Cards de Resultado */
    .result-card-unificado { 
        background-color: #0a0a0a !important; 
        border: 1px solid #1a1a1a;
        border-left: 6px solid #3b82f6;
        border-radius: 15px;
        padding: 30px;
        line-height: 1.8;
        font-size: 15px;
        box-shadow: 0 15px 40px rgba(0,0,0,0.8);
    }
    
    .stTabs [aria-selected="true"] { background-color: #111 !important; color: #3b82f6 !important; border-bottom: 2px solid #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)

# --- SISTEMA DE LIMPEZA DE TEXTO (IMPECÁVEL) ---
def limpar_texto(texto):
    # Remove hashtags, asteriscos duplos e outros símbolos de markdown
    texto = texto.replace('**', '').replace('###', '').replace('##', '').replace('#', '')
    texto = texto.replace('*', '•') # Transforma asteriscos em bullets elegantes
    texto = re.sub(r'\n\s*\n', '\n', texto) # Remove linhas em branco excessivas
    return texto.strip()

# --- CLASSE PDF PROFISSIONAL ---
class TechnoBoltPDF(FPDF):
    def header(self):
        self.set_fill_color(0, 0, 0)
        self.rect(0, 0, 210, 35, 'F')
        self.set_text_color(59, 130, 246)
        self.set_font("Helvetica", "B", 22)
        self.cell(0, 15, "TECHNOBOLT GYM", ln=True, align="C")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, "INTELECTO ARTIFICIAL APLICADO À PERFORMANCE HUMANA", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Página {self.page_no()} | Laudo Oficial TechnoBolt v3.0 | 2026", align="C")

def gerar_pdf_elite(nome, idade, altura, peso, imc, objetivo, conteudo, titulo):
    pdf = TechnoBoltPDF()
    pdf.add_page()
    
    # Bloco de Dados do Atleta
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"  DOSSIÊ TÉCNICO: {titulo.upper()}", ln=True, fill=True)
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, f"ATLETA: {nome.upper()}", ln=True)
    pdf.cell(0, 7, f"IDADE: {idade} anos | ESTATURA: {altura}cm | PESO: {peso}kg", ln=True)
    pdf.cell(0, 7, f"IMC: {imc:.2f} | OBJETIVO: {objetivo.upper()}", ln=True)
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    # Conteúdo Principal
    pdf.set_font("Helvetica", "", 11)
    texto_limpo = limpar_texto(conteudo)
    pdf.multi_cell(0, 7, texto_limpo.encode('latin-1', 'replace').decode('latin-1'))
    
    return pdf.output(dest='S')

# --- LÓGICA DE USUÁRIOS E LOGIN ---
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
        else: st.error("Acesso Negado.")
    st.stop()

# --- SIDEBAR E CAMPOS ---
with st.sidebar:
    st.header(f"Olá, {st.session_state.user_atual.split('.')[0].capitalize()}")
    if st.button("SAIR"): st.session_state.logado = False; st.rerun()
    st.divider()
    nome_perfil = st.text_input("Nome Completo", value=st.session_state.user_atual.capitalize())
    idade = st.number_input("Idade", 12, 90, 25)
    altura = st.number_input("Altura (cm)", 100, 250, 175)
    peso = st.number_input("Peso (kg)", 30.0, 250.0, 80.0)
    objetivo = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    up = st.file_uploader("📸 Foto para Análise", type=['jpg', 'jpeg', 'png'])

# --- MOTOR DE RODÍZIO 7 CHAVES ---
def processar_elite(prompt, img):
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") or st.secrets.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    
    motores = ["models/gemini-3-flash-preview", 
        "models/gemini-2.5-flash", 
        "models/gemini-2.0-flash", 
        "models/gemini-2.0-flash-lite", 
        "models/gemini-flash-latest"]

    for idx, key in enumerate(chaves):
        try:
            genai.configure(api_key=key)
            for m in motores:
                try:
                    model = genai.GenerativeModel(m)
                    # Configuração para resposta limpa
                    response = model.generate_content([prompt, img])
                    return limpar_texto(response.text), f"CONTA {idx+1} - {m.upper()}"
                except Exception as e:
                    if "429" in str(e): break
                    continue
        except: continue
    return "Erro Crítico: Todas as contas atingiram o limite.", "OFFLINE"

# --- PROCESSAMENTO ---
if up and nome_perfil:
    try:
        img_raw = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
        img_raw.thumbnail((600, 600))
        imc = peso / ((altura/100)**2)

        with st.empty():
            st.markdown("""<div style='text-align:center;'><h2 style='color:#3b82f6;'>ANALISANDO BIOMETRIA...</h2></div>""", unsafe_allow_html=True)
            
            # Prompts com instrução de formatação impecável
            p_base = "RETORNE APENAS DADOS TÉCNICOS. PROIBIDO SAUDAÇÕES OU MARCAÇÕES ##. Use tópicos curtos."
            
            r1, e1 = processar_elite(f"{p_base} Aja como PhD em Antropometria formado e que faz uso dos seguintes cursos: Certificação Internacional ISAK (Níveis 1 a 4), Curso de Cineantropometria Avançada, Avaliação da Composição Corporal por Ultrassonografia, Bioimpedância Tetrapolar e Clínica, Anatomia Palpatória e Funcional, Especialização em Bioestatística Aplicada à Saúde, Avaliação Antropométrica de Populações Especiais, Ergonomia e Biometria, Padronização de Medidas Antropométricas, Interpretação de DXA e Tomografia para Composição Corporal, Crescimento e Desenvolvimento Humano para entregar um serviço de qualidade. Analise {nome_perfil}, {idade}a, IMC {imc:.2f}. Determine Biotipo, BF% e Postura. Traduza termos técnicos.", img_raw)
            time.sleep(2)
            r2, e2 = processar_elite(f"{p_base} Aja como Nutricionista PhD que é formado e faz uso dos seguintes cursos: Pós-graduação em Nutrição Esportiva, Especialização em Nutrição Clínica e Funcional, Curso de Interpretação de Exames Laboratoriais, Fitoterapia Aplicada à Nutrição, Nutrição no Emagrecimento e Hipertrofia, Bioquímica do Metabolismo, Nutrição Comportamental, Gastronomia Funcional, Nutrigenética e Nutrigenômica, Planejamento Dietético Avançado e Cálculo de Dietas, Nutrição nas Patologias Metabólicas, Estratégias Nutricionais para Endurance, para compor as dietas. Objetivo {objetivo}. Determine GET, Macros e Plano Alimentar p/ biotipo.", img_raw)
            time.sleep(2)
            r3, e3 = processar_elite(f"{p_base} Especialista em Suplementação que é formado e faz uso dos seguintes cursos: Especialização em Suplementação Esportiva e Recursos Ergogênicos, Farmacologia do Exercício, Bioquímica Aplicada à Suplementação, Curso de Fitoterapia na Performance, Suplementação para Grupos Especiais (Idosos e Atletas de Elite), Atualização em Proteínas e Aminoácidos, Nutrologia Esportiva, Farmácia Clínica voltada ao Esporte, Mecanismos Moleculares da Suplementação, Atualização em Vitaminas e Minerais Quelatados, para propor a suplementação de seus clientes. Indique de 3 a 10 suplementos que considere necessário. Caso considere menos que os 10 suplementos, indique o que achar util para o aluno p/ {objetivo}. Justifique via Nexo Metabólico.", img_raw)
            time.sleep(2)
            r4, e4 = processar_elite(f"{p_base} Personal Trainer PhD, formado e que faz uso dos seguintes cursos:Pós-graduação em Biomecânica e Cinesiologia Aplicada, Especialização em Fisiologia do Exercício, Metodologia da Preparação Física e Periodização, Musculação e Treinamento de Força Avançado, Treinamento Funcional, Reabilitação de Lesões e Traumatologia Esportiva, Prescrição de Exercícios para Grupos Especiais (Idosos, Gestantes e Patologias), Avaliação Física e Antropometria, Nutrição Esportiva aplicada ao Treinamento, Treinamento de Alta Performance, Curso de Levantamento de Peso Olímpico (LPO), Treinamento Intervalado de Alta Intensidade (HIIT), Cinesiologia da Musculação ao montar os treinos. Treino 7 dias p/ {objetivo}. Inclua justificativa biomecânica e substitutos.", img_raw)
            st.empty()

        tabs = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino", "📜 Dossiê"])

        def display_card(res, eng, titulo):
            st.markdown(f"<div class='result-card-unificado'><small style='color:#3b82f6;'>{eng}</small><br><strong>{titulo}</strong><br><br>{res}</div>", unsafe_allow_html=True)
            st.download_button(f"📥 Baixar {titulo}", data=gerar_pdf_elite(nome_perfil, idade, altura, peso, imc, objetivo, res, titulo), file_name=f"{titulo}.pdf")

        with tabs[0]: display_card(r1, e1, "Avaliação Corporal")
        with tabs[1]: display_card(r2, e2, "Planejamento Nutricional")
        with tabs[2]: display_card(r3, e3, "Protocolo de Suplementação")
        with tabs[3]: display_card(r4, e4, "Prescrição de Treinamento")
        
        with tabs[4]:
            dossie_completo = f"AVALIAÇÃO:\n{r1}\n\nNUTRIÇÃO:\n{r2}\n\nSUPLEMENTAÇÃO:\n{r3}\n\nTREINO:\n{r4}"
            st.markdown(f"<div class='result-card-unificado'><strong>DOSSIÊ UNIFICADO TECHNOBOLT</strong><br><br>{dossie_completo}</div>", unsafe_allow_html=True)
            st.download_button("📥 BAIXAR RELATÓRIO COMPLETO (PDF)", data=gerar_pdf_elite(nome_perfil, idade, altura, peso, imc, objetivo, dossie_completo, "Dossiê Completo"), file_name=f"Dossie_{nome_perfil}.pdf")

    except Exception as e: st.error(f"Erro no processamento: {e}")
