import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import os
import re
import json
import urllib.parse
from datetime import datetime
from fpdf import FPDF
from pymongo import MongoClient

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TechnoBolt Gym Hub", layout="wide", page_icon="🏋️")

# --- CONEXÃO MONGODB BLINDADA (RENDER) ---
@st.cache_resource
def iniciar_conexao():
    try:
        # Puxa as variáveis de ambiente do Render para segurança total
        user = os.environ.get("MONGO_USER", "technobolt")
        password_raw = os.environ.get("MONGO_PASS", "tech@132")
        host = os.environ.get("MONGO_HOST", "cluster0.zbjsvk6.mongodb.net")
        
        # Tratamento RFC 3986 para caracteres especiais como '@'
        password = urllib.parse.quote_plus(password_raw)
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        
        client = MongoClient(uri)
        client.admin.command('ping')  # Validação de conexão
        return client['TechnoBoltDB']
    except Exception as e:
        st.error(f"Erro de conexão com a nuvem: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM TECHNOBOLT ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
    [data-testid="stSidebarCollapseButton"] { color: transparent !important; font-size: 0px !important; }
    [data-testid="stSidebarCollapseButton"] span { display: none !important; }
    [data-testid="stSidebarCollapseButton"] svg { fill: #3b82f6 !important; visibility: visible !important; width: 28px !important; height: 28px !important; }
    .result-card-unificado { 
        background-color: #0a0a0a !important; border-left: 6px solid #3b82f6;
        border-radius: 15px; padding: 25px; margin-top: 15px; border: 1px solid #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

# --- UTILITÁRIOS E PDF ---
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
    return bytes(pdf.output(dest='S'))

# --- MOTOR DE IA (PENTACAMADA) ---
def realizar_scan_phd(prompt_mestre, img_pil):
    img_byte_arr = io.BytesIO(); img_pil.save(img_byte_arr, format='JPEG')
    img_blob = {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    motores = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-flash-latest"]
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

# --- AUTENTICAÇÃO E REGISTRO ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("TechnoBolt Gym Hub")
    u = st.text_input("Usuário").lower().strip()
    p = st.text_input("Senha", type="password")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("AUTENTICAR"):
            udata = db.usuarios.find_one({"usuario": u}) if db is not None else None
            if udata and udata['senha'] == p:
                if udata['status'] == 'pendente': st.warning("⚠️ Conta em análise. Aguarde a ativação.")
                elif udata['status'] == 'inativo': st.error("❌ Conta desativada.")
                else:
                    st.session_state.logado = True; st.session_state.user_atual = u
                    st.session_state.is_admin = udata.get('is_admin', False); st.rerun()
            else: st.error("Dados de acesso incorretos.")
    with c2:
        if st.button("SOLICITAR ACESSO"):
            if u and p and db is not None:
                if db.usuarios.find_one({"usuario": u}): st.error("Este usuário já existe.")
                else:
                    db.usuarios.insert_one({"usuario": u, "senha": p, "status": "pendente", "avaliacoes_restantes": 0, "historico_dossies": [], "is_admin": False})
                    st.success("Solicitação enviada! Aguarde a aprovação do Admin.")
    st.stop()

# --- INTERFACE ADMIN ---
user_doc = db.usuarios.find_one({"usuario": st.session_state.user_atual})
if st.session_state.is_admin:
    with st.expander("🛠️ PAINEL ADMINISTRATIVO (Gestão de Atletas)"):
        for usr in list(db.usuarios.find({"usuario": {"$ne": "admin"}})):
            c1, c2, c3, c4 = st.columns([2, 2, 1, 2])
            c1.write(f"**{usr['usuario']}**")
            nst = c2.selectbox("Status", ["pendente", "ativo", "inativo"], index=["pendente", "ativo", "inativo"].index(usr['status']), key=f"s_{usr['usuario']}")
            if nst != usr['status']:
                db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"status": nst}}); st.rerun()
            c3.write(f"🪙 {usr.get('avaliacoes_restantes', 0)}")
            if c4.button("Renovar (4)", key=f"r_{usr['usuario']}"):
                db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"avaliacoes_restantes": 4, "status": "ativo"}}); st.rerun()

# --- SIDEBAR (DADOS E SAÚDE) ---
with st.sidebar:
    st.header(f"Atleta: {st.session_state.user_atual.capitalize()}")
    st.write(f"Créditos: **{user_doc.get('avaliacoes_restantes', 0)}**")
    if st.button("LOGOUT"): st.session_state.logado = False; st.rerun()
    st.divider()
    n_perfil = st.text_input("Nome", value=st.session_state.user_atual.capitalize())
    peso = st.number_input("Peso (kg)", 30.0, 250.0, 80.0); altura = st.number_input("Altura (cm)", 100, 250, 175)
    obj = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    
    st.subheader("📋 Histórico de Saúde")
    has_alim = st.checkbox("Possui restrição alimentar?")
    res_alim = st.text_input("Quais?", placeholder="Ex: Glúten, Lactose...") if has_alim else "Nenhuma"
    has_med = st.checkbox("Usa medicamento controlado?")
    res_med = st.text_input("Quais?", placeholder="Ex: Hipertensão...") if has_med else "Nenhum"
    has_fis = st.checkbox("Possui restrição física?")
    res_fis = st.text_input("Quais?", placeholder="Ex: Hérnia de disco...") if has_fis else "Nenhuma"
    
    up = st.file_uploader("📸 Foto Scanner", type=['jpg', 'jpeg', 'png'])

