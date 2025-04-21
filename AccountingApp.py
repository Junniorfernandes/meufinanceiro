import streamlit as st
from datetime import datetime
import json
import os
import pandas as pd
import io
from fpdf import FPDF # Certifique-se de que a biblioteca fpdf2 está instalada (pip install fpdf2)
import unicodedata # Importar para normalização de strings

# --- Estilo CSS para os botões de navegação ---
st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: #f0f2f6; /* Cor de fundo clara */
        color: #262730; /* Cor do texto escura */
        border-radius: 8px; /* Cantos arredondados */
        border: 1px solid #d4d7de; /* Borda sutil */
        padding: 8px 16px; /* Espaçamento interno */
        font-weight: bold; /* Texto em negrito */
        display: inline-flex; /* Alinha os itens inline */
        align-items: center; /* Alinha verticalmente o ícone e o texto */
        justify-content: center; /* Centraliza o conteúdo */
        gap: 8px; /* Espaço entre o ícone e o texto */
        width: auto; /* Largura automática para se ajustar ao conteúdo */
    }
    div.stButton > button:hover {
        background-color: #d4d7de; /* Cor de fundo ao passar o mouse */
        color: #262730;
    }
    /* Estilo para os botões de exclusão */
    div.stButton > button[kind="secondary"] {
        background-color: #003548; /* Fundo vermelho claro */
        color: #ffffff; /* Texto vermelho escuro */
        border-color: #fbcfe8; /* Borda vermelha */
    }
     div.stButton > button[kind="secondary"]:hover {
        background-color: #D6110F; /* Fundo vermelho ao passar o mouse */
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_FILE = "lancamentos.json"
USUARIOS_FILE = "usuarios.json"

# Define as categorias padrão de receita (conforme seu código original)
CATEGORIAS_PADRAO_RECEITA = ["Serviços","Vendas"]
# O código original não tinha categorias padrão de despesa ou gestão delas por usuário.


# --- Funções de Carregamento e Salvamento ---

def salvar_usuarios():
    with open(USUARIOS_FILE, "w") as f:
        json.dump(st.session_state.get('usuarios', []), f, indent=4)

def carregar_usuarios():
    # Lista de usuários a serem adicionados caso o arquivo não exista ou esteja vazio/inválido
    # Mapeando chaves do seu pedido (Usuario, email, Função) para chaves do código (Nome, Email, Tipo)
    usuarios_iniciais_padrao = [
        {
            "Nome": "Junior Fernandes",
            "Email": "valmirfernandescontabilidade@gmail.com",
            "Senha": "114316", # **Aviso: Senha em texto plano, inseguro para produção!**
            "Tipo": "Administrador" # Mapeado de 'Função'
        },
        {
            "Nome": "Junior Fernandes",
            "Email": "valmirfernandescontabilidade@hmail.com",
            "Senha": "123456", # **Aviso: Senha em texto plano, inseguro para produção!**
            "Tipo": "Cliente" # Mapeado de 'Função'
        },
        {
            "Nome": "Camila Garcia",
            "Email": "boatardecamila@gmail.com",
            "Senha": "123456", # **Aviso: Senha em texto plano, inseguro para produção!**
            "Tipo": "Cliente" # Mapeado de 'Função'
        }
    ]

    if os.path.exists(USUARIOS_FILE):
        try:
            with open(USUARIOS_FILE, "r") as f:
                content = f.read()
                if content:
                    usuarios = json.loads(content)
                    # Garante que cada usuário tem a lista de categorias_receita (se não existir)
                    for usuario in usuarios:
                         if 'categorias_receita' not in usuario:
                              usuario['categorias_receita'] = []
                    st.session_state['usuarios'] = usuarios
                    # st.info("Usuários carregados do arquivo existente.") # Opcional: Adicionar log visual
                else:
                    # Arquivo existe, mas está vazio. Inicializa com usuários padrão.
                    st.session_state['usuarios'] = usuarios_iniciais_padrao
                    # Adiciona a chave categorias_receita aos usuários recém-adicionados, se necessário
                    for usuario in st.session_state['usuarios']:
                         if 'categorias_receita' not in usuario:
                              usuario['categorias_receita'] = []
                    salvar_usuarios() # Salva os usuários padrão no arquivo vazio
                    st.info("Arquivo de usuários vazio encontrado. Usuários iniciais padrão adicionados e salvos.")

        except json.JSONDecodeError:
            st.error("Erro ao decodificar o arquivo de usuários. Inicializando com usuários iniciais padrão.")
            # Arquivo existe, mas contém JSON inválido. Inicializa com usuários padrão.
            st.session_state['usuarios'] = usuarios_iniciais_padrao
             # Adiciona a chave categorias_receita aos usuários recém-adicionados, se necessário
            for usuario in st.session_state['usuarios']:
                 if 'categorias_receita' not in usuario:
                      usuario['categorias_receita'] = []
            salvar_usuarios() # Salva os usuários padrão no novo arquivo (sobrescreve o inválido)
    else:
        st.info("Arquivo de usuários não encontrado. Criando com usuários iniciais padrão.")
        # Arquivo não existe. Inicializa com usuários padrão.
        st.session_state['usuarios'] = usuarios_iniciais_padrao
         # Adiciona a chave categorias_receita aos usuários recém-adicionados, se necessário
        for usuario in st.session_state['usuarios']:
             if 'categorias_receita' not in usuario:
                  usuario['categorias_receita'] = []
        salvar_usuarios() # Salva os usuários padrão no novo arquivo

def salvar_lancamentos():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.get("lancamentos", []), f, indent=4)

def carregar_lancamentos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                content = f.read()
                if content:
                    st.session_state["lancamentos"] = json.loads(content)
                else:
                     st.session_state["lancamentos"] = []
        except json.JSONDecodeError:
            st.error("Erro ao decodificar o arquivo de lançamentos. Criando um novo.")
            st.session_state["lancamentos"] = []
            salvar_lancamentos()
    else:
        st.session_state["lancamentos"] = []


# --- Inicialização de Estado e Auto-Login ---

# Garante que a lista de usuários está carregada/inicializada primeiro
if 'usuarios' not in st.session_state:
    carregar_usuarios()

# Variáveis de estado para controle
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = 'dashboard'
# Removendo a inicialização 'autenticado = False' para permitir o auto-login abaixo

