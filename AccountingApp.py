import streamlit as st
from datetime import datetime
import json
import os
import pandas as pd
import io
from fpdf import FPDF
# Import necessary components from streamlit-aggrid
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

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
# CATEGORIAS_FILE = "categorias.json" # Não precisamos mais deste arquivo

# --- Funções de Carregamento e Salvamento ---

def salvar_usuarios():
    with open(USUARIOS_FILE, "w") as f:
        json.dump(st.session_state.get('usuarios', []), f)

def carregar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        try:
            with open(USUARIOS_FILE, "r") as f:
                content = f.read()
                if content:
                    usuarios = json.loads(content)
                    # Garante que cada usuário tem a lista de categorias (originalmente só tinha receita)
                    for usuario in usuarios:
                         if 'categorias_receita' not in usuario:
                              usuario['categorias_receita'] = []
                         # Mantendo a estrutura original do seu código que não tinha categorias de despesa no usuário
                    st.session_state['usuarios'] = usuarios
                else:
                    st.session_state['usuarios'] = []
        except json.JSONDecodeError:
            st.error("Erro ao decodificar o arquivo de usuários. Criando um novo.")
            st.session_state['usuarios'] = []
            salvar_usuarios()
    else:
        st.session_state['usuarios'] = []


def salvar_lancamentos():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.get("lancamentos", []), f)

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


# --- Inicialização de Estado ---
if 'usuarios' not in st.session_state:
    carregar_usuarios()
if 'pagina_atual' not in st.session_state:
    st.session_state['pagina_atual'] = 'dashboard'
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'usuario_atual_email' not in st.session_state:
    st.session_state['usuario_atual_email'] = None
if 'usuario_atual_nome' not in st.session_state:
    st.session_state['usuario_atual_nome'] = None
if 'tipo_usuario_atual' not in st.session_state:
    st.session_state['tipo_usuario_atual'] = None
if 'usuario_atual_index' not in st.session_state:
     st.session_state['usuario_atual_index'] = None


# Variáveis de estado para controlar a exibição dos "popups"
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

# Adicionadas variáveis de estado para gerenciar ações solicitadas e confirmação
if 'edit_requested_index' not in st.session_state:
    st.session_state['edit_requested_index'] = None
if 'awaiting_delete_confirmation_index' not in st.session_state:
     st.session_state['awaiting_delete_confirmation_index'] = None


# Carrega os lançamentos ao iniciar o app
carregar_lancamentos()
if "lancamentos" not in st.session_state:
    st.session_state["lancamentos"] = []

# Define as categorias padrão de receita (conforme seu código original)
CATEGORIAS_PADRAO_RECEITA = ["Serviços","Vendas"]
# O código original não tinha categorias padrão de despesa ou gestão delas por usuário.
# A Demonstração de Resultados agrupará despesas pelo campo 'Categorias' existente,
# mas sem gestão específica de categorias de despesa no UI.

# Inicializa a lista de categorias disponíveis para o usuário logado (será atualizada no login)
if 'todas_categorias_receita' not in st.session_state:
     st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy() # Começa com as padrão
# Mantendo a estrutura original que não tinha 'todas_categorias_despesa' no estado

def excluir_usuario(index):
    # Antes de excluir o usuário, podemos verificar se há lançamentos associados
    # e decidir o que fazer (excluir lançamentos, reatribuir, etc.).
    # Por simplicidade, vamos apenas excluir o usuário por enquanto.
    del st.session_state['usuarios'][index]
    salvar_usuarios()
    st.success("Usuário excluído com sucesso!")
    st.rerun()


def pagina_login():
    st.title("Login")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    login_button = st.button("Entrar")

    if login_button:
        for i, usuario in enumerate(st.session_state.get('usuarios', [])):
            if usuario.get('Email') == email and usuario.get('Senha') == senha:
                st.session_state['autenticado'] = True
                st.session_state['usuario_atual_email'] = usuario.get('Email')
                st.session_state['usuario_atual_nome'] = usuario.get('Nome')
                st.session_state['tipo_usuario_atual'] = usuario.get('Tipo')
                st.session_state['usuario_atual_index'] = i # Guarda o índice do usuário logado

                # Carrega as categorias personalizadas de receita do usuário logado e combina com as padrão (conforme original)
                usuario_categorias_receita = usuario.get('categorias_receita', [])
                todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + usuario_categorias_receita))
                st.session_state['todas_categorias_receita'] = todas_unicas_receita

                # Não adiciona lógica para categorias de despesa no login, mantendo o original

                st.success(f"Login realizado com sucesso, {st.session_state['usuario_atual_nome']}!")
                st.rerun()
                return

        st.error("E-mail ou senha incorretos.")

# --- Funções para Renderizar os Formulários (agora na área principal) ---

def render_add_lancamento_form():
    if not st.session_state.get('autenticado'):
        return

    with st.expander("Adicionar Novo Lançamento", expanded=True):
        st.subheader(f"Adicionar Lançamento para {st.session_state.get('usuario_atual_nome', 'seu usuário')}")

        # O formulário contém os campos e o botão de submissão
        with st.form(key="add_lancamento_form"):
            data_str = st.text_input("Data (DD/MM/AAAA)", key="add_lanc_data_form")
            descricao = st.text_input("Descrição", key="add_lanc_descricao_form")
            # Captura o tipo de lançamento selecionado primeiro
            tipo = st.selectbox("Tipo de Lançamento", ["Receita", "Despesa"], key="add_lanc_tipo_form")

            # Cria um placeholder para a Categoria
            categoria_placeholder = st.empty()

            categorias = "" # Inicializa a variável de categoria
            # Só exibe o campo Categoria dentro do placeholder se o tipo for Receita (conforme original)
            if tipo == "Receita":
                # Usa a lista combinada de categorias de receita do usuário logado
                categorias_disponiveis = st.session_state.get('todas_categorias_receita', CATEGORIAS_PADRAO_RECEITA)
                categorias = categoria_placeholder.selectbox(
                    "Categoria",
                    categorias_disponiveis,
                    key="add_lanc_categoria_receita_form"
                )
            # Se o tipo não for Receita, o placeholder permanece vazio, e 'categorias' continua ""
            # Seu código original não tinha seleção de categoria para Despesa aqui.

            valor = st.number_input("Valor", format="%.2f", min_value=0.0, key="add_lanc_valor_form")

            # Botão de submissão DENTRO do formulário
            submit_button = st.form_submit_button("Adicionar Lançamento")

            if submit_button:
                # Validação de categoria apenas para Receita (conforme original)
                if not data_str or not descricao or valor is None or (tipo == "Receita" and not categorias):
                    st.warning("Por favor, preencha todos os campos obrigatórios.")
                else:
                    try:
                        data_obj = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                        novo_lancamento = {
                            "Data": data_obj,
                            "Descrição": descricao,
                            "Categorias": categorias, # Salva a categoria (será vazia se não for Receita no original)
                            "Tipo de Lançamento": tipo,
                            "Valor": valor,
                            "user_email": st.session_state['usuario_atual_email']
                        }
                        st.session_state["lancamentos"].append(novo_lancamento)
                        salvar_lancamentos()
                        st.success("Lançamento adicionado com sucesso!")
                        st.session_state['show_add_modal'] = False
                        st.rerun()
                    except ValueError:
                        st.error("Formato de data inválido. Use DD/MM/AAAA.")

        # Botão cancelar FORA do formulário
        if st.button("Cancelar", key="cancel_add_form_button"):
             st.session_state['show_add_modal'] = False
             st.rerun()


