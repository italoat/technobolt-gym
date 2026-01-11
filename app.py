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

# --- CONEXÃO MONGODB BLINDADA ---
@st.cache_resource
def iniciar_conexao():
    try:
        user = os.environ.get("MONGO_USER", "technobolt")
        password_raw = os.environ.get("MONGO_PASS", "tech@132")
        host = os.environ.get("MONGO_HOST", "cluster0.zbjsvk6.mongodb.net")
        password = urllib.parse.quote_plus(password_raw)
        uri = "mongodb+srv://{}:{}@{}/?appName=Cluster0".format(user, password, host)
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        client.admin.command('ping')
        return client['technoboltgym']
    except Exception as e:
        st.error("Erro de conexão com o Banco de Dados: {}".format(e))
        return None

db = iniciar_conexao()

# --- DESIGN SYSTEM TECHNOBOLT ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #000000 !important; }
    .result-card-unificado { 
        background-color: #0d0d0d !important; border-left: 5px solid #3b82f6;
        border-radius: 12px; padding: 25px; margin-top: 15px; border: 1px solid #1a1a1a;
        line-height: 1.7; color: #e0e0e0;
    }
    .result-card-unificado b, .result-card-unificado strong { color: #3b82f6; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #3b82f6 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- CLASSE PDF MODERNA E PROFISSIONAL ---
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
        self.cell(0, 10, "Laudo Tecnológico Confidencial | TechnoBolt Gym Hub | Página {}".format(self.page_no()), align="C")

def gerar_pdf_elite(nome, conteudo, titulo, data_analise):
    pdf = TechnoBoltPDF()
    pdf.set_auto_page_break(auto=True, margin=20); pdf.add_page()
    pdf.set_fill_color(245, 247, 250); pdf.set_draw_color(220, 220, 220); pdf.rect(15, 45, 180, 20, 'FD')
    pdf.set_xy(20, 48); pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(50, 50, 50)
    pdf.cell(90, 7, "ATLETA: {}".format(nome.upper()))
    pdf.set_font("Helvetica", "", 10); pdf.cell(0, 7, "DATA DA EMISSÃO: {}".format(data_analise), ln=True, align="R")
    pdf.set_xy(20, 55); pdf.set_font("Helvetica", "B", 10); pdf.cell(0, 7, "PROTOCOLO: {}".format(titulo.upper()))
    pdf.set_y(75); pdf.set_font("Helvetica", "", 11); pdf.set_text_color(30, 30, 30)
    
    txt = conteudo.replace('**', '').replace('###', '').replace('•', '-')
    linhas = txt.split('\n')
    for linha in linhas:
        if "TECHNOBOLT INSIGHT" in linha.upper():
            pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(59, 130, 246)
            pdf.multi_cell(0, 8, linha)
            pdf.set_font("Helvetica", "", 11); pdf.set_text_color(30, 30, 30)
        else:
            pdf.multi_cell(0, 7, linha.encode('latin-1', 'replace').decode('latin-1'))
    
    pdf_out = pdf.output(dest='S')
    return bytes(pdf_out, 'latin-1') if isinstance(pdf_out, str) else bytes(pdf_out)

# --- MOTOR DE IA (PENTACAMADA) ---
def realizar_scan_phd(prompt_mestre, img_pil):
    img_byte_arr = io.BytesIO(); img_pil.save(img_byte_arr, format='JPEG')
    img_blob = {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}
    chaves = [os.environ.get("GEMINI_CHAVE_{}".format(i)) for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    motores = ["models/gemini-3-flash-preview", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-2.0-flash-lite", "models/gemini-flash-latest"]
    for idx, key in enumerate(chaves):
        try:
            genai.configure(api_key=key)
            for m in motores:
                try:
                    model = genai.GenerativeModel(m)
                    response = model.generate_content([prompt_mestre, img_blob])
                    return response.text, "CONTA {} - {}".format(idx+1, m.upper())
                except: continue
        except: continue
    return None, "OFFLINE"

# --- ACESSO ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    t1, t2 = st.tabs(["🔐 Login Atleta", "📝 Solicitar Cadastro"])
    with t1:
        u = st.text_input("User").lower().strip(); p = st.text_input("Pass", type="password")
        if st.button("ACESSAR HUB"):
            udata = db.usuarios.find_one({"usuario": u}) if db is not None else None
            if udata and udata['senha'] == p and udata['status'] == 'ativo':
                st.session_state.logado = True; st.session_state.user_atual = u; st.session_state.is_admin = udata.get('is_admin', False); st.rerun()
            else: st.error("Acesso negado ou conta em análise.")
    with t2:
        n_n = st.text_input("Nome Completo"); n_u = st.text_input("Login").lower().strip(); n_p = st.text_input("Senha", type="password")
        if st.button("SOLICITAR ACESSO"):
            if n_n and n_u and n_p and db is not None:
                db.usuarios.insert_one({"usuario": n_u, "senha": n_p, "nome": n_n, "status": "pendente", "avaliacoes_restantes": 0, "historico_dossies": []})
                st.success("Cadastro solicitado! O Admin ativará sua conta em breve.")
    st.stop()

user_doc = db.usuarios.find_one({"usuario": st.session_state.user_atual}) if db is not None else {}

# ADMIN PANEL
if st.session_state.is_admin and db is not None:
    with st.expander("🛠️ PAINEL ADMINISTRATIVO TECHNOBOLT"):
        for usr in list(db.usuarios.find({"usuario": {"$ne": "admin"}})):
            c1, c2, c3 = st.columns([2, 2, 2])
            c1.write(usr['usuario'])
            if c2.button("Ativar/Renovar {}".format(usr['usuario']), key=usr['usuario']):
                db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"status": "ativo", "avaliacoes_restantes": 4}}); st.rerun()