# AUTO-LOGIN: Configura o primeiro usuário carregado como logado ao iniciar a sessão
if 'autenticado' not in st.session_state or not st.session_state['autenticado']: # Só executa auto-login se não estiver autenticado
    if st.session_state.get('usuarios'): # Verifica se a lista de usuários não está vazia
        primeiro_usuario = st.session_state['usuarios'][0] # Pega o primeiro usuário da lista
        st.session_state['autenticado'] = True
        st.session_state['usuario_atual_email'] = primeiro_usuario.get('Email')
        st.session_state['usuario_atual_nome'] = primeiro_usuario.get('Nome')
        st.session_state['tipo_usuario_atual'] = primeiro_usuario.get('Tipo')
        st.session_state['usuario_atual_index'] = 0 # O índice do primeiro usuário é 0

        # Carrega as categorias personalizadas de receita do usuário logado e combina com as padrão
        usuario_categorias_receita = primeiro_usuario.get('categorias_receita', [])
        todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + usuario_categorias_receita))
        st.session_state['todas_categorias_receita'] = todas_unicas_receita

        st.sidebar.success(f"Acesso direto como: {st.session_state['usuario_atual_nome']}")
        # Não precisa de rerun imediato aqui, o fluxo normal do main continua
    else:
        st.session_state['autenticado'] = False # Garante que o estado é False se não há usuários
        st.sidebar.error("Não foi possível carregar usuários para login automático. Verifique o arquivo usuarios.json.")


# Carrega os lançamentos ao iniciar o app
carregar_lancamentos()
# if "lancamentos" not in st.session_state: # Esta linha é redundante após carregar_lancamentos()
#     st.session_state["lancamentos"] = []

# Inicializa a lista de categorias disponíveis para o usuário logado (será atualizada no login/auto-login)
# Movemos a lógica de preenchimento para o bloco de auto-login/login
if 'todas_categorias_receita' not in st.session_state:
     st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy() # Começa com as padrão se nada foi carregado


# Variáveis de estado para controlar a exibição dos "popups" - Mantido
if 'show_add_modal' not in st.session_state:
    st.session_state['show_add_modal'] = False
if 'show_edit_modal' not in st.session_state:
    st.session_state['show_edit_modal'] = False
if 'editar_indice' not in st.session_state:
     st.session_state['editar_indice'] = None
if 'editar_lancamento' not in st.session_state:
     st.session_state['editar_lancamento'] = None
if 'editar_usuario_index' not in st.session_state:
     st.session_state['editar_usuario_index'] = None
if 'editar_usuario_data' not in st.session_state:
     st.session_state['editar_usuario_data'] = None
if 'show_edit_user_modal' not in st.session_state: # Flag para modal de edição de usuário
    st.session_state['show_edit_user_modal'] = False
if 'confirm_delete_index' not in st.session_state: # Índice para confirmação de exclusão de lançamento
    st.session_state['confirm_delete_index'] = None
if 'show_confirm_delete_modal' not in st.session_state: # Flag para modal de confirmação de exclusão de lançamento
    st.session_state['show_confirm_delete_modal'] = False
if 'confirm_delete_user_index' not in st.session_state: # Índice para confirmação de exclusão de usuário
     st.session_state['confirm_delete_user_index'] = None
if 'show_confirm_delete_user_modal' not in st.session_state: # Flag para modal de confirmação de exclusão de usuário
     st.session_state['show_confirm_delete_user_modal'] = False


# Removida a função pagina_login()


# --- Funções para Renderizar os Formulários (mantidas) ---
# (render_add_lancamento_form, render_edit_lancamento_form, etc. - SEM MUDANÇAS NELAS)
# ... (Copie e cole as funções render_add_lancamento_form, render_edit_lancamento_form) ...
def render_add_lancamento_form():
    # A verificação de autenticação ainda é útil dentro das funções de conteúdo
    if not st.session_state.get('autenticado'):
        return

    with st.expander("Adicionar Novo Lançamento", expanded=True):
        st.subheader(f"Adicionar Lançamento para {st.session_state.get('usuario_atual_nome', 'seu usuário')}")

        with st.form(key="add_lancamento_form"):
            data_str = st.text_input("Data (DD/MM/AAAA)", key="add_lanc_data_form")
            descricao = st.text_input("Descrição", key="add_lanc_descricao_form")
            tipo = st.selectbox("Tipo de Lançamento", ["Receita", "Despesa"], key="add_lanc_tipo_form")

            categoria_placeholder = st.empty()
            categoria = ""

            if tipo == "Receita":
                categorias_disponiveis = st.session_state.get('todas_categorias_receita', CATEGORIAS_PADRAO_RECEITA)
                categoria = categoria_placeholder.selectbox(
                    "Categoria",
                    categorias_disponiveis,
                    key="add_lanc_categoria_receita_form"
                )

            valor = st.number_input("Valor", format="%.2f", min_value=0.0, key="add_lanc_valor_form")

            submit_button = st.form_submit_button("Adicionar Lançamento")

            if submit_button:
                if not data_str or not descricao or valor is None or (tipo == "Receita" and not categoria):
                    st.warning("Por favor, preencha todos os campos obrigatórios.")
                else:
                    try:
                        data_obj = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                        novo_lancamento = {
                            "Data": data_obj,
                            "Descrição": descricao,
                            "Categorias": categoria,
                            "Tipo de Lançamento": tipo,
                            "Valor": valor,
                            "user_email": st.session_state.get('usuario_atual_email') # Garante que usa o email do usuário logado
                        }
                        st.session_state["lancamentos"].append(novo_lancamento)
                        salvar_lancamentos()
                        st.success("Lançamento adicionado com sucesso!")
                        st.session_state['show_add_modal'] = False # Pode manter o modal aberto ou fechar
                        st.rerun()
                    except ValueError:
                        st.error("Formato de data inválido. Use DD/MM/AAAA.")

