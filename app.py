import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import os
import re
import pandas as pd
import urllib.parse
from datetime import datetime
from fpdf import FPDF
from pymongo import MongoClient

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="TechnoBolt Gym Hub", layout="wide", page_icon="🏋️")

# --- CONEXÃO MONGODB ---
@st.cache_resource
def iniciar_conexao():
    try:
        user = os.environ.get("MONGO_USER", "technobolt")
        password_raw = os.environ.get("MONGO_PASS", "tech@132")
        host = os.environ.get("MONGO_HOST", "cluster0.zbjsvk6.mongodb.net")
        password = urllib.parse.quote_plus(password_raw)
        uri = f"mongodb+srv://{user}:{password}@{host}/?appName=Cluster0"
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        client.admin.command('ping')
        return client['technoboltgym']
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
    .result-card-unificado { 
        background-color: #0d0d0d !important; border-left: 5px solid #3b82f6;
        border-radius: 12px; padding: 25px; margin-top: 15px; border: 1px solid #1a1a1a;
        line-height: 1.7; color: #e0e0e0; font-family: 'Inter', sans-serif;
    }
    .result-card-unificado b, .result-card-unificado strong { color: #3b82f6; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #3b82f6 !important; color: white !important; }
    .admin-table-header { color: #3b82f6; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- UTILITÁRIOS E PDF ---
def sanitizar_texto_pdf(texto):
    texto = texto.replace('**', '').replace('###', '').replace('##', '').replace('#', '')
    texto = texto.replace('•', '-').replace('✅', '[OK]').replace('📊', '').replace('🥗', '').replace('💊', '').replace('🏋️', '')
    texto = texto.replace('🚀', '>>').replace('|', ' ').replace('--|--', ' ').replace('---', '')
    return texto.encode('latin-1', 'replace').decode('latin-1')

class TechnoBoltPDF(FPDF):
    def header(self):
        self.set_fill_color(10, 10, 10); self.rect(0, 0, 210, 40, 'F')
        self.set_xy(15, 12); self.set_font("Helvetica", "B", 24); self.set_text_color(59, 130, 246)
        self.cell(0, 10, "TECHNOBOLT GYM", ln=True)
        self.set_xy(15, 22); self.set_font("Helvetica", "B", 8); self.set_text_color(150, 150, 150)
        self.cell(0, 5, "INTELECTO ARTIFICIAL APLICADO A ALTA PERFORMANCE HUMANA", ln=True)
        self.set_draw_color(59, 130, 246); self.set_line_width(1); self.line(15, 32, 70, 32); self.ln(20)

    def footer(self):
        self.set_y(-20); self.set_font("Helvetica", "I", 8); self.set_text_color(160, 160, 160)
        self.set_draw_color(230, 230, 230); self.line(15, self.get_y(), 195, self.get_y())
        self.cell(0, 10, "Laudo Tecnologico Confidencial | TechnoBolt Gym Hub", align="C")

def gerar_pdf_elite(nome, conteudo, titulo, data_analise):
    pdf = TechnoBoltPDF()
    pdf.set_auto_page_break(auto=True, margin=20); pdf.add_page()
    pdf.set_fill_color(245, 247, 250); pdf.set_draw_color(220, 220, 220); pdf.rect(15, 45, 180, 20, 'FD')
    pdf.set_xy(20, 48); pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(50, 50, 50)
    pdf.cell(90, 7, f"ATLETA: {nome.upper()}")
    pdf.set_font("Helvetica", "", 10); pdf.cell(0, 7, f"DATA: {data_analise}", ln=True, align="R")
    pdf.set_xy(20, 55); pdf.set_font("Helvetica", "B", 10); pdf.cell(0, 7, f"PROTOCOLO: {titulo.upper()}")
    pdf.set_y(75); pdf.set_font("Helvetica", "", 11); pdf.set_text_color(30, 30, 30)
    texto_limpo = sanitizar_texto_pdf(conteudo)
    pdf.multi_cell(0, 7, texto_limpo)
    pdf_out = pdf.output(dest='S')
    return bytes(pdf_out, 'latin-1') if isinstance(pdf_out, str) else bytes(pdf_out)

# --- MOTOR DE IA (PENTACAMADA COMPLETA 2026) ---
def realizar_scan_phd(prompt_mestre, img_pil):
    img_byte_arr = io.BytesIO(); img_pil.save(img_byte_arr, format='JPEG')
    img_blob = {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}
    chaves = [os.environ.get(f"GEMINI_CHAVE_{i}") for i in range(1, 8)]
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
                    response = model.generate_content([prompt_mestre, img_blob])
                    if response and response.text:
                        return response.text, f"CONTA {idx+1} - {m.upper()}"
                except: continue
        except: continue
    return None, "OFFLINE"

# --- ACESSO ---
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    t1, t2 = st.tabs(["🔐 Login", "📝 Cadastro"])
    with t1:
        u_log = st.text_input("Usuário", key="login_u").lower().strip()
        p_log = st.text_input("Senha", type="password", key="login_p")
        if st.button("ACESSAR HUB"):
            udata = db.usuarios.find_one({"usuario": u_log}) if db is not None else None
            if udata and udata['senha'] == p_log and udata['status'] == 'ativo':
                st.session_state.logado = True; st.session_state.user_atual = u_log; st.session_state.is_admin = udata.get('is_admin', False); st.rerun()
            else: st.error("Acesso negado.")
    with t2:
        n_reg = st.text_input("Nome Completo", key="reg_n")
        u_reg = st.text_input("Login", key="reg_u").lower().strip()
        p_reg = st.text_input("Senha", type="password", key="reg_p")
        g_reg = st.selectbox("Gênero", ["Masculino", "Feminino"], key="reg_g")
        if st.button("CADASTRAR"):
            if n_reg and u_reg and p_reg:
                db.usuarios.insert_one({"usuario": u_reg, "senha": p_reg, "nome": n_reg, "genero": g_reg, "status": "pendente", "avaliacoes_restantes": 0, "historico_dossies": [], "data_renovacao": datetime.now().strftime("%d/%m/%Y")})
                st.success("Solicitado!")
    st.stop()

user_doc = db.usuarios.find_one({"usuario": st.session_state.user_atual})

# --- ADMIN PANEL ---
if st.session_state.is_admin and db is not None:
    with st.expander("🛠️ GESTÃO DE ATLETAS"):
        st.markdown("<div class='admin-table-header'>Controle de Acessos e Créditos</div>", unsafe_allow_html=True)
        h1, h2, h3, h4, h5 = st.columns([2, 2, 1, 1, 2])
        h1.write("**Nome / Usuário**"); h2.write("**Status**"); h3.write("**Créditos**"); h4.write("**Renovação**"); h5.write("**Ações**")
        st.divider()
        for usr in list(db.usuarios.find({"usuario": {"$ne": "admin"}})):
            c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 2])
            c1.write(f"**{usr.get('nome', 'N/A')}**\n({usr['usuario']})")
            op_st = ["pendente", "ativo", "inativo"]; nst = c2.selectbox(f"St_{usr['usuario']}", op_st, index=op_st.index(usr.get('status', 'pendente')), label_visibility="collapsed")
            if nst != usr.get('status'): db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"status": nst}}); st.rerun()
            ncr = c3.number_input(f"Cr_{usr['usuario']}", 0, 100, usr.get('avaliacoes_restantes', 0), label_visibility="collapsed")
            if ncr != usr.get('avaliacoes_restantes'): db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"avaliacoes_restantes": ncr}})
            c4.write(usr.get('data_renovacao', "---"))
            if c5.button(f"Renovar (4)", key=f"renov_{usr['usuario']}"):
                hoje = datetime.now().strftime("%d/%m/%Y")
                db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"avaliacoes_restantes": 4, "status": "ativo", "data_renovacao": hoje}})
                st.rerun()
            st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.header(f"Atleta: {user_doc.get('nome', 'N/A')}")
    st.write(f"Gênero: **{user_doc.get('genero', 'N/A')}**")
    st.write(f"Créditos: **{user_doc.get('avaliacoes_restantes', 0)}**")
    if st.button("LOGOUT"): st.session_state.logado = False; st.rerun()
    peso_at = st.number_input("Peso (kg)", 30.0, 250.0, 80.0); altura = st.number_input("Altura (cm)", 100, 250, 175)
    obj = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    r_a = st.text_area("Restrições Alimentares", "Nenhuma"); r_m = st.text_area("Medicamentos", "Nenhum"); r_f = st.text_area("Restrições Físicas", "Nenhuma")
    up = st.file_uploader("📸 Scanner para Análise", type=['jpg', 'jpeg', 'png'])