def render_edit_lancamento_form():
    if not st.session_state.get('autenticado') or st.session_state.get('editar_indice') is None:
        return

    indice = st.session_state["editar_indice"]
    if indice is None or indice >= len(st.session_state.get('lancamentos', [])):
        st.error("Lançamento a ser editado não encontrado ou inválido.")
        st.session_state['editar_indice'] = None
        st.session_state['editar_lancamento'] = None
        st.session_state['show_edit_modal'] = False
        st.rerun()
        return


    lancamento_a_editar = st.session_state.get("lancamentos", [])[indice]


    is_owner = lancamento_a_editar.get('user_email') == st.session_state.get('usuario_atual_email')
    is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'

    if not (is_owner or is_admin):
        st.error("Você não tem permissão para editar este lançamento.")
        st.session_state['editar_indice'] = None
        st.session_state['editar_lancamento'] = None
        st.session_state['show_edit_modal'] = False
        st.rerun()
        return

    with st.expander("Editar Lançamento", expanded=True):
        st.subheader(f"Editar Lançamento")

        # O formulário contém os campos e o botão de submissão
        with st.form(key=f"edit_lancamento_form_{indice}"):
            lancamento = st.session_state["editar_lancamento"]

            data_str = st.text_input(
                "Data (DD/MM/AAAA)",
                datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y"),
                key=f"edit_lanc_data_form_{indice}"
            )
            descricao = st.text_input("Descrição", lancamento.get("Descrição", ""), key=f"edit_lanc_descricao_form_{indice}")
            # Captura o tipo de lançamento selecionado primeiro
            tipo = st.selectbox(
                "Tipo de Lançamento",
                ["Receita", "Despesa"],
                index=["Receita", "Despesa"].index(lancamento.get("Tipo de Lançamento", "Receita")),
                key=f"edit_lanc_tipo_form_{indice}",
            )

            # Cria um placeholder para a Categoria
            categoria_placeholder = st.empty()

            categoria = "" # Inicializa a variável de categoria
            # Só exibe o campo Categoria dentro do placeholder se o tipo for Receita (conforme original)
            if tipo == "Receita":
                 # Encontra o índice da categoria atual na lista combinada do usuário logado
                 current_category = lancamento.get("Categorias", "")
                 # Usa a lista combinada de categorias do usuário logado para o selectbox
                 categorias_disponiveis = st.session_state.get('todas_categorias_receita', CATEGORIAS_PADRAO_RECEITA)

                 try:
                     default_index = categorias_disponiveis.index(current_category)
                 except ValueError:
                     # Se a categoria salva não estiver na lista atual, use a primeira opção
                     default_index = 0

                 categoria = categoria_placeholder.selectbox(
                    "Categoria",
                    categorias_disponiveis,
                    index=default_index,
                    key=f"edit_lanc_categoria_receita_form_{indice}",
                )
            # Seu código original não tinha seleção de categoria para Despesa na edição.
            # A Demonstração de Resultados usará o que estiver no campo 'Categorias' para Despesas,
            # mesmo que não haja um selectbox para definir isso na UI original.


            valor = st.number_input(
                "Valor", value=lancamento.get("Valor", 0.0), format="%.2f", min_value=0.0, key=f"edit_lanc_valor_form_{indice}"
            )

            # Botão de submissão DENTRO do formulário
            submit_button = st.form_submit_button("Salvar Edição")

            if submit_button:
                 # Validação de categoria apenas para Receita (conforme original)
                if not data_str or not descricao or valor is None or (tipo == "Receita" and not categoria):
                    st.warning("Por favor, preencha todos os campos obrigatórios.")
                else:
                    try:
                        data_obj = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                        st.session_state["lancamentos"][indice] = {
                            "Data": data_obj,
                            "Descrição": descricao,
                            "Categorias": categoria, # Salva a categoria (será vazia se não for Receita no original)
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


def exibir_resumo_central():
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

# Função para exportar lançamentos para Excel (mantida a original)
def exportar_lancamentos_para_excel(lancamentos_list):
    lancamentos_para_df = []
    for lancamento in lancamentos_list:
        lancamento_copy = lancamento.copy()
        if 'user_email' in lancamento_copy: # Mantendo a remoção do user_email para o Excel conforme original
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
                # Mantendo a formatação original R$ X,XX
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

# Função para exportar lançamentos para PDF (lista detalhada) - CORRIGIDA NA VERSÃO ANTERIOR
def exportar_lancamentos_para_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos. Se não encontrar, usa Arial padrão.
    # Certifique-se de ter um arquivo .ttf (como Arial.ttf) no mesmo diretório do seu script.
    # Para Streamlit Cloud, o arquivo .ttf precisa estar no mesmo diretório do script.
    try:
        # Assumindo que 'Arial_Unicode.ttf' está no mesmo diretório do script
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_table = 'Arial_Unicode'
    except Exception as e:
         # st.warning(f"Erro ao carregar fonte personalizada para PDF: {e}. Usando fonte padrão.") # Mantendo o aviso na console
         pdf.set_font("Arial", '', 12)
         font_for_table = 'Arial'


    pdf.set_font("Arial", 'B', 12) # Use negrito da fonte padrão para o título (conforme original)
    report_title = f"Relatório de Lançamentos - {usuario_nome}"
    # O encode/decode aqui é para lidar com caracteres especiais no título, mantendo o original
    pdf.cell(0, 10, report_title.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')
    pdf.ln(10)

    # Usa a fonte com suporte a acentos (se carregada) ou a padrão para os cabeçalhos e dados da tabela
    pdf.set_font(font_for_table, 'B', 10) # Cabeçalhos em negrito
    col_widths = [20, 50, 30, 20, 20]
    headers = ["Data", "Descrição", "Categoria", "Tipo", "Valor"]

    for i, header in enumerate(headers):
        # O encode/decode aqui é para lidar com caracteres especiais nos cabeçalhos
        pdf.cell(col_widths[i], 10, header.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C', fill=False)
    pdf.ln()

    pdf.set_font(font_for_table, '', 10) # Dados da tabela em fonte normal
    for lancamento in lancamentos_list:
        try:
            data_formatada = datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            data_formatada = lancamento.get("Data", "Data Inválida")

        descricao = lancamento.get("Descrição", "")
        categoria = lancamento.get("Categorias", "")
        tipo = lancamento.get("Tipo de Lançamento", "")
        valor_formatado = f"R$ {lancamento.get('Valor', 0.0):.2f}".replace('.', ',')

        # O encode/decode aqui é para lidar com caracteres especiais nos dados
        pdf.cell(col_widths[0], 10, data_formatada.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        pdf.cell(col_widths[1], 10, descricao.encode('latin1', 'replace').decode('latin1'), 1, 0, 'L')
        # Verifica se categoria não é vazia antes de tentar encodar/decodar
        pdf.cell(col_widths[2], 10, categoria.encode('latin1', 'replace').decode('latin1') if categoria else "", 1, 0, 'C')
        pdf.cell(col_widths[3], 10, tipo.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        pdf.cell(col_widths[4], 10, valor_formatado.encode('latin1', 'replace').decode('latin1'), 1, 0, 'R')

        pdf.ln()

    # --- CORREÇÃO ANTERIOR: Codificar a saída para bytes ---
    pdf_output = pdf.output(dest='S').encode('latin-1')
    return io.BytesIO(pdf_output)

# --- FUNÇÃO para gerar a Demonstração de Resultados em PDF - CORRIGIDA NA VERSÃO ANTERIOR ---
def gerar_demonstracao_resultados_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos. Se não encontrar, usa Arial padrão.
    # Certifique-se de ter um arquivo .ttf (como Arial.ttf) no mesmo diretório do seu script.
    # Para Streamlit Cloud, o arquivo .ttf precisa estar no mesmo diretório do script.
    try:
        # Assumindo que 'Arial_Unicode.ttf' está no mesmo diretório do script
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_text = 'Arial_Unicode'
    except Exception as e:
         # st.warning(f"Erro ao carregar fonte personalizada para PDF: {e}. Usando fonte padrão (pode não suportar acentos).") # O warning aparece no log, não no PDF
         pdf.set_font("Arial", '', 12)
         font_for_text = 'Arial'


    pdf.set_font(font_for_text, 'B', 14) # Título principal com fonte negrito
    report_title = f"Demonstração de Resultados - {usuario_nome}"
    # O encode/decode aqui é para lidar com caracteres especiais no título
    pdf.cell(0, 10, report_title.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')
    pdf.ln(10)

    # --- Processar dados para a Demonstração de Resultados ---
    receitas_por_categoria = {}
    despesas_por_categoria = {}
    total_receitas = 0
    total_despesas = 0

    for lancamento in lancamentos_list:
        tipo = lancamento.get("Tipo de Lançamento")
        # Usa "Sem Categoria" se a chave não existir ou for vazia
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

    # --- Adicionar Receitas ao PDF ---
    pdf.set_font(font_for_text, 'B', 12) # Título da seção em negrito
    pdf.cell(0, 10, "Receitas".encode('latin1', 'replace').decode('latin1'), 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10) # Conteúdo da seção em fonte normal
    # Ordenar categorias de receita alfabeticamente para consistência
    for categoria in sorted(receitas_por_categoria.keys()):
        valor = receitas_por_categoria[categoria]
        # Garante alinhamento com duas células: categoria à esquerda, valor à direita
        # O encode/decode aqui é para lidar com caracteres especiais
        pdf.cell(100, 7, f"- {categoria}".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10) # Total em negrito
    pdf.cell(100, 7, "Total Receitas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_receitas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')
    pdf.ln(10) # Espaço após a seção de Receitas

    # --- Adicionar Despesas ao PDF ---
    pdf.set_font(font_for_text, 'B', 12) # Título da seção em negrito
    pdf.cell(0, 10, "Despesas".encode('latin1', 'replace').decode('latin1'), 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10) # Conteúdo da seção em fonte normal
     # Ordenar categorias de despesa alfabeticamente
    for categoria in sorted(despesas_por_categoria.keys()):
        valor = despesas_por_categoria[categoria]
        # O encode/decode aqui é para lidar com caracteres especiais
        pdf.cell(100, 7, f"- {categoria}".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10) # Total em negrito
    pdf.cell(100, 7, "Total Despesas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_despesas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')
    pdf.ln(10) # Espaço após a seção de Despesas

    # --- Adicionar Resultado Líquido ---
    resultado_liquido = total_receitas - total_despesas
    pdf.set_font(font_for_text, 'B', 12) # Resultado em negrito

    # Cor do resultado líquido: Azul para positivo, Vermelho para negativo
    if resultado_liquido >= 0:
        pdf.set_text_color(0, 0, 255) # Azul para lucro
    else:
        pdf.set_text_color(255, 0, 0) # Vermelho para prejuízo

    pdf.cell(100, 10, "Resultado Líquido".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 10, f"R$ {resultado_liquido:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')

    # Resetar cor do texto para preto para qualquer texto futuro (se houver)
    pdf.set_text_color(0, 0, 0)

    # Finaliza o PDF e retorna como BytesIO
    # --- CORREÇÃO ANTERIOR: Codificar a saída para bytes ---
    pdf_output = pdf.output(dest='S').encode('latin-1')
    return io.BytesIO(pdf_output)


# --- FUNÇÃO DE EXIBIÇÃO DE LANÇAMENTOS REFATORADA PARA USAR STREAMLIT-AGGRID ---
def exibir_lancamentos():
    st.subheader("Lançamentos")

    # --- Processar ações solicitadas antes de renderizar ---
    # A lógica de processamento das ações (editar/excluir) que atualiza o session_state
    # continua aqui. A AgGrid na próxima execução lerá essas atualizações.
    if st.session_state.get('edit_requested_index') is not None:
        index_to_edit = st.session_state['edit_requested_index']
        # Verifica se o índice ainda é válido
        if 0 <= index_to_edit < len(st.session_state.get('lancamentos', [])):
            st.session_state['editar_indice'] = index_to_edit
            st.session_state['editar_lancamento'] = st.session_state["lancamentos"][index_to_edit]
            st.session_state['show_edit_modal'] = True
        else:
            st.error("Erro: Lançamento a ser editado não encontrado.")
        st.session_state['edit_requested_index'] = None # Reseta a solicitação
        st.rerun() # Rerun para mostrar o modal de edição


    # Processar confirmação de exclusão (mantida a lógica de confirmação separada por simplicidade)
    if st.session_state.get('awaiting_delete_confirmation_index') is not None:
        index_to_confirm_delete = st.session_state['awaiting_delete_confirmation_index']
        # Exibe a mensagem e botões de confirmação em um contêiner separado
        with st.container():
             st.warning(f"Confirmar exclusão deste lançamento?")
             col_confirm_del, col_cancel_del = st.columns([1, 1])
             with col_confirm_del:
                 if st.button("Sim, Excluir", key="confirm_delete_button"):
                     if 0 <= index_to_confirm_delete < len(st.session_state.get("lancamentos", [])):
                        del st.session_state["lancamentos"][index_to_confirm_delete]
                        salvar_lancamentos()
                        st.success("Lançamento excluído com sucesso!")
                     else:
                        st.error("Erro: Lançamento a ser excluído não encontrado na lista original.")
                     st.session_state['awaiting_delete_confirmation_index'] = None # Reseta a confirmação
                     st.rerun() # Rerun após exclusão

             with col_cancel_del:
                 if st.button("Cancelar", key="cancel_delete_button"):
                    st.session_state['awaiting_delete_confirmation_index'] = None # Reseta a confirmação
                    st.info("Exclusão cancelada.")
                    st.rerun() # Rerun após cancelamento

        # Se estiver aguardando confirmação, sai para esperar a interação do usuário
        return


    # --- Prepara os dados para exibição em AgGrid, incluindo o índice original e HTML para botões ---
    lancamentos_para_aggrid = []
    usuario_email = st.session_state.get('usuario_atual_email')

    # Filtra e ordena a lista original primeiro
    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
         lancamentos_filtered_sorted = sorted(st.session_state.get("lancamentos", []), key=lambda x: datetime.strptime(x.get('Data', '1900-01-01'), '%Y-%m-%d'), reverse=True)
    else:
         lancamentos_filtered_sorted = sorted([
             l for l in st.session_state.get("lancamentos", [])
             if l.get('user_email') == usuario_email
         ], key=lambda x: datetime.strptime(x.get('Data', '1900-01-01'), '%Y-%m-%d'), reverse=True)


    # Agora itera sobre a lista filtrada e ordenada para preparar os dados para AgGrid
    for lancamento in lancamentos_filtered_sorted:
         # Encontra o índice original deste lançamento na lista global (sem filtro/ordem)
         # Isso é importante para que as ações de editar/excluir modifiquem o item correto na lista original
         try:
             original_index = st.session_state.get("lancamentos", []).index(lancamento)
         except ValueError:
             # Isso não deveria acontecer se a lógica estiver correta, mas é um fallback
             st.warning(f"Erro interno: Não foi possível encontrar o índice original para um lançamento.")
             continue # Pula este lançamento se não encontrar o índice original


         lancamento_copy = lancamento.copy()
         lancamento_copy['_original_index'] = original_index # Adiciona o índice original para uso interno


         # Formatar data e valor para exibição (AgGrid pode formatar, mas formatar antes garante consistência)
         try:
             data_formatada = datetime.strptime(lancamento_copy.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y")
             lancamento_copy['Data'] = data_formatada
         except ValueError:
             lancamento_copy['Data'] = lancamento_copy.get("Data", "Data Inválida")

         try:
              lancamento_copy['Valor'] = f"R$ {lancamento_copy.get('Valor', 0.0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
         except Exception:
              lancamento_copy['Valor'] = lancamento_copy.get('Valor', 0.0)


         # --- CRIA HTML PARA OS BOTÕES DENTRO DA CÉLULA DE AÇÕES ---
         # Inclui o índice original em um atributo data para ser capturado pelo JavaScript/AgGrid events
         # Adicionados IDs para facilitar a identificação via JavaScript, se necessário
         edit_button_html = f'<button id="edit-btn-{original_index}" class="btn-action btn-edit" data-original-index="{original_index}" style="margin-right: 5px; cursor: pointer;">✏️ Editar</button>'
         delete_button_html = f'<button id="delete-btn-{original_index}" class="btn-action btn-delete" data-original-index="{original_index}" style="cursor: pointer;">🗑️ Excluir</button>'
         lancamento_copy['Ações'] = f"{edit_button_html}{delete_button_html}"


         lancamentos_para_aggrid.append(lancamento_copy)

    # --- Botões de Exportação (mantidos antes da tabela) ---
    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        filename_suffix = "admin"
        usuario_para_pdf_title = "Todos os Lançamentos"
    else:
        filename_suffix = st.session_state.get('usuario_atual_nome', 'usuario').replace(" ", "_").lower()
        usuario_para_pdf_title = st.session_state.get('usuario_atual_nome', 'Usuário')

    # As funções de exportação esperam apenas a lista de dicionários de lançamento original (sem _original_index e HTML)
    # Vamos gerar esta lista a partir de lancamentos_filtered_sorted
    lancamentos_para_exportar = [ {k: v for k, v in item.items() if k not in ['_original_index']} for item in lancamentos_filtered_sorted ] # Remove _original_index


    if not lancamentos_para_exportar:
        st.info("Nenhum lançamento encontrado para este usuário.")
        # Exibe botões de exportação vazios
        col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1])
        with col_excel:
             excel_buffer = exportar_lancamentos_para_excel([]) # Passa lista vazia
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
        return # Sai se não há lançamentos

    # Exibe botões de exportação com dados
    col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1])
    with col_excel:
        excel_buffer = exportar_lancamentos_para_excel(lancamentos_para_exportar)
        if excel_buffer:
            st.download_button(
                label="📥 Exportar Lançamentos em Excel",
                data=excel_buffer,
                file_name=f'lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
    with col_pdf_lista:
         pdf_lista_buffer = exportar_lancamentos_para_pdf(lancamentos_para_exportar, usuario_para_pdf_title)
         st.download_button(
            label="📄 Exportar Lançamentos em PDF",
            data=pdf_lista_buffer,
            file_name=f'lista_lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
         )
    with col_pdf_dr:
         pdf_dr_buffer = gerar_demonstracao_resultados_pdf(lancamentos_para_exportar, usuario_para_pdf_title)
         st.download_button(
            label="📊 Exportar DR em PDF",
            data=pdf_dr_buffer,
            file_name=f'demonstracao_resultados_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
         )
    st.markdown("---")

    # --- Cria DataFrame para AgGrid ---
    df_aggrid = pd.DataFrame(lancamentos_para_aggrid)


    # --- Configurações da AgGrid ---
    go = GridOptionsBuilder.from_dataframe(df_aggrid)

    # Configura a coluna 'Ações' para renderizar HTML e permitir cliques
    # Usamos um cellRenderer que interpreta HTML.
    # É crucial ter 'allow_unsafe_jscode=True' no AgGrid para isso.
    # Também adicionamos um JsCode para capturar cliques nos botões dentro da célula.
    cell_renderer_jscode = JsCode("""
    class ActionButtonRenderer {
        init(params) {
            this.eGui = document.createElement('div');
            this.eGui.innerHTML = params.value; // Renderiza o HTML

            // Adiciona listeners de evento para os botões
            const editButton = this.eGui.querySelector('.btn-edit');
            if (editButton) {
                editButton.addEventListener('click', () => {
                    // Envia uma mensagem de volta para Streamlit com o índice original
                    const originalIndex = editButton.getAttribute('data-original-index');
                    Streamlit.setComponentValue({ action: 'edit', index: originalIndex });
                });
            }

            const deleteButton = this.eGui.querySelector('.btn-delete');
            if (deleteButton) {
                deleteButton.addEventListener('click', () => {
                     // Envia uma mensagem de volta para Streamlit com o índice original
                    const originalIndex = deleteButton.getAttribute('data-original-index');
                    Streamlit.setComponentValue({ action: 'delete', index: originalIndex });
                });
            }
        }
        getGui() {
            return this.eGui;
        }
    }
    """)._js_code # Acessa o código JS puro

    go.configure_column(
        'Ações',
        cellRenderer=cell_renderer_jscode, # Usa o renderizador JS personalizado
        autoHeight=True, # Ajusta altura da linha
        editable=False, # Não permite editar o HTML diretamente na célula
        filterable=False, # Remove filtro na coluna de ações
        sortable=False, # Remove ordenação na coluna de ações
        width=100 # Ajusta largura da coluna de ações (pode precisar de ajuste visual)
    )

    # Configura outras colunas com tipos para melhor filtragem e ordenação pela AgGrid
    go.configure_column('Data', type=['dateColumnFilter', 'customDateTimeFormat'], custom_format_string='dd/MM/yyyy', sortingOrder=['desc', 'asc'])
    go.configure_column('Valor', type=['numericColumn', 'numberColumnFilter'], valueFormatter='(data.Valor != null) ? "R$ " + data.Valor.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : ""') # Formata valor na exibição da AgGrid
    go.configure_column('Descrição', filter=True) # Permite filtro por texto
    go.configure_column('Categorias', filter=True)
    go.configure_column('Tipo de Lançamento', filter=True)


    # Esconde a coluna temporária do índice original
    go.configure_column('_original_index', hide=True)
    if 'user_email' in df_aggrid.columns:
         go.configure_column('user_email', hide=True)


    #go.configure_selection('single', use_checkbox=False) # Desabilitado seleção de linha padrão para focar nos botões

    # Adiciona funcionalidade de "Full Row Action" se quiser capturar cliques na linha inteira
    # go.configure_grid_options(rowClicked=JsCode("""
    # function(params) {
    #     Streamlit.setComponentValue({ action: 'row_click', data: params.data });
    # }
    # """)._js_code)


    gridOptions = go.build()

    # --- Exibe a tabela AgGrid e captura eventos ---
    # É aqui que a tabela interativa é renderizada
    grid_response = AgGrid(
        df_aggrid,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.AS_INPUT, # Retorna os dados modificados na mesma estrutura
        update_mode=GridUpdateMode.MODEL_CHANGED, # Atualiza o estado da grid em mudanças no modelo
        fit_columns_on_grid_load=True, # Tenta ajustar colunas na carga
        allow_unsafe_jscode=True, # **CRUCIAL** para o JavaScript no cellRenderer funcionar
        enable_enterprise_modules=False, # Use False a menos que tenha licença
        height=350, # Altura da tabela
        width='100%', # Largura da tabela
        reload_data=True # Recarrega dados no rerun do Streamlit
    )

    # --- Captura e processa eventos enviados pelo JavaScript dos botões ---
    # A AgGrid envia o valor setado por Streamlit.setComponentValue() para grid_response['data']
    # Mas isso é mais usado para dados da célula. Para eventos de botão, podemos usar
    # o atributo 'onCellClicked' nas gridOptions ou o retorno de Streamlit.setComponentValue
    # A forma como o JsCode foi escrito envia o evento para Streamlit.setComponentValue.
    # Precisamos verificar se grid_response['data'] contém a estrutura que enviamos ({ action: ..., index: ... })

    # Nota: Capturar eventos de clique de botões HTML customizados dentro da AgGrid e passá-los
    # de volta para o Streamlit é uma das partes mais complexas.
    # O código JavaScript acima tenta enviar o índice original e a ação via setComponentValue.
    # Streamlit captura isso, mas a forma exata de recuperar no Python pode variar.

    # Uma abordagem comum é ter um listener JS que atualiza um campo específico na linha
    # que Streamlit está 'observando', ou usar `Streamlit.setComponentValue` e tentar ler
    # o valor retornado no grid_response. O AgGrid Component é um pouco complexo para
    # capturar eventos de botões arbitrários dentro de células HTML customizadas diretamente.

    # O código JS acima usa `Streamlit.setComponentValue`. Vamos tentar ler o que ele retorna.
    # A documentação da AgGrid sugere que setComponentValue atualiza o valor do componente,
    # que Streamlit pode ler no retorno de AgGrid().

    # Vamos verificar se há uma ação pendente baseada no retorno da AgGrid
    # Se o cellRenderer estiver funcionando e enviando o valor, ele pode aparecer aqui.
    # No entanto, AgGrid().data_return_mode='AS_INPUT' retorna os dados da grid.
    # Precisamos de uma forma de capturar o evento, não os dados.

    # Uma alternativa mais confiável para capturar cliques em botões dentro da AgGrid
    # é usar o parâmetro `enable_async_events=True` no `AgGrid` e o evento `cellClicked`,
    # e então verificar qual célula foi clicada.

    # Vamos tentar capturar o evento cellClicked da AgGrid
    # Isso requer habilitar enable_async_events=True e ter um JsCode listener para cellClicked
    # que envia a informação relevante de volta.

    # --- Lógica para capturar eventos de clique nas células da AgGrid ---
    # A AgGrid retorna um dicionário com o estado atual e eventos.
    # Eventos como cellClicked são acionados se enable_async_events=True.
    # A estrutura do evento retornado precisa ser verificada.

    # Com o JsCode no cellRenderer usando Streamlit.setComponentValue, o valor pode ser
    # associado à célula ou linha clicada no retorno da AgGrid.
    # Vamos inspecionar o grid_response para ver se há dados de evento.

    # st.write(grid_response) # Descomente para inspecionar a resposta da AgGrid e entender o que é retornado no clique

    # Vamos tentar verificar se alguma ação foi enviada pelo JavaScript dos botões
    # A estrutura enviada pelo JS é `{ action: 'edit' | 'delete', index: originalIndex }`
    # Precisamos encontrar onde essa informação aparece no `grid_response`.
    # Geralmente, eventos de clique de célula customizados precisam de tratamento específico.

    # Para simplificar (e porque a captura de eventos de botões customizados via AgGrid é complexa),
    # a melhor forma de integrar com o seu sistema atual é:
    # 1. Manter a AgGrid para renderizar a tabela com botões visuais HTML.
    # 2. Continuar usando a lógica de edição/exclusão baseada em st.session_state
    # 3. Precisamos de um mecanismo para que um clique no botão HTML da AgGrid atualize o st.session_state
    #    (`edit_requested_index` ou `awaiting_delete_confirmation_index`).

    # A forma mais fácil de fazer isso COM Streamlit.setComponentValue é usar um JsCode
    # global ou no cellRenderer que envia o valor, e Streamlit.setComponentValue
    # atualizará o valor do componente AgGrid. A resposta da AgGrid pode conter
    # o valor enviado.

    # Vamos adicionar um listener de eventos no Python para a resposta da AgGrid.
    # Se a AgGrid retornar algo na chave 'value' ou similar que corresponda à nossa estrutura { action: ..., index: ...}

    # Captura o valor retornado pelo componente (que pode ser o valor setado pelo Streamlit.setComponentValue no JS)
    # É importante notar que AgGrid()._component_value é o que Streamlit.setComponentValue no JS atualiza.
    # No entanto, acessar atributos privados como _component_value não é recomendado.
    # A forma correta é usar a resposta da AgGrid.

    # Vamos verificar se o grid_response contém a informação da ação clicada
    # A estrutura do retorno de AgGrid com enable_async_events=True e listeners JS pode variar.
    # Assumindo que o JsCode envia {action: ..., index: ...}, precisamos encontrar isso no response.
    # Geralmente, isso aparece em `grid_response['data']` se você modifica os dados,
    # ou em `grid_response['selected_rows']` se a linha é selecionada,
    # ou em chaves específicas de evento se `enable_async_events=True` e listeners são usados.

    # Com o JsCode no cellRenderer, o valor setado por Streamlit.setComponentValue
    # pode aparecer diretamente na resposta da AgGrid.
    # Vamos tentar verificar se `grid_response` contém as chaves 'action' e 'index'.

    # Verifica se a resposta da AgGrid contém informações de ação (enviadas pelo JS)
    if grid_response is not None and isinstance(grid_response, dict):
        # A forma exata como o valor do Streamlit.setComponentValue retorna pode variar dependendo da versão da AgGrid
        # E como está configurado. Pode estar em 'value', 'data', etc.
        # Vamos tentar inspecionar algumas chaves comuns ou a resposta completa.
        # st.write("Grid Response:", grid_response) # Ajuda de debug

        # Se o JsCode setta o valor do COMPONENTE com Streamlit.setComponentValue,
        # Streamlit pode retornar esse valor diretamente na resposta ou em uma chave padrão.
        # Vamos tentar verificar se as chaves 'action' e 'index' estão diretamente no dicionário de resposta.
        # Ou talvez no 'data' ou 'selected_rows' se a linha for considerada "modificada" ou "selecionada".

        # Tentativa de verificar as chaves diretamente no dicionário de resposta
        if 'action' in grid_response and 'index' in grid_response:
             action = grid_response['action']
             index = int(grid_response['index']) # O índice vem como string do JS

             if action == 'edit':
                 st.session_state['edit_requested_index'] = index
                 st.rerun()
             elif action == 'delete':
                 st.session_state['awaiting_delete_confirmation_index'] = index
                 st.rerun()
        # Nota: Esta forma de capturar eventos pode não ser a mais robusta ou oficial.
        # A forma mais "correta" com AgGrid envolve listeners de eventos e enable_async_events.

    # --- Fim da lógica de exibição e captura de eventos da AgGrid ---


def pagina_cadastro():
    st.title("Cadastro de Novo Usuário")

    if st.session_state.get('tipo_usuario_atual') != 'Administrador':
        st.warning("Você não tem permissão para acessar esta página.")
        st.session_state['pagina_atual'] = 'dashboard'
        st.rerun()
        return

    with st.form("cadastro_usuario_form"):
        nome = st.text_input("Nome Completo")
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Senha", type="password")
        tipo = st.selectbox("Tipo de Usuário", ["Cliente", "Administrador"])
        categorias_receita_str = st.text_area("Categorias de Receita Personalizadas (separar por vírgula)")

        cadastrar_button = st.form_submit_button("Cadastrar")

        if cadastrar_button:
            if not nome or not email or not senha or not confirmar_senha:
                st.warning("Por favor, preencha todos os campos.")
            elif senha != confirmar_senha:
                st.warning("As senhas não coincidem.")
            else:
                # Verifica se o e-mail já existe
                if any(usuario.get('Email') == email for usuario in st.session_state.get('usuarios', [])):
                    st.error("Este e-mail já está cadastrado.")
                else:
                    # Processa as categorias de receita
                    categorias_receita_lista = [cat.strip() for cat in categorias_receita_str.split(',') if cat.strip()]

                    novo_usuario = {
                        "Nome": nome,
                        "Email": email,
                        "Senha": senha, # Em um app real, a senha deve ser hashada!
                        "Tipo": tipo,
                        "categorias_receita": categorias_receita_lista # Salva as categorias personalizadas
                    }
                    st.session_state.get('usuarios', []).append(novo_usuario)
                    salvar_usuarios()
                    st.success("Usuário cadastrado com sucesso!")
                    # Limpa o formulário após o cadastro (opcional)
                    # st.form_state(key="cadastro_usuario_form").clear() # Esta função não existe mais diretamente assim
                    # Para limpar, precisaríamos de controle de estado mais granular nos inputs
                    st.rerun() # Roda novamente para limpar o formulário
    st.markdown("---")
    st.subheader("Usuários Cadastrados")

    usuarios_para_exibir = st.session_state.get('usuarios', [])
    if not usuarios_para_exibir:
        st.info("Nenhum usuário cadastrado.")
    else:
        # Cria um DataFrame para exibir os dados dos usuários
        df_usuarios = pd.DataFrame(usuarios_para_exibir)

        # Remove a coluna de senha para exibição
        if 'Senha' in df_usuarios.columns:
             df_usuarios = df_usuarios.drop(columns=['Senha'])

        # Adiciona uma coluna para ações (excluir)
        df_usuarios['Ações'] = ""

        st.dataframe(
            df_usuarios,
            column_config={
                "Nome": st.column_config.Column(width="medium"),
                "Email": st.column_config.Column(width="medium"),
                "Tipo": st.column_config.Column(width="small"),
                "categorias_receita": st.column_config.Column("Categorias Receita", width="medium"),
                "Ações": st.column_config.Column(width="small") # Ajuste a largura conforme necessário
            },
            hide_index=True,
            use_container_width=True
        )

        # Adiciona botões de ação abaixo da tabela para cada usuário
        for index, row in df_usuarios.iterrows():
            # Verifica se o usuário atual é o que está sendo exibido para não excluir a si mesmo (opcional)
            if row['Email'] != st.session_state.get('usuario_atual_email'):
                 col1, col2, col3 = st.columns([1, 1, 8]) # Colunas para alinhar o botão

                 with col1:
                    # Botão Excluir para cada usuário
                    # Adicionado kind="secondary" para aplicar o estilo CSS de exclusão
                    # Adapte a lógica de exclusão de usuário se precisar de confirmação também
                    if st.button("🗑️ Excluir", key=f"delete_usuario_{index}"):
                         # Confirmação antes de excluir (opcional, mas recomendado)
                         # Nota: A lógica de confirmação de usuário aqui é a original e pode ser adaptada
                         # para o novo padrão de estado se desejar uma experiência consistente.
                         if st.session_state.get('confirm_delete_usuario_index') == index:
                             # Se já pediu confirmação para este item, exclui
                             excluir_usuario(index)
                             st.session_state['confirm_delete_usuario_index'] = None # Reseta a confirmação
                             st.rerun()
                         else:
                             # Primeira vez clicando, pede confirmação
                             st.session_state['confirm_delete_usuario_index'] = index
                             st.warning(f"Clique novamente em 'Excluir' para confirmar a exclusão de {row['Nome']}.")
                             # Não faz rerun aqui, espera o segundo clique


def pagina_dashboard():
    if not st.session_state.get('autenticado'):
        st.session_state['pagina_atual'] = 'login'
        st.rerun()
        return

    st.title(f"Dashboard - {st.session_state.get('usuario_atual_nome', 'Usuário')}")

    exibir_resumo_central()

    # Botão para adicionar novo lançamento (sempre visível para usuários autenticados)
    if st.button("➕ Adicionar Novo Lançamento"):
        st.session_state['show_add_modal'] = True # Exibe o formulário "popup"
        st.rerun()

    # Renderiza o formulário de adição se a variável de estado for True
    if st.session_state.get('show_add_modal'):
        render_add_lancamento_form()

    # Renderiza o formulário de edição se a variável de estado for True
    if st.session_state.get('show_edit_modal'):
         render_edit_lancamento_form()

    # Chama a função exibir_lancamentos (agora usando AgGrid)
    exibir_lancamentos()


def gerenciar_categorias_receita():
    st.title("Gerenciar Categorias de Receita")

    # Verifica se o usuário está logado antes de continuar
    if not st.session_state.get('autenticado'):
        st.warning("Você precisa estar logado para gerenciar categorias.")
        st.session_state['pagina_atual'] = 'login' # Redireciona para login se não estiver logado
        st.rerun()
        return

    st.info(f"Editando categorias para: {st.session_state.get('usuario_atual_nome')}")

    # Obter o índice do usuário logado
    usuario_index = st.session_state.get('usuario_atual_index')

    if usuario_index is None or usuario_index >= len(st.session_state.get('usuarios', [])):
         st.error("Erro: Usuário logado não encontrado.")
         return # Sai da função se o usuário logado não for válido

    usuario_logado = st.session_state['usuarios'][usuario_index]

    st.subheader("Categorias Atuais")

    # Exibe as categorias atuais (combinando padrão e personalizadas)
    todas_categorias_atuais = st.session_state.get('todas_categorias_receita', CATEGORIAS_PADRAO_RECEITA)
    if todas_categorias_atuais:
        st.write(", ".join(todas_categorias_atuais))
    else:
        st.info("Nenhuma categoria de receita definida (apenas as padrão serão usadas).")

    st.subheader("Adicionar Nova Categoria")
    nova_categoria = st.text_input("Nome da Nova Categoria de Receita")
    if st.button("Adicionar Categoria"):
        if nova_categoria and nova_categoria not in usuario_logado.get('categorias_receita', []) and nova_categoria not in CATEGORIAS_PADRAO_RECEITA:
             # Adiciona apenas se não estiver nas categorias personalizadas atuais ou nas padrão
             if 'categorias_receita' not in usuario_logado:
                 usuario_logado['categorias_receita'] = []
             usuario_logado['categorias_receita'].append(nova_categoria.strip()) # Adiciona à lista do usuário logado
             salvar_usuarios() # Salva as alterações nos usuários
             # Atualiza a lista combinada no estado da sessão para refletir a mudança imediatamente
             todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + usuario_logado['categorias_receita']))
             st.session_state['todas_categorias_receita'] = todas_unicas_receita

             st.success(f"Categoria '{nova_categoria}' adicionada com sucesso!")
             st.rerun()
        elif nova_categoria in usuario_logado.get('categorias_receita', []) or nova_categoria in CATEGORIAS_PADRAO_RECEITA:
            st.warning(f"A categoria '{nova_categoria}' já existe.")
        else:
            st.warning("Por favor, digite o nome da nova categoria.")


    st.subheader("Remover Categoria Personalizada")
    # Lista apenas as categorias personalizadas do usuário logado para remoção
    categorias_personalizadas_atuais = usuario_logado.get('categorias_receita', [])

    if categorias_personalizadas_atuais:
        categoria_a_remover = st.selectbox("Selecione a categoria personalizada para remover", [""] + categorias_personalizadas_atuais)
        if st.button("Remover Categoria Selecionada"):
            if categoria_a_remover and categoria_a_remover in categorias_personalizadas_atuais:
                usuario_logado['categorias_receita'].remove(categoria_a_remover) # Remove da lista do usuário logado
                salvar_usuarios() # Salva as alterações nos usuários
                 # Atualiza a lista combinada no estado da sessão
                todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + usuario_logado['categorias_receita']))
                st.session_state['todas_categorias_receita'] = todas_unicas_receita

                st.success(f"Categoria '{categoria_a_remover}' removida com sucesso.")
                st.rerun()
            elif categoria_a_remover:
                st.warning("A categoria selecionada não foi encontrada nas suas categorias personalizadas.")
            else:
                st.warning("Por favor, selecione uma categoria para remover.")
    else:
        st.info("Você não possui categorias de receita personalizadas para remover.")


def pagina_gerenciar_usuarios():
    st.title("Gerenciar Usuários")

    # Verifica si el usuario logueado es Administrador
    if st.session_state.get('tipo_usuario_atual') != 'Administrador':
        st.warning("Usted no tiene permiso para acceder a esta página.")
        st.session_state['pagina_atual'] = 'dashboard' # Redirecciona si no es admin
        st.rerun()
        return

    # Exibe a lista de usuários e botões para adicionar/editar/excluir (usando a função de cadastro adaptada)
    pagina_cadastro() # Reutiliza a lógica de exibição e adição da página de cadastro

    # Adicionar lógica para edição de usuários se necessário (não implementado no código original fornecido)


# --- Navegação ---
def navegar_para(pagina):
    st.session_state['pagina_atual'] = pagina
    st.rerun()

# --- Barra Lateral ---
with st.sidebar:
    if st.session_state.get('autenticado'):
        st.write(f"Bem-vindo, {st.session_state.get('usuario_atual_nome')}!")
        st.write(f"Tipo: {st.session_state.get('tipo_usuario_atual')}")

        st.button("Dashboard", on_click=navegar_para, args=('dashboard',))
        if st.session_state.get('tipo_usuario_atual') == 'Administrador':
            st.button("Gerenciar Usuários", on_click=navegar_para, args=('gerenciar_usuarios',))
        # Botão para gerenciar categorias (agora disponível para todos os usuários autenticados)
        st.button("Gerenciar Categorias Receita", on_click=navegar_para, args=('gerenciar_categorias_receita',))
        st.button("Sair", on_click=navegar_para, args=('logout',))
    else:
        st.button("Login", on_click=navegar_para, args=('login',))

# --- Roteamento de Páginas ---
if st.session_state['pagina_atual'] == 'login':
    pagina_login()
elif st.session_state['pagina_atual'] == 'dashboard':
    pagina_dashboard()
elif st.session_state['pagina_atual'] == 'cadastro':
    # Nota: a página de cadastro agora é renderizada dentro de 'gerenciar_usuarios'
    # Esta condição pode ser removida ou adaptada se você tiver uma página de cadastro separada.
    # Mantendo aqui caso haja outra forma de acessar cadastro no seu fluxo.
    st.warning("Página de Cadastro acessada diretamente. Redirecionando para Gerenciar Usuários.")
    st.session_state['pagina_atual'] = 'gerenciar_usuarios'
    st.rerun()
elif st.session_state['pagina_atual'] == 'gerenciar_categorias_receita':
     gerenciar_categorias_receita() # Nova página para gerenciar categorias de receita
elif st.session_state['pagina_atual'] == 'gerenciar_usuarios':
     pagina_gerenciar_usuarios() # Nova página para gerenciar usuários (inclui cadastro/exibição)
elif st.session_state['pagina_atual'] == 'logout':
    st.session_state['autenticado'] = False
    st.session_state['usuario_atual_email'] = None
    st.session_state['usuario_atual_nome'] = None
    st.session_state['tipo_usuario_atual'] = None
    st.session_state['usuario_atual_index'] = None
    st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy() # Resetar categorias ao fazer logout
    st.info("Você saiu da sua conta.")
    st.session_state['pagina_atual'] = 'login'
    st.rerun()
else:
    # Página padrão caso algo dê errado
    st.session_state['pagina_atual'] = 'login'
    st.rerun()