def render_edit_lancamento_form():
    if not st.session_state.get('autenticado') or st.session_state.get('editar_indice') is None:
        return

    indice = st.session_state["editar_indice"]
    try:
         lancamento_a_editar = st.session_state.get("lancamentos", [])[indice]
    except IndexError:
         st.error("Lançamento a ser editado não encontrado ou índice inválido.")
         st.session_state['editar_indice'] = None
         st.session_state['editar_lancamento'] = None
         st.session_state['show_edit_modal'] = False
         # st.rerun() # Evita rerun duplo se chamado em cascata
         return

    is_owner = lancamento_a_editar.get('user_email') == st.session_state.get('usuario_atual_email')
    is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'

    if not (is_owner or is_admin):
        st.error("Você não tem permissão para editar este lançamento.")
        st.session_state['editar_indice'] = None
        st.session_state['editar_lancamento'] = None
        st.session_state['show_edit_modal'] = False
        # st.rerun()
        return

    with st.expander("Editar Lançamento", expanded=True):
        st.subheader(f"Editar Lançamento")

        with st.form(key=f"edit_lancamento_form_{indice}"):
            lancamento = st.session_state["editar_lancamento"] # Use o lancamento salvo no state para pré-popular

            data_str = st.text_input(
                "Data (DD/MM/AAAA)",
                datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y"),
                key=f"edit_lanc_data_form_{indice}"
            )
            descricao = st.text_input("Descrição", lancamento.get("Descrição", ""), key=f"edit_lanc_descricao_form_{indice}")

            tipo_options = ["Receita", "Despesa"]
            try:
                default_tipo_index = tipo_options.index(lancamento.get("Tipo de Lançamento", "Receita"))
            except ValueError:
                default_tipo_index = 0

            tipo = st.selectbox(
                "Tipo de Lançamento",
                tipo_options,
                index=default_tipo_index,
                key=f"edit_lanc_tipo_form_{indice}",
            )

            categoria_placeholder = st.empty()
            categoria = ""

            if tipo == "Receita":
                 current_category = lancamento.get("Categorias", "")
                 categorias_disponiveis = st.session_state.get('todas_categorias_receita', CATEGORIAS_PADRAO_RECEITA)
                 try:
                     default_index_categoria = categorias_disponiveis.index(current_category)
                 except ValueError:
                     default_index_categoria = 0
                     if current_category and current_category != "Sem Categoria":
                         st.warning(f"A categoria salva '{current_category}' não está na lista de categorias de receita. Selecione uma nova.")

                 categoria = categoria_placeholder.selectbox(
                    "Categoria",
                    categorias_disponiveis,
                    index=default_index_categoria,
                    key=f"edit_lanc_categoria_receita_form_{indice}",
                )
            else:
                 categoria = lancamento.get("Categorias", "")

            valor = st.number_input(
                "Valor", value=lancamento.get("Valor", 0.0), format="%.2f", min_value=0.0, key=f"edit_lanc_valor_form_{indice}"
            )

            submit_button = st.form_submit_button("Salvar Edição")

            if submit_button:
                if not data_str or not descricao or valor is None or (tipo == "Receita" and not categoria):
                    st.warning("Por favor, preencha todos os campos obrigatórios (Data, Descrição, Valor e Categoria para Receita).")
                else:
                    try:
                        data_obj = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                        st.session_state["lancamentos"][indice] = {
                            "Data": data_obj,
                            "Descrição": descricao,
                            "Categorias": categoria,
                            "Tipo de Lançamento": tipo,
                            "Valor": valor,
                            "user_email": lancamento_a_editar.get('user_email')
                        }
                        salvar_lancamentos()
                        st.success("Lançamento editado com sucesso!")
                        st.session_state['editar_indice'] = None
                        st.session_state['editar_lancamento'] = None
                        st.session_state['show_edit_modal'] = False
                        st.rerun()
                    except ValueError:
                        st.error("Formato de data inválido. Use DD/MM/AAAA.")

        # Botão cancelar FORA do formulário
        if st.button("Cancelar Edição", key=f"cancel_edit_form_button_{indice}"):
            st.session_state['editar_indice'] = None
            st.session_state['editar_lancamento'] = None
            st.session_state['show_edit_modal'] = False
            st.rerun()

# ... (Copie e cole as funções exibir_resumo_central, exportar_lancamentos_para_excel, exportar_lancamentos_para_pdf, gerar_demonstracao_resultados_pdf) ...
def exibir_resumo_central():
    if not st.session_state.get('autenticado'): return # Verifica autenticação
    st.subheader("Resumo Financeiro")

    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        lancamentos_filtrados = st.session_state.get("lancamentos", [])
        st.info("Exibindo resumo de TODOS os lançamentos (Admin view).")
    else:
        usuario_email = st.session_state.get('usuario_atual_email')
        lancamentos_filtrados = [
            l for l in st.session_state.get("lancamentos", [])
            if l.get('user_email') == usuario_email
        ]
        st.info(f"Exibindo seus lançamentos, {st.session_state.get('usuario_atual_nome', 'usuário')} (Client view).")


    total_receitas = 0
    total_despesas = 0

    for lancamento in lancamentos_filtrados:
        if lancamento.get("Tipo de Lançamento") == "Receita":
            total_receitas += lancamento.get("Valor", 0)
        elif lancamento.get("Tipo de Lançamento") == "Despesa":
            total_despesas += lancamento.get("Valor", 0)

    total_geral = total_receitas - total_despesas

    st.markdown(
        f"<p style='color:blue;'>Receitas: R$ {total_receitas:.2f}</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:red;'>Despesas: R$ {total_despesas:.2f}</p>",
        unsafe_allow_html=True,
    )

    if total_geral >= 0:
        st.markdown(
            f"<p style='color:blue;'>Total: R$ {total_geral:.2f}</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<p style='color:red;'>Total: R$ {total_geral:.2f}</p>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

def exportar_lancamentos_para_excel(lancamentos_list):
    lancamentos_para_df = []
    for lancamento in lancamentos_list:
        lancamento_copy = lancamento.copy()
        if 'user_email' in lancamento_copy:
            del lancamento_copy['user_email']
        lancamentos_para_df.append(lancamento_copy)

    df = pd.DataFrame(lancamentos_para_df)

    if not df.empty:
        if 'Data' in df.columns:
             try:
                df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%d/%m/%Y')
             except Exception as e:
                 st.warning(f"Erro ao formatar a coluna 'Data' para exportação Excel: {e}")

        if 'Valor' in df.columns:
             try:
                df['Valor'] = df['Valor'].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))
             except Exception as e:
                 st.warning(f"Erro ao formatar a coluna 'Valor' para exportação Excel: {e}")

    output = io.BytesIO()
    try:
        df.to_excel(output, index=False, sheet_name='Lançamentos', engine='openpyxl')
        output.seek(0)
        return output
    except ImportError:
        st.error("A biblioteca 'openpyxl' é necessária para exportar para Excel. Instale com `pip install openpyxl`.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o arquivo Excel: {e}")
        return None

def exportar_lancamentos_para_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    try:
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_text = 'Arial_Unicode'
    except Exception as e:
         pdf.set_font("Arial", '', 12)
         font_for_text = 'Arial'

    pdf.set_font(font_for_text, 'B', 12)
    report_title = f"Relatório de Lançamentos - {usuario_nome}"
    pdf.cell(0, 10, report_title, 0, 1, 'C')
    pdf.ln(10)

    pdf.set_font(font_for_text, 'B', 10)
    col_widths = [25, 60, 35, 25, 30]
    headers = ["Data", "Descrição", "Categoria", "Tipo", "Valor"]

    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C', fill=False)
    pdf.ln()

    pdf.set_font(font_for_text, '', 10)
    for lancamento in lancamentos_list:
        try:
            data_formatada = datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            data_formatada = lancamento.get("Data", "Data Inválida")

        descricao = lancamento.get("Descrição", "")
        categoria = lancamento.get("Categorias", "") if lancamento.get("Categorias") else "Sem Categoria"
        tipo = lancamento.get("Tipo de Lançamento", "")
        valor_formatado = f"R$ {lancamento.get('Valor', 0.0):.2f}".replace('.', ',')

        pdf.cell(col_widths[0], 10, data_formatada, 1, 0, 'C')

        # MultiCell for description
        x = pdf.get_x()
        y = pdf.get_y()
        pdf.multi_cell(col_widths[1], 10, descricao, 1, 'L', fill=False)
        pdf.set_xy(x + col_widths[1], y)

        pdf.cell(col_widths[2], 10, categoria, 1, 0, 'C')
        pdf.cell(col_widths[3], 10, tipo, 1, 0, 'C')
        pdf.cell(col_widths[4], 10, valor_formatado, 1, 0, 'R')

        pdf.ln()

    pdf_output = pdf.output(dest='S')
    return io.BytesIO(pdf_output)