# --- PROCESSAMENTO (PROTOCOLOS CLÍNICOS) ---
if up and st.button("🚀 INICIAR ANÁLISE TÉCNICA"):
    if user_doc.get('avaliacoes_restantes', 0) > 0 or st.session_state.is_admin:
        with st.status("🧬 PROCESSANDO PROTOCOLO TECHNOBOLT..."):
            img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
            img.thumbnail((600, 600)); imc = peso_at / ((altura/100)**2); gen = user_doc.get('genero', 'Masculino')
            
            prompt_mestre = f"""VOCÊ É UM CONSELHO TÉCNICO DE ESPECIALISTAS DA TECHNOBOLT GYM.
            DADOS DO ATLETA: GÊNERO {gen} | OBJETIVO {obj} | IMC {imc:.2f}.
            RESTRIÇÕES: {r_a}, {r_m}, {r_f}.

            RESTRITO: NÃO INCLUA SAUDAÇÕES, APRESENTAÇÕES OU TÍTULOS DE SEÇÃO NO TEXTO. 
            A RESPOSTA DEVE SER UM FLUXO DIRETO DE TEXTO FORMAL E TÉCNICO.
            EXPLIQUE TODOS OS TERMOS TÉCNICOS ENTRE PARÊNTESES DE FORMA INTUITIVA.
            TODO O FOCO DO PROTOCOLO DEVE SER NAS NECESSIDADES ESTRUTURAIS IDENTIFICADAS NA IMAGEM PARA O OBJETIVO {obj}.

            [AVALIACAO]
            Aja como Especialista em Cineantropometria e Antropometria (ISAK 4). Analise a imagem para determinar somatotipo (classificação biotipológica), BF% (percentual de gordura) e desvios cinemáticos (erros de padrão de movimento). FOCO: Assimetrias e correções necessárias para {obj}.
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações técnicas para homeostase (equilíbrio interno) e correção postural.

            [NUTRICAO]
            Aja como Especialista em Nutrogenômica (nutrição e expressão gênica) e Nutrologia. Plano dietético extenso (2 opções por refeição). Foco em Flexibilidade Metabólica (eficiência na oxidação de substratos) para {obj} baseado no biotipo visual. Respeite: {r_a}.
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações técnicas para otimizar síntese proteica (construção de tecido) e metabolismo.

            [SUPLEMENTACAO]
            Aja como Especialista em Farmacologia Aplicada e Medicina Ortomolecular (equilíbrio químico celular). Indique 3-10 suplementos via Nexo Metabólico (conexão entre vias bioquímicas). Foco em ativação da via mTOR (via de crescimento muscular) ou Lipólise (queima de gordura) conforme {obj} e gênero {gen}. Verifique: {r_m}.
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações técnicas sobre timing ergogênico (aumento de performance).

            [TREINO]
            Aja como Especialista em Biomecânica de Alta Performance e Neuromecânica (controle neural do movimento). O TREINO DEVE PRIORIZAR AS FALHAS ESTRUTURAIS IDENTIFICADAS NA FOTO. 
            Estrutura: Nome do Exercício | Séries | Reps | Justificativa Biomecânica baseada na imagem. Explique Braço de Momento (alavanca de força) e Perfil de Resistência (torque muscular). Adapte para: {r_f}.
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações técnicas sobre cadência (velocidade) e recrutamento motor.
            """
            
            res, engine = realizar_scan_phd(prompt_mestre, img)
            if res:
                def extrair(tag_inicio, tag_fim=None):
                    padrao = f"\\{tag_inicio}\\s*(.*?)\\s*(?=\\{tag_fim}|$)" if tag_fim else f"\\{tag_inicio}\\s*(.*)"
                    match = re.search(padrao, res, re.DOTALL | re.IGNORECASE)
                    return match.group(1).strip() if match else ""

                r1, r2, r3, r4 = extrair("[AVALIACAO]", "[NUTRICAO]"), extrair("[NUTRICAO]", "[SUPLEMENTACAO]"), extrair("[SUPLEMENTACAO]", "[TREINO]"), extrair("[TREINO]", None)
                if not any([r1, r2, r3, r4]): r1 = res # Fallback total

                nova = {"data": datetime.now().strftime("%d/%m/%Y %H:%M"), "peso_reg": peso_at, "r1": r1 or "...", "r2": r2 or "...", "r3": r3 or "...", "r4": r4 or "..."}
                db.usuarios.update_one({"usuario": st.session_state.user_atual}, {"$push": {"historico_dossies": nova}, "$inc": {"avaliacoes_restantes": -1} if not st.session_state.is_admin else {"avaliacoes_restantes": 0}})
                st.rerun()