# --- SIDEBAR & DASHBOARD ---
with st.sidebar:
    st.header(f"Atleta: {user_doc.get('nome', st.session_state.user_atual).split()[0]}")
    st.write("Créditos: {}".format(user_doc.get('avaliacoes_restantes', 0)))
    if st.button("LOGOUT"): st.session_state.logado = False; st.rerun()
    
    if user_doc.get('historico_dossies'):
        st.divider(); st.subheader("📈 Evolução Biométrica")
        pesos = [a.get('peso_reg', 80) for a in user_doc['historico_dossies']]
        datas = [a['data'].split()[0] for a in user_doc['historico_dossies']]
        if len(pesos) > 1:
            df_evolucao = pd.DataFrame({"Data": datas, "Peso (kg)": pesos})
            st.line_chart(df_evolucao.set_index("Data"))
    
    st.divider()
    peso_atual = st.number_input("Peso (kg)", 30.0, 250.0, 80.0); altura = st.number_input("Altura (cm)", 100, 250, 175)
    obj = st.selectbox("Objetivo", ["Hipertrofia", "Lipólise", "Performance", "Postural"])
    res_alim = st.text_area("Restrições Alimentares", "Nenhuma"); res_med = st.text_area("Medicamentos", "Nenhum"); res_fis = st.text_area("Restrições Físicas", "Nenhuma")
    up = st.file_uploader("📸 Scanner de Performance", type=['jpg', 'jpeg', 'png'])