def gerar_demonstracao_resultados_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    try:
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_text = 'Arial_Unicode'
    except Exception as e:
         pdf.set_font("Arial", '', 12)
         font_for_text = 'Arial'

    pdf.set_font(font_for_text, 'B', 14)
    report_title = f"Demonstração de Resultados - {usuario_nome}"
    pdf.cell(0, 10, report_title, 0, 1, 'C')
    pdf.ln(10)

    receitas_por_categoria = {}
    despesas_por_categoria = {}
    total_receitas = 0
    total_despesas = 0

    for lancamento in lancamentos_list:
        tipo = lancamento.get("Tipo de Lançamento")
        categoria = lancamento.get("Categorias", "Sem Categoria") if lancamento.get("Categorias") else "Sem Categoria"
        valor = lancamento.get("Valor", 0.0)

        if tipo == "Receita":
            if categoria not in receitas_por_categoria:
                receitas_por_categoria[categoria] = 0
            receitas_por_categoria[categoria] += valor
            total_receitas += valor
        elif tipo == "Despesa":
            if categoria not in despesas_por_categoria:
                despesas_por_categoria[categoria] = 0
            despesas_por_categoria[categoria] += valor
            total_despesas += valor

    pdf.set_font(font_for_text, 'B', 12)
    pdf.cell(0, 10, "Receitas", 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10)
    for categoria in sorted(receitas_por_categoria.keys()):
        valor = receitas_por_categoria[categoria]
        pdf.cell(100, 7, f"- {categoria}", 0, 0, 'L')
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ','), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10)
    pdf.cell(100, 7, "Total Receitas", 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_receitas:.2f}".replace('.', ','), 0, 1, 'R')
    pdf.ln(10)

    pdf.set_font(font_for_text, 'B', 12)
    pdf.cell(0, 10, "Despesas", 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10)
    for categoria in sorted(despesas_por_categoria.keys()):
        valor = despesas_por_categoria[categoria]
        pdf.cell(100, 7, f"- {categoria}", 0, 0, 'L')
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ','), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10)
    pdf.cell(100, 7, "Total Despesas", 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_despesas:.2f}".replace('.', ','), 0, 1, 'R')
    pdf.ln(10)

    resultado_liquido = total_receitas - total_despesas
    pdf.set_font(font_for_text, 'B', 12)

    if resultado_liquido >= 0:
        pdf.set_text_color(0, 0, 255)
    else:
        pdf.set_text_color(255, 0, 0)

    pdf.cell(100, 10, "Resultado Líquido", 0, 0, 'L')
    pdf.cell(0, 10, f"R$ {resultado_liquido:.2f}".replace('.', ','), 0, 1, 'R')

    pdf.set_text_color(0, 0, 0)

    pdf_output = pdf.output(dest='S')
    return io.BytesIO(pdf_output)

