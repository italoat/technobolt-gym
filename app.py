import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import os
import re
import json
from datetime import datetime
from fpdf import FPDF
from pymongo import MongoClient

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TechnoBolt Gym Hub", layout="wide", page_icon="🏋️")

# --- CONEXÃO MONGODB ATLAS ---
# A URL deve ser configurada no Render (Environment Variables) como MONGO_URL
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://technobolt:tech@132@cluster0.zbjsvk6.mongodb.net/?appName=Cluster0")

@st.cache_resource
def iniciar_conexao():
    client = MongoClient(MONGO_URL)
    return client['TechnoBoltDB']

try:
    db = iniciar_conexao()
except Exception as e:
    st.error(f"Erro de conexão com a nuvem: {e}")
    st.stop()

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

# --- FUNÇÕES DE APOIO ---
def sanitizar_texto_pdf(texto):
    texto = texto.replace('**', '').replace('###', '').replace('##', '').replace('#', '')
    texto = texto.replace('•', '-').replace('✅', '[OK]').replace('📊', '').replace('🥗', '').replace('💊', '').replace('🏋️', '')
    texto = texto.replace('|', ' ').replace('--|--', ' ').replace('---', '')
    return texto

class TechnoBoltPDF(FPDF):
    def header(self):
        self.set_fill_color(10, 10, 10); self.rect(0, 0, 210, 45, 'F')
        self.set_xy(10, 15); self.set_font("Helvetica", "B", 26); self.set_text_color(59, 130, 246)
        self.cell(0, 10, "TECHNOBOLT GYM", ln=True, align="L")
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
    pdf.cell(90, 8, f"ATLETA: {nome.upper()}"); pdf.cell(0, 8, f"DATA: {data_analise}", ln=True, align="R")
    pdf.ln(25); pdf.set_font("Helvetica", "B", 14); pdf.set_text_color(59, 130, 246)
    pdf.cell(0, 10, titulo.upper(), ln=True); pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    pdf.set_text_color(40, 40, 40); pdf.set_font("Helvetica", "", 10)
    texto_limpo = sanitizar_texto_pdf(conteudo)
    pdf.multi_cell(0, 7, texto_limpo.encode('latin-1', 'replace').decode('latin-1'))
    pdf_output = pdf.output(dest='S')
    return bytes(pdf_output) if not isinstance(pdf_output, str) else bytes(pdf_output, 'latin-1')

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

# --- SISTEMA DE AUTENTICAÇÃO E REGISTRO ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("TechnoBolt Gym")
    u = st.text_input("Usuário").lower().strip()
    p = st.text_input("Senha", type="password")
    
    col_login, col_reg = st.columns(2)
    with col_login:
        if st.button("AUTENTICAR"):
            user_data = db.usuarios.find_one({"usuario": u})
            if user_data and user_data['senha'] == p:
                if user_data['status'] == 'pendente':
                    st.warning("⚠️ Conta em análise. Aguarde a liberação do administrador.")
                elif user_data['status'] == 'inativo':
                    st.error("❌ Esta conta foi desativada.")
                else:
                    st.session_state.logado = True
                    st.session_state.user_atual = u
                    st.session_state.is_admin = user_data.get('is_admin', False)
                    st.rerun()
            else: st.error("Usuário ou senha inválidos.")
    with col_reg:
        if st.button("SOLICITAR ACESSO"):
            if u and p:
                if db.usuarios.find_one({"usuario": u}): st.error("Este usuário já existe.")
                else:
                    db.usuarios.insert_one({
                        "usuario": u, "senha": p, "status": "pendente", 
                        "avaliacoes_restantes": 0, "historico_dossies": [], "is_admin": False
                    })
                    st.success("Solicitação enviada! Aguarde a aprovação.")
            else: st.info("Preencha os campos para solicitar acesso.")
    st.stop()

# --- PAINEL ADMINISTRATIVO ---
user_doc = db.usuarios.find_one({"usuario": st.session_state.user_atual})

