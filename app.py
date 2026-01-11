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

# --- CONEXÃO MONGODB ---
MONGO_URL = st.secrets.get("MONGO_URL", "mongodb+srv://technobolt:tech@132@cluster0.zbjsvk6.mongodb.net/?appName=Cluster0")

@st.cache_resource
def iniciar_conexao():
    client = MongoClient(MONGO_URL)
    return client['TechnoBoltDB']

try:
    db = iniciar_conexao()
except:
    st.error("Erro ao conectar ao banco de dados.")
    st.stop()

# --- DESIGN SYSTEM TECHNOBOLT ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
    [data-testid="stSidebarCollapseButton"] svg { fill: #3b82f6 !important; width: 28px !important; height: 28px !important; }
    .result-card-unificado { 
        background-color: #0a0a0a !important; border-left: 6px solid #3b82f6;
        border-radius: 15px; padding: 25px; margin-top: 15px; border: 1px solid #1a1a1a;
    }
    .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
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
    return bytes(pdf_output, 'latin-1') if isinstance(pdf_output, str) else bytes(pdf_output)

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

# --- INTERFACE DE ACESSO ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    tab_login, tab_registro = st.tabs(["🔐 Login", "📝 Novo Cadastro"])
    
    with tab_login:
        st.title("TechnoBolt Gym")
        u = st.text_input("Usuário (Login)").lower().strip()
        p = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            user_data = db.usuarios.find_one({"usuario": u})
            if user_data and user_data['senha'] == p:
                if user_data['status'] == 'pendente': st.warning("⚠️ Conta em análise. Aguarde a ativação pelo Admin.")
                elif user_data['status'] == 'inativo': st.error("❌ Conta inativada.")
                else:
                    st.session_state.logado = True
                    st.session_state.user_atual = u
                    st.session_state.is_admin = user_data.get('is_admin', False)
                    st.rerun()
            else: st.error("Usuário ou senha inválidos.")
            
    with tab_registro:
        st.title("Solicitar Acesso")
        new_nome = st.text_input("Nome Completo")
        new_user = st.text_input("Escolha um Login").lower().strip()
        new_pass = st.text_input("Escolha uma Senha", type="password")
        c1, c2, c3 = st.columns(3)
        new_idade = c1.number_input("Idade", 12, 90, 25)
        new_altura = c2.number_input("Altura (cm)", 100, 250, 175)
        new_peso = c3.number_input("Peso (kg)", 30.0, 250.0, 80.0)
        new_obj = st.selectbox("Objetivo Principal", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
        
        if st.button("FINALIZAR CADASTRO"):
            if new_nome and new_user and new_pass:
                if db.usuarios.find_one({"usuario": new_user}): st.error("Este login já está em uso.")
                else:
                    db.usuarios.insert_one({
                        "usuario": new_user, "senha": new_pass, "nome": new_nome,
                        "idade": new_idade, "altura": new_altura, "peso": new_peso,
                        "objetivo": new_obj, "status": "pendente", "avaliacoes_restantes": 0,
                        "is_admin": False, "historico_dossies": []
                    })
                    st.success("✅ Cadastro enviado! Solicite ao Admin a liberação do seu acesso.")
            else: st.warning("Por favor, preencha todos os campos obrigatórios.")
    st.stop()

# --- ÁREA LOGADA ---
user_doc = db.usuarios.find_one({"usuario": st.session_state.user_atual})

if st.session_state.is_admin:
    with st.expander("🛠️ PAINEL ADMINISTRATIVO (GESTÃO DE USUÁRIOS)"):
        users = list(db.usuarios.find({"usuario": {"$ne": "admin"}}))
        for u in users:
            c1, c2, c3, c4 = st.columns([2, 2, 1, 2])
            c1.write(f"**{u.get('nome', u['usuario'])}** ({u['usuario']})")
            new_st = c2.selectbox(f"Status", ["pendente", "ativo", "inativo"], index=["pendente", "ativo", "inativo"].index(u['status']), key=f"st_{u['usuario']}")
            if new_st != u['status']:
                db.usuarios.update_one({"usuario": u['usuario']}, {"$set": {"status": new_st}})
                st.rerun()
            c3.write(f"🪙 {u.get('avaliacoes_restantes', 0)}")
            if c4.button(f"Renovar Ciclo (4)", key=f"ren_{u['usuario']}"):
                db.usuarios.update_one({"usuario": u['usuario']}, {"$set": {"avaliacoes_restantes": 4, "status": "ativo"}})
                st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header(f"Olá, {user_doc.get('nome', st.session_state.user_atual).split()[0]}")
    st.markdown(f"📊 **Créditos:** {user_doc.get('avaliacoes_restantes', 0)}")
    if st.button("SAIR"): st.session_state.logado = False; st.rerun()
    st.divider()
    nome_perfil = st.text_input("Nome no Laudo", value=user_doc.get('nome', st.session_state.user_atual))
    peso = st.number_input("Peso Atual (kg)", 30.0, 250.0, float(user_doc.get('peso', 80)))
    altura = st.number_input("Altura (cm)", 100, 250, int(user_doc.get('altura', 175)))
    objetivo = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"], index=["Hipertrofia", "Lipólise", "Performance", "Postural"].index(user_doc.get('objetivo', "Hipertrofia")))
    up = st.file_uploader("📸 Scanner de Performance", type=['jpg', 'jpeg', 'png'])

# --- PROCESSAMENTO IA ---
if up and st.button("🚀 INICIAR ESCANEAMENTO PHD"):
    if user_doc.get('avaliacoes_restantes', 0) <= 0 and not st.session_state.is_admin:
        st.error("Sem créditos. Solicite renovação ao Admin.")
    else:
        with st.status("🧬 PROCESSANDO PROTOCOLO TECHNOBOLT..."):
            img_raw = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
            img_raw.thumbnail((600, 600)); imc = peso / ((altura/100)**2)
            prompt = f"""VOCÊ É UM CONSELHO DE ESPECIALISTAS PHD DA TECHNOBOLT GYM. ANALISE PARA: {nome_perfil} | OBJETIVO: {objetivo} | IMC: {imc:.2f}
            ESCREVA 4 RELATÓRIOS ABAIXO DAS SEGUINTES TAGS. OCULTE TÍTULOS E USE "A TECHNOBOLT GYM PRESCREVE".

            [AVALIACAO]
            Aja como PhD Antropometria. Use termos técnicos com glossário intuitivo entre parênteses. Determine Biotipo, BF% e Postura.

            [NUTRICAO]
            Aja como Nutricionista PhD. DIETA EXTENSA E COMPLETA com 2 alternativas/refeição. Explique termos técnicos entre parênteses.

            [SUPLEMENTACAO]
            Aja como PhD Farmacologia. 3-10 itens via Nexo Metabólico. Explique termos técnicos entre parênteses.

            [TREINO]
            Aja como PhD Biomecânica. 7 dias, 8-10 exercícios/dia. Explique termos técnicos entre parênteses. SEM TABELAS.

            REGRAS: Explique TODO termo técnico entre parênteses. Adicione dicas de "Performance Master" em cada seção."""
            
            res, eng = realizar_scan_phd(prompt, img_raw)
            if res:
                def extrair(t1, t2=None):
                    pattern = f"\\{t1}\\s*(.*?)\\s*(?=\\{t2}|$)" if t2 else f"\\{t1}\\s*(.*)"
                    m = re.search(pattern, res, re.DOTALL | re.IGNORECASE)
                    return m.group(1).strip() if m else "..."
                
                analise = {
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "r1": extrair("[AVALIACAO]", "[NUTRICAO]"),
                    "r2": extrair("[NUTRICAO]", "[SUPLEMENTACAO]"),
                    "r3": extrair("[SUPLEMENTACAO]", "[TREINO]"),
                    "r4": extrair("[TREINO]", None)
                }
                db.usuarios.update_one({"usuario": st.session_state.user_atual}, {
                    "$push": {"historico_dossies": analise},
                    "$set": {"ultima_analise": analise, "peso": peso, "altura": altura, "objetivo": objetivo},
                    "$inc": {"avaliacoes_restantes": -1} if not st.session_state.is_admin else {"avaliacoes_restantes": 0}
                })
                st.rerun()

# --- HISTÓRICO ---
if user_doc and user_doc.get('historico_dossies'):
    hist = user_doc['historico_dossies']
    datas = [a['data'] for a in reversed(hist)]
    sel_data = st.selectbox("📅 Histórico de Dossiês:", datas)
    d = next(a for a in hist if a['data'] == sel_data)
    
    tabs = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino", "📜 Dossiê"])
    c_list = [d['r1'], d['r2'], d['r3'], d['r4']]; t_list = ["Avaliacao", "Nutricao", "Suplementos", "Treino"]
    
    for i, tab in enumerate(tabs[:4]):
        with tab:
            st.markdown(f"<div class='result-card-unificado'>{c_list[i]}</div>", unsafe_allow_html=True)
            st.download_button(f"📥 Baixar PDF {t_list[i]}", data=gerar_pdf_elite(nome_perfil, c_list[i], t_list[i], d['data']), file_name=f"{t_list[i]}.pdf", mime="application/pdf", key=f"dl_{i}_{sel_data}")
    
    with tabs[4]:
        full_txt = f"AVALIAÇÃO:\n{d['r1']}\n\nNUTRIÇÃO:\n{d['r2']}\n\nSUPLEMENTAÇÃO:\n{d['r3']}\n\nTREINO:\n{d['r4']}"
        st.markdown(f"<div class='result-card-unificado'>{full_txt}</div>", unsafe_allow_html=True)
        st.download_button("📥 BAIXAR DOSSIÊ COMPLETO", data=gerar_pdf_elite(nome_perfil, full_txt, "Dossie Completo", d['data']), file_name="Dossie_TechnoBolt.pdf", mime="application/pdf", key=f"full_{sel_data}")
else:
    st.markdown("<div class='result-card-unificado' style='text-align:center;'>Aguardando Upload para Primeira Análise</div>", unsafe_allow_html=True)