def exibir_lancamentos():
    if not st.session_state.get('autenticado'): return # Verifica autenticação
    st.subheader("Lançamentos")

    lancamentos_para_exibir = []
    usuario_email = st.session_state.get('usuario_atual_email')

    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        lancamentos_para_exibir = st.session_state.get("lancamentos", [])
        st.info("Exibindo TODOS os lançamentos (Admin view).")
        filename_suffix = "admin"
        usuario_para_pdf_title = "Todos os Lançamentos"
    else:
        lancamentos_para_exibir = [
            l for l in st.session_state.get("lancamentos", [])
            if l.get('user_email') == usuario_email
        ]
        st.info(f"Exibindo seus lançamentos, {st.session_state.get('usuario_atual_nome', 'usuário')} (Client view).")
        filename_suffix = st.session_state.get('usuario_atual_nome', 'usuario').replace(" ", "_").lower()
        filename_suffix = ''.join(c for c in unicodedata.normalize('NFD', filename_suffix) if unicodedata.category(c) != 'Mn')
        filename_suffix = ''.join(e for e in filename_suffix if e.isalnum() or e == '_')

        usuario_para_pdf_title = st.session_state.get('usuario_atual_nome', 'Usuário')


    if not lancamentos_para_exibir:
        st.info("Nenhum lançamento encontrado para este usuário.")
        col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1])
        with col_excel:
             excel_buffer = exportar_lancamentos_para_excel([])
             if excel_buffer:
                st.download_button(
                    label="📥 Exportar para Excel (Vazio)",
                    data=excel_buffer,
                    file_name=f'lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        with col_pdf_lista:
             pdf_lista_buffer = exportar_lancamentos_para_pdf([], usuario_para_pdf_title)
             st.download_button(
                label="📄 Exportar Lista PDF (Vazia)",
                data=pdf_lista_buffer,
                file_name=f'lista_lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
                mime='application/pdf'
             )
        with col_pdf_dr:
             pdf_dr_buffer = gerar_demonstracao_resultados_pdf([], usuario_para_pdf_title)
             st.download_button(
                label="📊 Exportar DR PDF (Vazia)",
                data=pdf_dr_buffer,
                file_name=f'demonstracao_resultados_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
                mime='application/pdf'
             )
        st.markdown("---")
        return

    try:
        lancamentos_para_exibir.sort(key=lambda x: datetime.strptime(x.get('Data', '1900-01-01'), '%Y-%m-%d'), reverse=True)
    except ValueError:
        st.warning("Não foi possível ordenar os lançamentos por data devido a formato inválido.")

    col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1])

    with col_excel:
        excel_buffer = exportar_lancamentos_para_excel(lancamentos_para_exibir)
        if excel_buffer:
            st.download_button(
                label="📥 Exportar Lançamentos em Excel",
                data=excel_buffer,
                file_name=f'lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

    with col_pdf_lista:
         pdf_lista_buffer = exportar_lancamentos_para_pdf(lancamentos_para_exibir, usuario_para_pdf_title)
         st.download_button(
            label="📄 Exportar Lista PDF",
            data=pdf_lista_buffer,
            file_name=f'lista_lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
         )

    with col_pdf_dr:
         pdf_dr_buffer = gerar_demonstracao_resultados_pdf(lancamentos_para_exibir, usuario_para_pdf_title)
         st.download_button(
            label="📊 Exportar DR PDF",
            data=pdf_dr_buffer,
            file_name=f'demonstracao_resultados_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
         )

    st.markdown("---")

    st.subheader("Tabela de Lançamentos")

    lancamentos_para_df_tabela = []
    for lancamento in lancamentos_para_exibir:
        lancamento_copy = lancamento.copy()
        if st.session_state.get('tipo_usuario_atual') != 'Administrador' and 'user_email' in lancamento_copy:
             del lancamento_copy['user_email']
        lancamentos_para_df_tabela.append(lancamento_copy)

    df_tabela = pd.DataFrame(lancamentos_para_df_tabela)

    if not df_tabela.empty:
        if 'Data' in df_tabela.columns:
             try:
                 df_tabela['Data'] = pd.to_datetime(df_tabela['Data']).dt.strftime('%d/%m/%Y')
             except Exception:
                 pass

        if 'Valor' in df_tabela.columns:
             try:
                 df_tabela['Valor'] = df_tabela['Valor'].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))
             except Exception:
                 pass

        cols = df_tabela.columns.tolist()
        if 'user_email' in cols:
            cols.remove('user_email')
            cols.append('user_email')
            df_tabela = df_tabela[cols]

        df_tabela['Ações'] = "" # Coluna placeholder

        st.data_editor(
            df_tabela,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ações": st.column_config.Column(
                    "Ações",
                    width="medium"
                )
            },
            # data_editor não é usado para editar/excluir aqui, apenas visualização
            disabled=True, # Desabilita edição inline no data_editor
            key=f"lancamentos_editor_{filename_suffix}"
        )

        st.markdown("---")
        st.subheader("Ações nos Lançamentos")

        col_widths_actions = [25, 60, 35, 25, 30, 30]
        cols_actions = st.columns(col_widths_actions)

        # Usando um placeholder para os botões de ação para melhor controle
        # Um expander pode ser mais simples que colunas complexas abaixo do data_editor
        # Vamos usar expander/modal para ações de edição/exclusão acionadas por botões SIMPLES "Editar" / "Excluir" por linha

        # Uma alternativa mais limpa é listar os lançamentos com botões abaixo de cada um
        st.write("Selecione um lançamento abaixo para editar ou excluir:")
        for i, lancamento in enumerate(lancamentos_para_exibir):
             # Encontra o índice original para exclusão/edição na lista global
            try:
                original_index = next(idx for idx, l in enumerate(st.session_state.get('lancamentos', [])) if l == lancamento)
            except StopIteration:
                continue # Pula se não encontrar (não deveria acontecer)

            is_owner = lancamento.get('user_email') == st.session_state.get('usuario_atual_email')
            is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'

            if is_owner or is_admin:
                 col1, col2, col3 = st.columns([0.6, 0.2, 0.2]) # Colunas para Descrição, Editar, Excluir
                 col1.write(f"- {lancamento.get('Descrição', 'Sem Descrição')} ({lancamento.get('Tipo de Lançamento', '')}) R$ {lancamento.get('Valor', 0.0):.2f}".replace('.', ','))

                 if col2.button("✏️ Editar", key=f"btn_edit_lanc_{original_index}", help="Editar Lançamento"):
                      st.session_state['editar_indice'] = original_index
                      st.session_state['editar_lancamento'] = st.session_state.get("lancamentos", [])[original_index].copy()
                      st.session_state['show_edit_modal'] = True
                      st.session_state['show_add_modal'] = False
                      st.session_state['show_confirm_delete_modal'] = False
                      st.rerun()

                 if col3.button("🗑️ Excluir", key=f"btn_del_lanc_{original_index}", help="Excluir Lançamento", type="secondary"):
                      st.session_state['confirm_delete_index'] = original_index
                      st.session_state['show_confirm_delete_modal'] = True
                      st.session_state['show_edit_modal'] = False
                      st.session_state['show_add_modal'] = False
                      st.rerun()

        # --- Modal de Confirmação de Exclusão (Lançamento) ---
        if st.session_state.get('show_confirm_delete_modal', False):
             with st.expander("Confirmar Exclusão do Lançamento", expanded=True):
                 delete_index = st.session_state.get('confirm_delete_index')
                 # Verificar se o índice ainda é válido antes de tentar acessar
                 if delete_index is not None and 0 <= delete_index < len(st.session_state.get('lancamentos', [])):
                     lancamento_para_deletar = st.session_state['lancamentos'][delete_index]
                     st.warning(f"Tem certeza que deseja excluir o lançamento: '{lancamento_para_deletar.get('Descrição', 'Sem Descrição')}' de {f'R$ {lancamento_para_deletar.get('Valor', 0.0):.2f}'.replace('.', ',')}?")
                     col_confirm_del, col_cancel_del = st.columns(2)
                     if col_confirm_del.button("Sim, Excluir", key="confirm_delete_yes", type="secondary"):
                         st.session_state["lancamentos"].pop(delete_index)
                         salvar_lancamentos()
                         st.success("Lançamento excluído com sucesso!")
                         st.session_state['show_confirm_delete_modal'] = False
                         st.session_state['confirm_delete_index'] = None
                         st.rerun()
                     if col_cancel_del.button("Não, Cancelar", key="confirm_delete_no"):
                         st.session_state['show_confirm_delete_modal'] = False
                         st.session_state['confirm_delete_index'] = None
                         st.rerun()
                 else:
                      st.error("Erro: Lançamento a ser excluído não encontrado ou inválido.")
                      st.session_state['show_confirm_delete_modal'] = False
                      st.session_state['confirm_delete_index'] = None
                      # st.rerun() # Evita rerun se já ocorreu acima