# --- PROCESSAMENTO PHD INTEGRADO ---
if up and st.button("🚀 INICIAR ESCANEAMENTO PHD"):
    if user_doc.get('avaliacoes_restantes', 0) <= 0 and not st.session_state.is_admin:
        st.error("Sem créditos disponíveis. Solicite renovação.")
    else:
        with st.status("🧬 PROCESSANDO PROTOCOLO TECHNOBOLT..."):
            img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
            img.thumbnail((600, 600)); imc = peso / ((altura/100)**2)
            
            prompt = f"""VOCÊ É UM CONSELHO DE ESPECIALISTAS PHD DA TECHNOBOLT GYM.
            ANALISE PARA: {n_perfil} | OBJETIVO: {obj} | IMC: {imc:.2f}
            RESTRIÇÕES CRÍTICAS: Alimentar: {res_alim} | Medicamentos: {res_med} | Física: {res_fis}

            ESCREVA 4 RELATÓRIOS ABAIXO DAS TAGS. OCULTE TÍTULOS E USE SEMPRE "A TECHNOBOLT GYM PRESCREVE".

            [AVALIACAO]
            Aja como PhD em Antropometria formado com Certificação Internacional ISAK (Níveis 1 a 4), Cineantropometria Avançada e Interpretação de DXA/Tomografia. Determine Biotipo, BF% e Postura. Considere as restrições físicas no diagnóstico postural.

            [NUTRICAO]
            Aja como Nutricionista PhD especialista em Nutrição Esportiva e Bioquímica do Metabolismo. Prescreva DIETA EXTENSA (2 alternativas/refeição). CONSIDERE RIGOROSAMENTE: {res_alim}. Explique termos técnicos como termogênese (queima calórica digestiva) e densidade nutricional (qualidade por grama) entre parênteses.

            [SUPLEMENTACAO]
            Aja como PhD em Farmacologia do Exercício e Mecanismos Moleculares. Indique 3 a 10 suplementos. VERIFIQUE RIGOROSAMENTE interações com {res_med}. Explique termos como biodisponibilidade (nível de absorção) e sinergismo (ação conjunta) entre parênteses.

            [TREINO]
            Aja como Personal Trainer PhD em Biomecânica, Cinesiologia e Musculação Avançada. Prescreva 7 dias (8-10 exerc/dia). ADAPTE O TREINO para evitar agravamento de: {res_fis}. Explique termos como braço de momento (alavanca de força) e tensão mecânica (estresse fibrilar) entre parênteses.
            ESTRUTURA: NOME | SÉRIES | REPETIÇÕES | JUSTIFICATIVA (SEM TABELAS).
            
            REGRAS GERAIS: Explique TODO termo técnico entre parênteses de forma intuitiva. Use linguagem Institucional de Elite."""
            
            res, eng = realizar_scan_phd(prompt, img)
            if res:
                def ext(ti, tp=None):
                    p = f"\\{ti}\\s*(.*?)\\s*(?=\\{tp}|$)" if tp else f"\\{ti}\\s*(.*)"
                    m = re.search(p, res, re.DOTALL | re.IGNORECASE)
                    return m.group(1).strip() if m else "Processando..."
                
                nova = {"data": datetime.now().strftime("%d/%m/%Y %H:%M"), "r1": ext("[AVALIACAO]", "[NUTRICAO]"), "r2": ext("[NUTRICAO]", "[SUPLEMENTACAO]"), "r3": ext("[SUPLEMENTACAO]", "[TREINO]"), "r4": ext("[TREINO]", None)}
                db.usuarios.update_one({"usuario": st.session_state.user_atual}, {"$push": {"historico_dossies": nova}, "$inc": {"avaliacoes_restantes": -1} if not st.session_state.is_admin else {"avaliacoes_restantes": 0}})
                st.rerun()

# --- EXIBIÇÃO E HISTÓRICO ---
hist = user_doc.get('historico_dossies', [])
if hist:
    datas = [a['data'] for a in reversed(hist)]; d_sel = st.selectbox("📅 Consultar Histórico de Dossiês:", datas)
    d = next(a for a in hist if a['data'] == d_sel)
    tabs = st.tabs(["📊 Avaliação", "🥗 Nutrição", "💊 Suplementos", "🏋️ Treino", "📜 Dossiê"])
    conts = [d['r1'], d['r2'], d['r3'], d['r4']]; tits = ["Avaliacao", "Nutricao", "Suplementos", "Treino"]
    for i, tab in enumerate(tabs[:4]):
        with tab:
            st.markdown(f"<div class='result-card-unificado'>{conts[i]}</div>", unsafe_allow_html=True)
            st.download_button(f"📥 Baixar PDF {tits[i]}", data=gerar_pdf_elite(n_perfil, conts[i], tits[i], d['data']), file_name=f"{tits[i]}.pdf", mime="application/pdf", key=f"d_{i}_{d_sel}")
    with tabs[4]:
        f_t = f"AVALIAÇÃO ANTROPOMÉTRICA:\n{d['r1']}\n\nPLANEJAMENTO NUTRICIONAL:\n{d['r2']}\n\nSUPLEMENTAÇÃO E FARMACOLOGIA:\n{d['r3']}\n\nPRESCRIÇÃO DE TREINO BIOMECÂNICO:\n{d['r4']}"
        st.markdown(f"<div class='result-card-unificado'>{f_t}</div>", unsafe_allow_html=True)
        st.download_button("📥 BAIXAR DOSSIÊ COMPLETO", data=gerar_pdf_elite(n_perfil, f_t, "Dossie Completo", d['data']), file_name="Dossie_Completo.pdf", mime="application/pdf", key=f"f_{d_sel}")
else: st.info("Sua jornada começa aqui. Realize o primeiro escaneamento para gerar seus relatórios.")