# --- PROCESSAMENTO (PROMPTS DETALHADOS RESTAURADOS) ---
if up and st.button("🚀 INICIAR ANÁLISE CLÍNICA"):
    if (user_doc.get('avaliacoes_restantes', 0) > 0 or st.session_state.is_admin) and db is not None:
        with st.status("🧬 PROCESSANDO PROTOCOLO TECHNOBOLT..."):
            img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
            img.thumbnail((600, 600)); imc = peso_atual / ((altura/100)**2)
            
            prompt_mestre = f"""VOCÊ É UM CONSELHO TÉCNICO DE ESPECIALISTAS DA TECHNOBOLT GYM. 
            PACIENTE/ATLETA: {user_doc.get('nome')} | OBJETIVO: {obj} | IMC: {imc:.2f}
            RESTRIÇÕES: Alimentar: {res_alim} | Médica: {res_med} | Física: {res_fis}

            ESCREVA 4 RELATÓRIOS TÉCNICOS SEPARADOS PELAS TAGS ABAIXO. REMOVA CABEÇALHOS REDUNDANTES E TÍTULOS ACADÊMICOS (COMO PHD).
            USE LINGUAGEM TÉCNICA E PROFISSIONAL. EXPLIQUE TERMOS TÉCNICOS EM PARÊNTESES.

            [AVALIACAO]
            Aja como Especialista em Antropometria formado com Certificação Internacional ISAK (Níveis 1 a 4). Realize a análise cineantropometria (medidas humanas) para determinar o somatotipo (tipo físico), BF% (percentual de gordura) e desvios cinemáticos (erros de movimento) ou posturais. 
            Considere rigorosamente a restrição física: {res_fis}. 
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações técnicas para maximizar a homeostase (equilíbrio interno) e estética funcional.

            [NUTRICAO]
            Aja como Especialista em Nutrologia e Metabolismo Esportivo. Prescreva planejamento dietético extenso (ao menos 2 alternativas por refeição). 
            Respeite RIGOROSAMENTE as restrições alimentares: {res_alim}. 
            Explique termos como Termogênese Induzida pela Dieta (energia gasta na digestão) e Densidade Nutricional (riqueza de nutrientes por caloria).
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações para otimizar a síntese proteica (construção de tecido) e aporte energético.

            [SUPLEMENTACAO]
            Aja como Especialista em Farmacologia Aplicada à Performance. Indique de 3 a 10 suplementos via Nexo Metabólico (conexão entre processos químicos).
            Verifique interações com: {res_med}. Explique Biodisponibilidade (taxa de absorção) e Sinergismo Nutricional (quando substâncias potencializam uma à outra).
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações sobre o timing ergogênico (aumento de performance) e empilhamento nutricional.

            [TREINO]
            Aja como Especialista em Biomecânica e Fisiologia do Exercício. Prescreva protocolo de 7 dias (8 a 10 exercícios por dia). 
            Adapte o plano para as restrições: {res_fis}. Estrutura: NOME DO EXERCÍCIO | SÉRIES | REPS | JUSTIFICATIVA TÉCNICA (SEM TABELAS).
            Explique termos como Braço de Momento (alavanca de força) e Tensão Mecânica (estresse físico nas fibras).
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações sobre cadência (velocidade) e recrutamento de unidades motoras.
            """
            
            res, engine_info = realizar_scan_phd(prompt_mestre, img)
            if res:
                def ext(ti, tp=None):
                    p = f"\\{ti}\\s*(.*?)\\s*(?=\\{ti}|$)" if tp is None else f"\\{ti}\\s*(.*?)\\s*(?=\\{tp}|$)"
                    m = re.search(p, res, re.DOTALL | re.IGNORECASE)
                    return m.group(1).strip() if m else "..."
                
                nova_analise = {
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "peso_reg": peso_atual,
                    "r1": ext("[AVALIACAO]", "[NUTRICAO]"), "r2": ext("[NUTRICAO]", "[SUPLEMENTACAO]"),
                    "r3": ext("[SUPLEMENTACAO]", "[TREINO]"), "r4": ext("[TREINO]", None),
                    "engine": engine_info
                }
                db.usuarios.update_one({"usuario": st.session_state.user_atual}, {
                    "$push": {"historico_dossies": nova_analise},
                    "$inc": {"avaliacoes_restantes": -1} if not st.session_state.is_admin else {"avaliacoes_restantes": 0}
                })
                st.rerun()

# --- EXIBIÇÃO ---
if user_doc and user_doc.get('historico_dossies'):
    hist = user_doc['historico_dossies']
    sel = st.selectbox("📅 Selecionar Laudo Histórico", [a['data'] for a in reversed(hist)])
    d = next(a for a in hist if a['data'] == sel)
    tabs = st.tabs(["📊 Antropometria", "🥗 Nutrologia", "💊 Suplementação", "🏋️ Biomecânica", "📜 Laudo Completo"])
    cs = [d['r1'], d['r2'], d['r3'], d['r4']]; ts = ["Antropometria", "Nutrologia", "Suplementacao", "Biomecanica"]
    for i, tab in enumerate(tabs[:4]):
        with tab:
            st.markdown("<div class='result-card-unificado'>{}</div>".format(cs[i].replace('\n', '<br>')), unsafe_allow_html=True)
            st.download_button("📥 Baixar PDF {}".format(ts[i]), data=gerar_pdf_elite(user_doc.get('nome'), cs[i], ts[i], d['data']), file_name="{}.pdf".format(ts[i]), key="{}_{}".format(ts[i], sel))
    with tabs[4]:
        f_t = "LAUDO ANTROPOMÉTRICO:\n{}\n\nLAUDO NUTROLÓGICO:\n{}\n\nLAUDO DE SUPLEMENTAÇÃO:\n{}\n\nLAUDO BIOMECÂNICO:\n{}".format(d['r1'], d['r2'], d['r3'], d['r4'])
        st.markdown("<div class='result-card-unificado'>{}</div>".format(f_t.replace('\n', '<br>')), unsafe_allow_html=True)
        st.download_button("📥 BAIXAR LAUDO COMPLETO", data=gerar_pdf_elite(user_doc.get('nome'), f_t, "Laudo Completo", d['data']), file_name="Laudo_Completo.pdf", key="f_{}".format(sel))