def exibir_usuarios():
    if st.session_state.get('tipo_usuario_atual') != 'Administrador':
        st.warning("Acesso negado. Somente administradores podem gerenciar usuários.")
        return

    st.subheader("Gerenciar Usuários")

    with st.expander("Adicionar Novo Usuário", expanded=False):
        with st.form(key="add_usuario_form"):
            novo_nome = st.text_input("Nome do Usuário", key="add_user_nome")
            novo_email = st.text_input("E-mail", key="add_user_email")
            nova_senha = st.text_input("Senha", type="password", key="add_user_senha")
            novo_tipo = st.selectbox("Tipo", ["Cliente", "Administrador"], key="add_user_tipo")

            submit_usuario_button = st.form_submit_button("Adicionar Usuário")

            if submit_usuario_button:
                if not novo_nome or not novo_email or not nova_senha:
                    st.warning("Por favor, preencha Nome, E-mail e Senha para o novo usuário.")
                else:
                    emails_existentes = [u.get('Email') for u in st.session_state.get('usuarios', [])]
                    if novo_email in emails_existentes:
                        st.error(f"O e-mail '{novo_email}' já está cadastrado.")
                    else:
                        novo_usuario_data = {
                            "Nome": novo_nome,
                            "Email": novo_email,
                            "Senha": nova_senha, # **Aviso: Senha em texto plano!**
                            "Tipo": novo_tipo,
                            "categorias_receita": CATEGORIAS_PADRAO_RECEITA.copy()
                        }
                        st.session_state['usuarios'].append(novo_usuario_data)
                        salvar_usuarios()
                        st.success(f"Usuário '{novo_nome}' adicionado com sucesso!")
                        st.rerun()

    st.markdown("---")
    st.subheader("Lista de Usuários")

    usuarios_para_df = []
    for user in st.session_state.get('usuarios', []):
        user_copy = user.copy()
        if 'Senha' in user_copy:
            user_copy['Senha'] = '********'
        if 'categorias_receita' in user_copy:
             del user_copy['categorias_receita']
        usuarios_para_df.append(user_copy)

    df_usuarios = pd.DataFrame(usuarios_para_df)

    if df_usuarios.empty:
        st.info("Nenhum usuário cadastrado.")
    else:
        st.dataframe(df_usuarios, use_container_width=True, hide_index=True) # Exibe a tabela não editável

        st.markdown("---")
        st.subheader("Ações nos Usuários")

        # Lista os usuários com botões de ação
        for i, usuario in enumerate(st.session_state.get('usuarios', [])):
             col_user_info, col_user_actions = st.columns([0.8, 0.2]) # Coluna para info e outra para botões

             col_user_info.write(f"- **{usuario.get('Nome', 'Nome Desconhecido')}** ({usuario.get('Email', 'Email Desconhecido')}) - {usuario.get('Tipo', 'Tipo Desconhecido')}")

             col_editar_user, col_excluir_user = col_user_actions.columns(2)

             if col_editar_user.button("✏️ Editar", key=f"btn_edit_user_{i}", help="Editar Usuário"):
                 st.session_state['editar_usuario_index'] = i
                 st.session_state['editar_usuario_data'] = st.session_state['usuarios'][i].copy()
                 st.session_state['show_edit_user_modal'] = True
                 st.session_state['show_confirm_delete_user_modal'] = False
                 st.rerun()

             if col_excluir_user.button("🗑️ Excluir", key=f"btn_del_user_{i}", help="Excluir Usuário", type="secondary"):
                  st.session_state['confirm_delete_user_index'] = i
                  st.session_state['show_confirm_delete_user_modal'] = True
                  st.session_state['show_edit_user_modal'] = False
                  st.rerun()

        # --- Modal de Edição de Usuário ---
        if st.session_state.get('show_edit_user_modal', False):
             editar_index = st.session_state.get('editar_usuario_index')
             usuario_data = st.session_state.get('editar_usuario_data')

             if editar_index is not None and usuario_data:
                  with st.expander("Editar Usuário", expanded=True):
                       st.subheader(f"Editar Usuário: {usuario_data.get('Nome', 'Nome Desconhecido')}")
                       with st.form(key=f"edit_usuario_form_{editar_index}"):
                            st.text_input("E-mail (Não Editável)", value=usuario_data.get('Email', ''), disabled=True, key=f"edit_user_email_disabled_{editar_index}")
                            edited_nome = st.text_input("Nome", value=usuario_data.get('Nome', ''), key=f"edit_user_nome_{editar_index}")
                            edited_senha = st.text_input("Nova Senha (Deixe em branco para não alterar)", type="password", key=f"edit_user_senha_{editar_index}")
                            tipo_options = ["Cliente", "Administrador"]
                            try:
                                default_tipo_index = tipo_options.index(usuario_data.get('Tipo', 'Cliente'))
                            except ValueError:
                                default_tipo_index = 0
                            edited_tipo = st.selectbox("Tipo", tipo_options, index=default_tipo_index, key=f"edit_user_tipo_{editar_index}")

                            st.markdown("#### Categorias de Receita (exclusivas deste usuário)")
                            categorias_atuais_usuario = usuario_data.get('categorias_receita', [])
                            todas_opcoes_cat = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + categorias_atuais_usuario))
                            selected_categorias_receita = st.multiselect(
                                "Selecione as categorias de Receita para este usuário:",
                                todas_opcoes_cat,
                                default=categorias_atuais_usuario,
                                key=f"multiselect_user_cats_{editar_index}"
                            )
                            nova_categoria_input = st.text_input("Adicionar nova categoria de receita:", key=f"new_cat_input_{editar_index}")

                            submit_edit_usuario_button = st.form_submit_button("Salvar Alterações do Usuário")

                            if submit_edit_usuario_button:
                                if not edited_nome or not edited_tipo:
                                    st.warning("Nome e Tipo são obrigatórios.")
                                else:
                                     try:
                                         real_index = next(i for i, user in enumerate(st.session_state.get('usuarios', [])) if user.get('Email') == usuario_data.get('Email'))
                                     except StopIteration:
                                         st.error("Erro interno: Usuário não encontrado na lista principal durante a edição.")
                                         st.session_state['show_edit_user_modal'] = False
                                         st.session_state['editar_usuario_index'] = None
                                         st.session_state['editar_usuario_data'] = None
                                         st.rerun()
                                         return

                                     # Cuidado para não remover o último administrador
                                     if st.session_state['usuarios'][real_index].get('Tipo') == 'Administrador' and edited_tipo != 'Administrador':
                                         admins_count_before = len([u for i, u in enumerate(st.session_state['usuarios']) if u.get('Tipo') == 'Administrador' and i != real_index])
                                         if admins_count_before == 0:
                                             st.warning("Não é possível alterar o tipo do último usuário administrador para 'Cliente'. Crie outro administrador primeiro.")
                                             st.session_state['show_edit_user_modal'] = False
                                             st.session_state['editar_usuario_index'] = None
                                             st.session_state['editar_usuario_data'] = None
                                             st.rerun()
                                             return

                                     st.session_state['usuarios'][real_index]['Nome'] = edited_nome
                                     st.session_state['usuarios'][real_index]['Tipo'] = edited_tipo
                                     if edited_senha:
                                          st.session_state['usuarios'][real_index]['Senha'] = edited_senha # **Aviso!**
                                     # Processar nova categoria antes de salvar as selecionadas
                                     if nova_categoria_input:
                                         nova_categoria_input_stripped = nova_categoria_input.strip()
                                         if nova_categoria_input_stripped and nova_categoria_input_stripped not in selected_categorias_receita:
                                             selected_categorias_receita.append(nova_categoria_input_stripped)
                                             st.info(f"Categoria '{nova_categoria_input_stripped}' adicionada à lista. Salve novamente para confirmar.") # Informa que precisa salvar de novo
                                             # Não salva ainda, espera o segundo submit ou usa callback se fora do form
                                             # Para simplicidade com form, o usuário precisaria clicar "Salvar Alterações" de novo.
                                             # Melhor abordagem: adicionar categoria fora do form ou com callback.
                                             # Neste caso, vamos apenas atualizar a lista 'selected_categorias_receita' no estado temporário
                                             # para que apareça no multiselect se o usuário não sair do modal.
                                             # A categoria só será salva de fato quando o botão "Salvar Alterações" for clicado
                                             # DEPOIS que a nova categoria apareceu e foi (re)selecionada no multiselect.
                                             # Isso é um pouco confuso na UX. Uma abordagem melhor seria um botão "Adicionar"
                                             # separado que atualiza o multiselect e o estado temporário imediatamente.
                                             # Para manter a lógica dentro do form, vamos apenas adicionar à lista que será salva.
                                             st.session_state[f"multiselect_user_cats_{editar_index}"] = selected_categorias_receita # Tenta atualizar o estado do widget
                                             st.rerun() # Força rerender para mostrar a nova categoria selecionável
                                             return # Sai do submit para a nova categoria ser processada

                                     st.session_state['usuarios'][real_index]['categorias_receita'] = selected_categorias_receita

                                     salvar_usuarios()
                                     st.success("Dados do usuário atualizados com sucesso!")
                                     if real_index == st.session_state.get('usuario_atual_index'):
                                         st.session_state['usuario_atual_nome'] = edited_nome
                                         st.session_state['tipo_usuario_atual'] = edited_tipo
                                         usuario_categorias_receita = st.session_state['usuarios'][real_index].get('categorias_receita', [])
                                         todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + usuario_categorias_receita))
                                         st.session_state['todas_categorias_receita'] = todas_unicas_receita

                                     st.session_state['show_edit_user_modal'] = False
                                     st.session_state['editar_usuario_index'] = None
                                     st.session_state['editar_usuario_data'] = None
                                     st.rerun()

                       # Botão Cancelar Edição FORA do formulário
                       if st.button("Cancelar Edição", key=f"cancel_edit_user_form_{editar_index}"):
                            st.session_state['show_edit_user_modal'] = False
                            st.session_state['editar_usuario_index'] = None
                            st.session_state['editar_usuario_data'] = None
                            st.rerun()

        # --- Modal de Confirmação de Exclusão (Usuário) ---
        if st.session_state.get('show_confirm_delete_user_modal', False):
             delete_index = st.session_state.get('confirm_delete_user_index')
             if delete_index is not None and 0 <= delete_index < len(st.session_state.get('usuarios', [])):
                 usuario_para_deletar = st.session_state['usuarios'][delete_index]
                 st.warning(f"Tem certeza que deseja excluir o usuário: '{usuario_para_deletar.get('Nome', 'Nome Desconhecido')}' ({usuario_para_deletar.get('Email', 'Email Desconhecido')})?")

                 admins_count = len([u for u in st.session_state.get('usuarios', []) if u.get('Tipo') == 'Administrador'])
                 if usuario_para_deletar.get('Tipo') == 'Administrador' and admins_count == 1:
                     st.error("Não é possível excluir o último usuário administrador.")
                     if st.button("Fechar", key="cancel_delete_user_last_admin"):
                         st.session_state['show_confirm_delete_user_modal'] = False
                         st.session_state['confirm_delete_user_index'] = None
                         st.rerun()
                     return

                 col_confirm_del_user, col_cancel_del_user = st.columns(2)
                 if col_confirm_del_user.button("Sim, Excluir Usuário", key="confirm_delete_user_yes", type="secondary"):
                     st.session_state['usuarios'].pop(delete_index)
                     salvar_usuarios()
                     st.success("Usuário excluído com sucesso!")
                     st.session_state['show_confirm_delete_user_modal'] = False
                     st.session_state['confirm_delete_user_index'] = None
                     if delete_index == st.session_state.get('usuario_atual_index'):
                          st.session_state['autenticado'] = False
                          st.session_state['usuario_atual_email'] = None
                          st.session_state['usuario_atual_nome'] = None
                          st.session_state['tipo_usuario_atual'] = None
                          st.session_state['usuario_atual_index'] = None
                          st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy()
                     st.rerun()
                 if col_cancel_del_user.button("Não, Cancelar", key="confirm_delete_user_no"):
                     st.session_state['show_confirm_delete_user_modal'] = False
                     st.session_state['confirm_delete_user_index'] = None
                     st.rerun()
             else:
                 st.error("Erro: Usuário a ser excluído não encontrado.")
                 st.session_state['show_confirm_delete_user_modal'] = False
                 st.session_state['confirm_delete_user_index'] = None


