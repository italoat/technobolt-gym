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

# --- CONEXÃO MONGODB BLINDADA (RENDER) ---
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

# --- DESIGN SYSTEM ---
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
    .admin-table-header { color: #3b82f6; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- UTILITÁRIOS E PDF (VISUAL PROFISSIONAL + FIX UNICODE) ---
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
    pdf.cell(90, 7, "ATLETA: {}".format(nome.upper()))
    pdf.set_font("Helvetica", "", 10); pdf.cell(0, 7, "DATA: {}".format(data_analise), ln=True, align="R")
    pdf.set_xy(20, 55); pdf.set_font("Helvetica", "B", 10); pdf.cell(0, 7, "PROTOCOLO: {}".format(titulo.upper()))
    pdf.set_y(75); pdf.set_font("Helvetica", "", 11); pdf.set_text_color(30, 30, 30)
    texto_limpo = sanitizar_texto_pdf(conteudo)
    pdf.multi_cell(0, 7, texto_limpo)
    pdf_out = pdf.output(dest='S')
    return bytes(pdf_out, 'latin-1') if isinstance(pdf_out, str) else bytes(pdf_out)

# --- RESTAURAÇÃO: MOTOR DE IA (PENTACAMADA DE ALTA DISPONIBILIDADE) ---
def realizar_scan_phd(prompt_mestre, img_pil):
    img_byte_arr = io.BytesIO(); img_pil.save(img_byte_arr, format='JPEG')
    img_blob = {"mime_type": "image/jpeg", "data": img_byte_arr.getvalue()}
    
    # Rodízio de chaves de API (1 a 7)
    chaves = [os.environ.get("GEMINI_CHAVE_{}".format(i)) for i in range(1, 8)]
    chaves = [k for k in chaves if k]
    
    # Motores em ordem de potência/estabilidade para 2026
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
                    return response.text, "CONTA {} - {}".format(idx+1, m.upper())
                except: continue # Se o motor falhar, tenta o próximo motor da mesma chave
        except: continue # Se a chave estiver offline/bloqueada, tenta a próxima chave
    return None, "OFFLINE"

# --- ACESSO ---
if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    t1, t2 = st.tabs(["🔐 Login Atleta", "📝 Solicitar Cadastro"])
    with t1:
        u = st.text_input("Usuário").lower().strip(); p = st.text_input("Senha", type="password")
        if st.button("ACESSAR HUB"):
            udata = db.usuarios.find_one({"usuario": u}) if db is not None else None
            if udata and udata['senha'] == p and udata['status'] == 'ativo':
                st.session_state.logado = True; st.session_state.user_atual = u; st.session_state.is_admin = udata.get('is_admin', False); st.rerun()
            else: st.error("Acesso negado ou conta em análise.")
    with t2:
        n_n = st.text_input("Nome Completo"); n_u = st.text_input("Login").lower().strip(); n_p = st.text_input("Senha", type="password")
        if st.button("SOLICITAR ACESSO"):
            if n_n and n_u and n_p and db is not None:
                if db.usuarios.find_one({"usuario": n_u}): st.error("Login já em uso.")
                else:
                    db.usuarios.insert_one({
                        "usuario": n_u, "senha": n_p, "nome": n_n, "status": "pendente", 
                        "avaliacoes_restantes": 0, "historico_dossies": [], 
                        "data_renovacao": datetime.now().strftime("%d/%m/%Y")
                    })
                    st.success("Cadastro solicitado!")
    st.stop()

user_doc = db.usuarios.find_one({"usuario": st.session_state.user_atual}) if db is not None else {}

# --- ADMIN PANEL (TABULAR & EDITÁVEL) ---
if st.session_state.is_admin and db is not None:
    with st.expander("🛠️ GESTÃO E CONTROLE DE ATLETAS"):
        st.markdown("<div class='admin-table-header'>Controle de Acessos e Créditos</div>", unsafe_allow_html=True)
        h1, h2, h3, h4, h5 = st.columns([2, 2, 1, 1, 2])
        h1.write("**Nome / Usuário**"); h2.write("**Status**"); h3.write("**Créditos**"); h4.write("**Renovação**"); h5.write("**Ações**")
        st.divider()

        usuarios_lista = list(db.usuarios.find({"usuario": {"$ne": "admin"}}))
        for usr in usuarios_lista:
            c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 2])
            c1.write(f"**{usr.get('nome', 'N/A')}**\n({usr['usuario']})")
            
            opcoes_status = ["pendente", "ativo", "inativo"]
            current_status = usr.get('status', 'pendente')
            new_status = c2.selectbox(f"St_{usr['usuario']}", opcoes_status, index=opcoes_status.index(current_status), label_visibility="collapsed")
            if new_status != current_status:
                db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"status": new_status}})
                st.toast(f"Status de {usr['usuario']} atualizado!")
            
            new_credits = c3.number_input(f"Cr_{usr['usuario']}", 0, 100, usr.get('avaliacoes_restantes', 0), label_visibility="collapsed")
            if new_credits != usr.get('avaliacoes_restantes'):
                db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"avaliacoes_restantes": new_credits}})
            
            c4.write(usr.get('data_renovacao', "---"))
            
            if c5.button(f"Renovar (4)", key=f"ren_{usr['usuario']}"):
                hoje = datetime.now().strftime("%d/%m/%Y")
                db.usuarios.update_one({"usuario": usr['usuario']}, {"$set": {"avaliacoes_restantes": 4, "status": "ativo", "data_renovacao": hoje}})
                st.rerun()
            st.divider()