# --- EXIBIÇÃO ---
if user_doc and user_doc.get('historico_dossies'):
    hist = user_doc['historico_dossies']
    sel = st.selectbox("📅 Laudos Anteriores", [a['data'] for a in reversed(hist)])
    d = next(a for a in hist if a['data'] == sel)
    tabs = st.tabs(["📊 Antropometria", "🥗 Nutrologia", "💊 Suplementação", "🏋️ Biomecânica", "📜 Completo"])
    cs, ts = [d['r1'], d['r2'], d['r3'], d['r4']], ["Antropometria", "Nutrologia", "Suplementacao", "Biomecanica"]
    for i, tab in enumerate(tabs[:4]):
        with tab:
            st.markdown(f"<div class='result-card-unificado'>{cs[i].replace('\n', '<br>')}</div>", unsafe_allow_html=True)
            st.download_button(f"📥 PDF {ts[i]}", data=gerar_pdf_elite(user_doc['nome'], cs[i], ts[i], d['data']), file_name=f"{ts[i]}.pdf", key=f"{ts[i]}_{sel}")
    with tabs[4]:
        f_t = f"LAUDO ANTROPOMÉTRICO:\n{d['r1']}\n\nLAUDO NUTROLÓGICO:\n{d['r2']}\n\nLAUDO DE SUPLEMENTAÇÃO:\n{d['r3']}\n\nLAUDO BIOMECÂNICO:\n{d['r4']}"
        st.markdown(f"<div class='result-card-unificado'>{f_t.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
        st.download_button("📥 BAIXAR LAUDO COMPLETO", data=gerar_pdf_elite(user_doc['nome'], f_t, "Laudo Completo", d['data']), file_name="Laudo_Completo.pdf", key=f"full_{sel}")