def gerenciar_categorias():
     if st.session_state.get('tipo_usuario_atual') != 'Administrador':
        st.warning("Acesso negado. Somente administradores podem gerenciar categorias padrão.")
        return

     st.subheader("Gerenciar Categorias de Receita por Usuário")
     st.info("Cada usuário pode ter categorias de receita personalizadas. As categorias padrão (Serviços, Vendas) sempre estarão disponíveis.")

     user_emails = [u.get('Email') for u in st.session_state.get('usuarios', [])]
     selected_user_email = st.selectbox("Selecione o usuário para gerenciar categorias:", user_emails, key="select_user_for_categories")

     if selected_user_email:
          user_index_for_cat = next((i for i, u in enumerate(st.session_state.get('usuarios', [])) if u.get('Email') == selected_user_email), None)

          if user_index_for_cat is not None:
               user = st.session_state['usuarios'][user_index_for_cat]
               st.write(f"Categorias de Receita para **{user.get('Nome', 'Usuário Desconhecido')}**:")

               categorias_atuais = user.get('categorias_receita', [])
               todas_opcoes_cat = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + categorias_atuais))

               with st.form(key=f"edit_user_categories_form_{user_index_for_cat}"):
                    edited_categorias = st.multiselect(
                        "Selecione as categorias de Receita:",
                        todas_opcoes_cat,
                        default=categorias_atuais,
                        key=f"multiselect_user_cats_{user_index_for_cat}"
                    )

                    nova_categoria_usuario_input = st.text_input("Adicionar nova categoria para este usuário:", key=f"new_cat_user_input_{user_index_for_cat}")

                    save_user_categories_button = st.form_submit_button("Salvar Categorias para este Usuário")

                    if save_user_categories_button:
                         # Processar nova categoria antes de salvar as selecionadas
                         if nova_categoria_usuario_input:
                             nova_categoria_usuario_stripped = nova_categoria_usuario_input.strip()
                             if nova_categoria_usuario_stripped and nova_categoria_usuario_stripped not in edited_categorias:
                                  # Adiciona a nova categoria à lista que será salva
                                  edited_categorias.append(nova_categoria_usuario_stripped)
                                  st.info(f"Categoria '{nova_categoria_usuario_stripped}' adicionada. Salve novamente para confirmar.")
                                  # Não salva ainda, espera o segundo submit ou usa callback se fora do form
                                  # Para manter a lógica dentro do form, atualizamos a lista aqui antes de salvar.
                                  # Para que ela apareça no multiselect, uma rerender pode ser necessária.
                                  # st.session_state[f"multiselect_user_cats_{user_index_for_cat}"] = edited_categorias # Tenta atualizar o state key
                                  # st.rerun() # Pode precisar disso para a UX fluir

                         # Remove categorias padrão da lista salva do usuário, se desejar que o JSON contenha apenas as extras.
                         # Ou mantém todas, o que simplifica. Vamos manter todas selecionadas.
                         # categorias_para_salvar = [cat for cat in edited_categorias if cat not in CATEGORIAS_PADRAO_RECEITA] # Exemplo se quisesse remover padrão
                         # categorias_para_salvar = edited_categorias # Mantém todas selecionadas

                         st.session_state['usuarios'][user_index_for_cat]['categorias_receita'] = edited_categorias
                         salvar_usuarios()
                         st.success(f"Categorias de receita para '{user.get('Nome')}' salvas com sucesso!")
                         if user_index_for_cat == st.session_state.get('usuario_atual_index'):
                              usuario_categorias_receita = st.session_state['usuarios'][user_index_for_cat].get('categorias_receita', [])
                              todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + usuario_categorias_receita))
                              st.session_state['todas_categorias_receita'] = todas_unicas_receita
                         st.rerun()