if st.session_state.is_admin:
    with st.expander("🛠️ PAINEL ADMINISTRATIVO (Gestão de Usuários)"):
        usuarios_lista = list(db.usuarios.find({"usuario": {"$ne": "admin"}}))
        for usr in usuarios_lista:
            c1, c2, c3, c4 = st.columns([2, 2, 1, 2])
            c1.write(f"**{usr['usuario']}**")
            # Controle de Status
            novo_st = c2.selectbox("Status", ["pendente", "ativo", "inativo"], 
                                  index=["pendente", "ativo", "inativo"].index(usr['status']), 
                                  key=f"st_{usr['usuario']}")
            if novo_st != usr['status']:
                db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"status": novo_st}})
                st.rerun()
            
            c3.write(f"🪙 {usr.get('avaliacoes_restantes', 0)}")
            # Renovação de Créditos
            if c4.button("Renovar Ciclo (4)", key=f"ren_{usr['usuario']}"):
                db.usuarios.update_one({"usuario": usr['usuario']}, 
                                      {"$set": {"avaliacoes_restantes": 4, "status": "ativo"}})
                st.rerun()

# --- SIDEBAR E CONFIGURAÇÃO ATUAL ---
with st.sidebar:
    st.header(f"Olá, {st.session_state.user_atual.capitalize()}")
    st.markdown(f"**Créditos Disponíveis:** {user_doc.get('avaliacoes_restantes', 0)}")
    if st.button("SAIR DO SISTEMA"): st.session_state.logado = False; st.rerun()
    st.divider()
    nome_perfil = st.text_input("Nome", value=st.session_state.user_atual.capitalize())
    peso = st.number_input("Peso Atual (kg)", 30.0, 250.0, 80.0)
    altura = st.number_input("Altura (cm)", 100, 250, 175)
    objetivo = st.selectbox("Objetivo Estratégico", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    up = st.file_uploader("📸 Atualizar Foto para Scanner", type=['jpg', 'jpeg', 'png'])

# --- PROCESSAMENTO DE IA COM CONTROLE DE CRÉDITOS ---
if up and st.button("🚀 INICIAR ESCANEAMENTO PHD"):
    creditos = user_doc.get('avaliacoes_restantes', 0)
    if creditos <= 0 and not st.session_state.is_admin:
        st.error("Créditos insuficientes. Entre em contato com a TechnoBolt para renovação.")
    else:
        with st.status("🧬 PROCESSANDO PROTOCOLO TECHNOBOLT..."):
            img_raw = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
            img_raw.thumbnail((600, 600))
            imc = peso / ((altura/100)**2)
            
            prompt = f"""VOCÊ É UM CONSELHO DE ESPECIALISTAS PHD DA TECHNOBOLT GYM. ANALISE PARA: {nome_perfil} | OBJETIVO: {objetivo} | IMC: {imc:.2f}
            
            ESCREVA 4 RELATÓRIOS ABAIXO DAS SEGUINTES TAGS. OCULTE TÍTULOS E USE SEMPRE A LINGUAGEM "A TECHNOBOLT GYM PRESCREVE".

            [AVALIACAO]
            Aja como PhD Antropometria (ISAK 4). Use termos técnicos com glossário intuitivo entre parênteses. Determine Biotipo, BF% e Postura. Inclua dicas de "Performance Master" para otimizar resultados visuais.

            [NUTRICAO]
            Aja como Nutricionista PhD. DIETA EXTENSA E COMPLETA com 2 alternativas por refeição. Explique termos técnicos (ex: termogênese, densidade nutricional) entre parênteses.

            [SUPLEMENTACAO]
            Aja como PhD Farmacologia. 3-10 itens via Nexo Metabólico. Explique termos técnicos (ex: biodisponibilidade, sinergismo) entre parênteses. Inclua dicas de timing.

            [TREINO]
            Aja como PhD Biomecânica. 7 dias, 8-10 exercícios/dia. Explique termos técnicos (ex: braço de momento, tensão mecânica) entre parênteses. 
            ESTRUTURA: NOME DO EXERCÍCIO | SÉRIES | REPETIÇÕES | JUSTIFICATIVA BIOMECÂNICA. (SEM TABELAS)

            REGRAS GERAIS: Explique TODO termo técnico entre parênteses. Linguagem Institucional Elite."""
            
            res, eng = realizar_scan_phd(prompt, img_raw)
            if res:
                def extrair(tag_inicio, proxima_tag=None):
                    pattern = f"\\{tag_inicio}\\s*(.*?)\\s*(?=\\{proxima_tag}|$)" if proxima_tag else f"\\{tag_inicio}\\s*(.*)"
                    match = re.search(pattern, res, re.DOTALL | re.IGNORECASE)
                    return match.group(1).strip() if match else "Informação em análise..."

                nova_analise = {
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "r1": extrair("[AVALIACAO]", "[NUTRICAO]"),
                    "r2": extrair("[NUTRICAO]", "[SUPLEMENTACAO]"),
                    "r3": extrair("[SUPLEMENTACAO]", "[TREINO]"),
                    "r4": extrair("[TREINO]", None)
                }
                
                # Persistência no MongoDB e abate de crédito
                db.usuarios.update_one({"usuario": st.session_state.user_atual}, {
                    "$push": {"historico_dossies": nova_analise},
                    "$set": {"ultima_analise": nova_analise},
                    "$inc": {"avaliacoes_restantes": -1} if not st.session_state.is_admin else {"avaliacoes_restantes": 0}
                })
                st.success("Análise finalizada! Os dados foram salvos no seu dossiê histórico.")
                st.rerun()

# --- EXIBIÇÃO E HISTÓRICO DE DOSSIÊS ---
historico = user_doc.get('historico_dossies', [])
if historico:
    st.divider()
    datas_historico = [a['data'] for a in reversed(historico)]
    data_selecionada = st.selectbox("📅 Selecionar análise do histórico:", datas_historico)
    
    # Recupera a análise específica selecionada
    d = next(a for a in historico if a['data'] == data_selecionada)
    
    tabs = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino", "📜 Dossiê"])
    conts = [d['r1'], d['r2'], d['r3'], d['r4']]
    tits = ["Avaliacao", "Nutricao", "Suplementos", "Treino"]
    
    for i, tab in enumerate(tabs[:4]):
        with tab:
            st.markdown(f"<div class='result-card-unificado'>{conts[i]}</div>", unsafe_allow_html=True)
            pdf_data = gerar_pdf_elite(nome_perfil, conts[i], tits[i], d['data'])
            st.download_button(label=f"📥 Baixar PDF {tits[i]}", data=pdf_data, 
                               file_name=f"{tits[i]}_TechnoBolt.pdf", mime="application/pdf", key=f"dl_{i}_{data_selecionada}")
    
    with tabs[4]:
        full_text = f"AVALIAÇÃO ANTROPOMÉTRICA:\n{d['r1']}\n\nPLANEJAMENTO NUTRICIONAL:\n{d['r2']}\n\nSUPLEMENTAÇÃO:\n{d['r3']}\n\nPRESCRIÇÃO DE TREINO:\n{d['r4']}"
        st.markdown(f"<div class='result-card-unificado'>{full_text}</div>", unsafe_allow_html=True)
        pdf_full = gerar_pdf_elite(nome_perfil, full_text, "Dossie Completo", d['data'])
        st.download_button(label="📥 BAIXAR DOSSIÊ COMPLETO (PDF)", data=pdf_full, 
                           file_name="Dossie_TechnoBolt.pdf", mime="application/pdf", key=f"full_{data_selecionada}")
else:
    st.info("Nenhuma análise encontrada. Realize o seu primeiro escaneamento no botão da lateral.")