# --- SIDEBAR & DASHBOARD ---
with st.sidebar:
    st.header(f"Atleta: {user_doc.get('nome', st.session_state.user_atual).split()[0]}")
    st.write("Créditos: {}".format(user_doc.get('avaliacoes_restantes', 0)))
    if st.button("SAIR"): st.session_state.logado = False; st.rerun()
    
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
    up = st.file_uploader("📸 Scanner", type=['jpg', 'jpeg', 'png'])

# --- PROCESSAMENTO: PROMPTS TÉCNICOS PHD ---
if up and st.button("🚀 INICIAR ANÁLISE CLÍNICA"):
    if (user_doc.get('avaliacoes_restantes', 0) > 0 or st.session_state.is_admin) and db is not None:
        with st.status("🧬 EXECUTANDO PROTOCOLO TECHNOBOLT..."):
            img = ImageOps.exif_transpose(Image.open(up)).convert("RGB")
            img.thumbnail((600, 600)); imc = peso_atual / ((altura/100)**2)
            
            prompt_mestre = f"""VOCÊ É UM CONSELHO TÉCNICO DE ESPECIALISTAS DA TECHNOBOLT GYM. 
            PACIENTE/ATLETA: {user_doc.get('nome')} | OBJETIVO: {obj} | IMC: {imc:.2f}
            RESTRIÇÕES: Alimentar: {res_alim} | Médica: {res_med} | Física: {res_fis}

            ESCREVA 4 RELATÓRIOS TÉCNICOS SEPARADOS PELAS TAGS ABAIXO. REMOVA CABEÇALHOS REDUNDANTES.
            USE LINGUAGEM ESTRITAMENTE TÉCNICA E PROFISSIONAL. EXPLIQUE TERMOS TÉCNICOS EM PARÊNTESES.

            [AVALIACAO]
            Aja como Especialista em Antropometria e Cineantropometria Avançada. Analise a imagem para determinar o Somatotipo, BF% estimado e desvios cinemáticos. FOCO: Identificar assimetrias miofasciais e alinhamento de processos acromiais e pélvicos. Considere restrição física: {res_fis}. 
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações técnicas para homeostase e correção postural imediata.

            [NUTRICAO]
            Aja como Especialista em Nutrologia e Nutrogenômica. Prescreva planejamento dietético extenso (2 alternativas por refeição). FOCO: Flexibilidade Metabólica e Gestão da Carga Glicêmica. Respeite: {res_alim}. Explique Termogênese Induzida e Densidade Nutricional.
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações para otimizar a sensibilidade insulínica e síntese proteica.

            [SUPLEMENTACAO]
            Aja como Especialista em Farmacodinâmica e Suplementação Esportiva. Indique 3 a 10 suplementos via Nexo Metabólico. FOCO: Ativação da via mTOR e modulação do Cortisol matinal. Verifique interações com: {res_med}. Explique Biodisponibilidade e Sinergismo Nutricional.
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações sobre janelas de absorção e empilhamento ergogênico.

            [TREINO]
            Aja como Especialista em Biomecânica de Alta Performance. Protocolo de 7 dias (8-10 exerc/dia). FOCO: Perfil de Resistência e Relação Comprimento-Tensão. Adapte para: {res_fis}. Estrutura: NOME DO EXERCÍCIO | SÉRIES | REPS | JUSTIFICATIVA TÉCNICA (SEM TABELAS). Explique Braço de Momento e Tensão Mecânica.
            AO FINAL: 🚀 TECHNOBOLT INSIGHT: 3 recomendações sobre cadência, controle de fundo de série e recrutamento motor.
            """
            
            res, engine_info = realizar_scan_phd(prompt_mestre, img)
            if res:
                def ext(ti, tp=None):
                    p = f"\\{ti}\\s*(.*?)\\s*(?=\\{ti}|$)" if tp is None else f"\\{ti}\\s*(.*?)\\s*(?=\\{tp}|$)"
                    m = re.search(p, res, re.DOTALL | re.IGNORECASE)
                    return m.group(1).strip() if m else "..."
                
                analise = {
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"), "peso_reg": peso_atual,
                    "r1": ext("[AVALIACAO]", "[NUTRICAO]"), "r2": ext("[NUTRICAO]", "[SUPLEMENTACAO]"),
                    "r3": ext("[SUPLEMENTACAO]", "[TREINO]"), "r4": ext("[TREINO]", None),
                    "engine": engine_info
                }
                db.usuarios.update_one({"usuario": st.session_state.user_atual}, {
                    "$push": {"historico_dossies": analise},
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
            st.download_button("📥 PDF {}".format(ts[i]), data=gerar_pdf_elite(user_doc.get('nome'), cs[i], ts[i], d['data']), file_name="{}.pdf".format(ts[i]), key="{}_{}".format(ts[i], sel))
    with tabs[4]:
        f_t = "LAUDO ANTROPOMÉTRICO:\n{}\n\nLAUDO NUTROLÓGICO:\n{}\n\nLAUDO DE SUPLEMENTAÇÃO:\n{}\n\nLAUDO BIOMECÂNICO:\n{}".format(d['r1'], d['r2'], d['r3'], d['r4'])
        st.markdown("<div class='result-card-unificado'>{}</div>".format(f_t.replace('\n', '<br>')), unsafe_allow_html=True)
        st.download_button("📥 BAIXAR LAUDO COMPLETO", data=gerar_pdf_elite(user_doc.get('nome'), f_t, "Laudo Completo", d['data']), file_name="Laudo_Completo.pdf", key="f_{}".format(sel))