# --- Layout Principal ---
def main():
    st.sidebar.title("Navegação")

    # A página principal agora sempre começa tentando exibir o conteúdo autenticado
    # O auto-login no início do script já definiu st.session_state['autenticado']
    # e os dados do usuário, se houver usuários disponíveis.

    if st.session_state.get('autenticado'):
        # Adiciona o nome do usuário logado na sidebar
        st.sidebar.write(f"Bem-vindo(a), **{st.session_state.get('usuario_atual_nome', 'Usuário')}**!")
        # Adiciona o tipo de usuário logado na sidebar
        st.sidebar.write(f"Tipo: **{st.session_state.get('tipo_usuario_atual', 'Cliente')}**")

        # Botões de navegação
        if st.sidebar.button("Dashboard", key="nav_dashboard"):
            st.session_state['pagina_atual'] = 'dashboard'
            # Limpa flags de modais ao navegar
            st.session_state['show_add_modal'] = False
            st.session_state['show_edit_modal'] = False
            st.session_state['show_edit_user_modal'] = False
            st.session_state['show_confirm_delete_user_modal'] = False
            st.session_state['confirm_delete_index'] = None
            st.session_state['show_confirm_delete_modal'] = False
            st.rerun()

        if st.sidebar.button("Lançamentos", key="nav_lancamentos"):
            st.session_state['pagina_atual'] = 'lancamentos'
            # Limpa flags de modais ao navegar
            st.session_state['show_add_modal'] = False
            st.session_state['show_edit_modal'] = False
            st.session_state['show_edit_user_modal'] = False
            st.session_state['show_confirm_delete_user_modal'] = False
            st.session_state['confirm_delete_index'] = None
            st.session_state['show_confirm_delete_modal'] = False
            st.rerun()

        # Apenas administradores veem a página de usuários e categorias
        if st.session_state.get('tipo_usuario_atual') == 'Administrador':
            if st.sidebar.button("Gerenciar Usuários", key="nav_usuarios"):
                st.session_state['pagina_atual'] = 'usuarios'
                # Limpa flags de modais ao navegar
                st.session_state['show_add_modal'] = False
                st.session_state['show_edit_modal'] = False
                st.session_state['show_edit_user_modal'] = False
                st.session_state['show_confirm_delete_user_modal'] = False
                st.session_state['confirm_delete_index'] = None
                st.session_state['show_confirm_delete_modal'] = False
                st.rerun()

            if st.sidebar.button("Gerenciar Categorias", key="nav_categorias"):
                st.session_state['pagina_atual'] = 'categorias'
                 # Limpa flags de modais ao navegar
                st.session_state['show_add_modal'] = False
                st.session_state['show_edit_modal'] = False
                st.session_state['show_edit_user_modal'] = False
                st.session_state['show_confirm_delete_user_modal'] = False
                st.session_state['confirm_delete_index'] = None
                st.session_state['show_confirm_delete_modal'] = False
                st.rerun()

        # Botão de Logout
        if st.sidebar.button("Sair", key="nav_logout"):
            st.session_state['autenticado'] = False
            st.session_state['usuario_atual_email'] = None
            st.session_state['usuario_atual_nome'] = None
            st.session_state['tipo_usuario_atual'] = None
            st.session_state['usuario_atual_index'] = None
            st.session_state['pagina_atual'] = 'dashboard' # Volta para o dashboard (que não exigirá login agora, mas estará vazio)
            # Limpa flags de modais ao sair
            st.session_state['show_add_modal'] = False
            st.session_state['show_edit_modal'] = False
            st.session_state['show_edit_user_modal'] = False
            st.session_state['show_confirm_delete_user_modal'] = False
            st.session_state['confirm_delete_index'] = None
            st.session_state['show_confirm_delete_modal'] = False
            st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy()
            st.rerun()

        st.sidebar.markdown("---")


        # --- Renderização da Página Principal ---
        if st.session_state.get('pagina_atual') == 'dashboard':
            st.title("Dashboard Financeiro")
            exibir_resumo_central()
            # Renderiza modais de edição/exclusão se estiverem ativos
            if st.session_state.get('show_edit_modal', False): render_edit_lancamento_form()
            if st.session_state.get('show_confirm_delete_modal', False): exibir_lancamentos() # Exibe o modal dentro da função de exibição
            else: render_add_lancamento_form() # Renderiza adicionar apenas se modal de delete não estiver ativo
            exibir_lancamentos()


        elif st.session_state.get('pagina_atual') == 'lancamentos':
            st.title("Gerenciar Lançamentos")
            # Renderiza modais de edição/exclusão se estiverem ativos
            if st.session_state.get('show_edit_modal', False): render_edit_lancamento_form()
            if st.session_state.get('show_confirm_delete_modal', False): exibir_lancamentos() # Exibe o modal dentro da função de exibição
            else: render_add_lancamento_form() # Renderiza adicionar apenas se modal de delete não estiver ativo
            exibir_lancamentos()


        elif st.session_state.get('pagina_atual') == 'usuarios':
            st.title("Administração de Usuários")
            # Renderiza modais de edição/exclusão de usuário se estiverem ativos
            if st.session_state.get('show_edit_user_modal', False): exibir_usuarios() # Modal exibido dentro da função
            elif st.session_state.get('show_confirm_delete_user_modal', False): exibir_usuarios() # Modal exibido dentro da função
            else: exibir_usuarios() # Exibe a lista principal e formulário de adicionar

        elif st.session_state.get('pagina_atual') == 'categorias':
             st.title("Administração de Categorias")
             gerenciar_categorias()

    else:
         # Caso em que st.session_state.get('autenticado') é False após o auto-login
         # Isso só acontecerá se não houver usuários carregados (lista vazia ou erro)
         st.title("Erro na Inicialização")
         st.error("Não foi possível carregar usuários iniciais.")
         st.info("Por favor, verifique o arquivo `usuarios.json` ou adicione usuários iniciais no código se ele não existir.")


if __name__ == "__main__":
    main()
