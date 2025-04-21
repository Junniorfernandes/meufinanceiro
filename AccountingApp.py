import streamlit as st
from datetime import datetime
import json
import os
import pandas as pd
import io
from fpdf import FPDF

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
        background-color: #003548; # era #f8d7da; /* Fundo vermelho claro */
        color: #ffffff; # era #721c24; /* Texto vermelho escuro */
        border-color: #fbcfe8; # era #f5c6cb; /* Borda vermelha */
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

# Função para exportar lançamentos para PDF (lista detalhada) - Mantida a original
def exportar_lancamentos_para_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos. Se não encontrar, usa Arial padrão.
    # Certifique-se de ter um arquivo .ttf (como Arial.ttf) no mesmo diretório do seu script.
    try:
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf') # Substitua 'Arial_Unicode.ttf' pelo caminho ou nome do seu arquivo .ttf
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_table = 'Arial_Unicode'
    except Exception as e:
         # st.warning(f"Erro ao carregar fonte personalizada para PDF: {e}. Usando fonte padrão.") # Mantendo o aviso na console
         pdf.set_font("Arial", '', 12)
         font_for_table = 'Arial'


    pdf.set_font("Arial", 'B', 12) # Use negrito da fonte padrão para o título (conforme original)
    report_title = f"Relatório de Lançamentos - {usuario_nome}"
    pdf.cell(0, 10, report_title.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')
    pdf.ln(10)

    # Usa a fonte com suporte a acentos (se carregada) ou a padrão para os cabeçalhos e dados da tabela
    pdf.set_font(font_for_table, 'B', 10) # Cabeçalhos em negrito
    col_widths = [20, 50, 30, 20, 20]
    headers = ["Data", "Descrição", "Categoria", "Tipo", "Valor"]

    for i, header in enumerate(headers):
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

        # Certifique-se de que cada célula está recebendo bytes, não strings
        # encode('latin1', 'replace') já faz isso
        pdf.cell(col_widths[0], 10, data_formatada.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        pdf.cell(col_widths[1], 10, descricao.encode('latin1', 'replace').decode('latin1'), 1, 0, 'L')
        pdf.cell(col_widths[2], 10, categoria.encode('latin1', 'replace').decode('latin1') if categoria else "", 1, 0, 'C')
        pdf.cell(col_widths[3], 10, tipo.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        pdf.cell(col_widths[4], 10, valor_formatado.encode('latin1', 'replace').decode('latin1'), 1, 0, 'R')

        pdf.ln()

    # --- LINHA CORRIGIDA ---
    pdf_output_str = pdf.output(dest='S')
    pdf_output_bytes = pdf_output_str.encode('latin-1') # Tente 'utf-8' se 'latin-1' ainda falhar

    return io.BytesIO(pdf_output_bytes)


# --- FUNÇÃO para gerar a Demonstração de Resultados em PDF ---
def gerar_demonstracao_resultados_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos. Se não encontrar, usa Arial padrão.
    # Certifique-se de ter um arquivo .ttf (como Arial.ttf) no mesmo diretório do seu script.
    try:
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf') # Substitua 'Arial_Unicode.ttf'
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_text = 'Arial_Unicode'
    except Exception as e:
         # st.warning(f"Erro ao carregar fonte personalizada para PDF: {e}. Usando fonte padrão (pode não suportar acentos).") # O warning aparece no log, não no PDF
         pdf.set_font("Arial", '', 12)
         font_for_text = 'Arial'


    pdf.set_font(font_for_text, 'B', 14) # Título principal com fonte negrito
    report_title = f"Demonstração de Resultados - {usuario_nome}"
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
    # --- LINHA CORRIGIDA ---
    pdf_output_str = pdf.output(dest='S')
    pdf_output_bytes = pdf_output_str.encode('latin-1') # Tente 'utf-8' se 'latin-1' ainda falhar

    return io.BytesIO(pdf_output_bytes)


def exibir_lancamentos():
    st.subheader("Lançamentos")

    # Define a variável antes dos blocos if/else e inicializa como lista vazia
    lancamentos_para_exibir = []
    usuario_email = st.session_state.get('usuario_atual_email')

    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        lancamentos_para_exibir = st.session_state.get("lancamentos", [])
        st.info("Exibindo TODOS os lançamentos (Admin view).")
        filename_suffix = "admin"
        usuario_para_pdf_title = "Todos os Lançamentos"
    else:
        # Atribui diretamente à variável lancamentos_para_exibir no bloco else
        lancamentos_para_exibir = [
            l for l in st.session_state.get("lancamentos", [])
            if l.get('user_email') == usuario_email
        ]
        st.info(f"Exibindo seus lançamentos, {st.session_state.get('usuario_atual_nome', 'usuário')} (Client view).")
        filename_suffix = st.session_state.get('usuario_atual_nome', 'usuario').replace(" ", "_").lower()
        usuario_para_pdf_title = st.session_state.get('usuario_atual_nome', 'Usuário')


    if not lancamentos_para_exibir:
        st.info("Nenhum lançamento encontrado para este usuário.")
        # Exibe os botões de exportação mesmo com lista vazia (arquivos estarão vazios ou com cabeçalho)
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
             # Use a sua função original para exportar a lista vazia
             pdf_lista_buffer = exportar_lancamentos_para_pdf([], usuario_para_pdf_title)
             st.download_button(
                label="📄 Exportar Lista PDF (Vazia)",
                data=pdf_lista_buffer,
                file_name=f'lista_lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
                mime='application/pdf'
             )
        with col_pdf_dr:
             # Use a nova função para exportar a DR vazia
             pdf_dr_buffer = gerar_demonstracao_resultados_pdf([], usuario_para_pdf_title)
             st.download_button(
                label="📊 Exportar DR PDF (Vazia)",
                data=pdf_dr_buffer,
                file_name=f'demonstracao_resultados_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
                mime='application/pdf'
             )
        st.markdown("---")
        return # Sai da função para não exibir a tabela vazia


    # Ordenar lançamentos por data (do mais recente para o mais antigo)
    try:
        # Usamos a lista que já foi filtrada/selecionada corretamente
        lancamentos_para_exibir.sort(key=lambda x: datetime.strptime(x.get('Data', '1900-01-01'), '%Y-%m-%d'), reverse=True)
    except ValueError:
        st.warning("Não foi possível ordenar os lançamentos por data devido a formato inválido.")

    # --- Botões de Exportação ---
    # Adicionamos uma terceira coluna para o novo botão da Demonstração de Resultados
    # AUMENTANDO A LARGURA DA COLUNA DE AÇÕES (último valor na lista)
    col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1]) # Mantendo 3 colunas para os botões de exportação

    with col_excel:
        excel_buffer = exportar_lancamentos_para_excel(lancamentos_para_exibir)
        if excel_buffer: # Só exibe o botão se a geração do Excel for bem-sucedida
            st.download_button(
                label="📥 Exportar Lançamentos em Excel",
                data=excel_buffer,
                file_name=f'lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

    with col_pdf_lista:
         # Botão para a sua função original de exportação (lista detalhada)
         pdf_lista_buffer = exportar_lancamentos_para_pdf(lancamentos_para_exibir, usuario_para_pdf_title)
         st.download_button(
            label="📄 Exportar Lista PDF",
            data=pdf_lista_buffer,
            file_name=f'lista_lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
         )

    with col_pdf_dr:
         # Botão para a nova Demonstração de Resultados
         pdf_dr_buffer = gerar_demonstracao_resultados_pdf(lancamentos_para_exibir, usuario_para_pdf_title)
         st.download_button(
            label="📊 Exportar DR PDF",
            data=pdf_dr_buffer,
            file_name=f'demonstracao_resultados_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
         )


    st.markdown("---")

    # --- Exibição dos Lançamentos em Tabela ---
    # Cria uma cópia para exibir na tabela, removendo 'user_email' se não for admin
    lancamentos_para_tabela = [l.copy() for l in lancamentos_para_exibir]

    # Remove a coluna 'user_email' da exibição para usuários não administradores
    if st.session_state.get('tipo_usuario_atual') != 'Administrador':
        for l in lancamentos_para_tabela:
            if 'user_email' in l:
                del l['user_email']
    else:
        # Para administradores, pode ser útil ver a qual usuário o lançamento pertence
        # Renomeia a coluna para algo mais amigável
        for l in lancamentos_para_tabela:
             if 'user_email' in l:
                  l['Usuário (Email)'] = l.pop('user_email')


    if not lancamentos_para_tabela:
        st.info("Nenhum lançamento para exibir na tabela.")
        return

    df_lancamentos = pd.DataFrame(lancamentos_para_tabela)

    # Formata colunas antes de exibir
    if 'Data' in df_lancamentos.columns:
        # Converte para datetime primeiro, manipulando erros, e depois formata
        try:
            df_lancamentos['Data'] = pd.to_datetime(df_lancamentos['Data'], errors='coerce').dt.strftime('%d/%m/%Y')
        except Exception as e:
             st.warning(f"Erro ao formatar a coluna 'Data' para exibição: {e}")
             # Mantém a coluna como estava se a formatação falhar

    if 'Valor' in df_lancamentos.columns:
         try:
             df_lancamentos['Valor'] = df_lancamentos['Valor'].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))
         except Exception as e:
             st.warning(f"Erro ao formatar a coluna 'Valor' para exibição: {e}")
             # Mantém a coluna como estava se a formatação falhar


    # Adiciona colunas para botões de Ações
    # AUMENTANDO A LARGURA DA COLUNA DE AÇÕES (último valor na lista)
    colunas_exibicao = df_lancamentos.columns.tolist() + ["Ações"]

    # Usa o Streamlit data_editor para uma tabela mais interativa com botões por linha
    # É mais complexo integrar botões diretamente no data_editor para cada linha.
    # Uma abordagem comum é usar colunas separadas para os botões ou links,
    # mas a estrutura atual com laço sobre o DataFrame index é mais flexível para botões.
    # Vamos manter a iteração para ter botões de edição/exclusão por linha.


    st.dataframe(df_lancamentos, hide_index=True) # Exibe o DataFrame formatado


    st.markdown("---")

    # --- Edição/Exclusão (Abaixo da Tabela) ---
    st.subheader("Opções de Lançamentos")

    # Adiciona um botão para adicionar novo lançamento
    if st.button("➕ Adicionar Novo Lançamento"):
         st.session_state['show_add_modal'] = True
         st.rerun()

    # Se o modal de adicionar estiver ativo, renderiza o formulário de adição
    if st.session_state.get('show_add_modal'):
         render_add_lancamento_form()


    # Adiciona campos para selecionar lançamento a editar ou excluir
    st.markdown("---")
    st.subheader("Gerenciar Lançamentos Individuais")
    # Reconstroi o DataFrame apenas para obter os índices para seleção
    # Usa os lançamentos originais para garantir que o índice corresponda
    df_para_selecao = pd.DataFrame(st.session_state.get("lancamentos", []))


    if not df_para_selecao.empty:
        # Cria uma coluna combinada para seleção (ex: "Data - Descrição - Valor")
        df_para_selecao['Exibicao'] = df_para_selecao.apply(
            lambda row: f"{datetime.strptime(row.get('Data', '1900-01-01'), '%Y-%m-%d').strftime('%d/%m/%Y')} - {row.get('Descrição', 'Sem Descrição')} - R$ {row.get('Valor', 0.0):.2f}".replace('.', ','),
            axis=1
        )
        lancamentos_para_selectbox = df_para_selecao['Exibicao'].tolist()
        opcoes_selecao = ["Selecione um lançamento..."] + lancamentos_para_selectbox
        selecao_lancamento = st.selectbox("Selecione o lançamento para Editar ou Excluir", opcoes_selecao)

        # Encontra o índice do lançamento selecionado na lista original
        indice_selecionado = None
        if selecao_lancamento != "Selecione um lançamento...":
            try:
                 # Precisamos encontrar o índice na lista original baseada na string de exibição
                 # Isso é um pouco frágil se as descrições forem muito parecidas.
                 # Uma abordagem mais robusta seria usar o índice do DataFrame `df_para_selecao`
                 # e mapeá-lo de volta para a lista original, mas o DataFrame já está baseado nela.
                 # Vamos tentar encontrar pelo conteúdo correspondente na lista original.
                 # Como a lista `lancamentos_para_exibir` está ordenada, e o selectbox usa a mesma ordem,
                 # podemos usar o índice da seleção (menos 1, por causa da opção "Selecione...")
                 index_na_selecao = opcoes_selecao.index(selecao_lancamento) - 1
                 if 0 <= index_na_selecao < len(lancamentos_para_exibir):
                      # Precisamos encontrar o índice original na lista global st.session_state["lancamentos"]
                      # que corresponde ao lançamento selecionado em lancamentos_para_exibir.
                      lancamento_selecionado_exibicao = lancamentos_para_exibir[index_na_selecao]
                      # Encontra o índice original na lista global
                      try:
                           for i, lancamento_original in enumerate(st.session_state.get("lancamentos", [])):
                                # Compara por um identificador único ou múltiplos campos para evitar erros
                                # Comparar por data (como string), descrição e valor (com formatação) pode ser suficiente
                                data_original_str = lancamento_original.get('Data', '1900-01-01')
                                descricao_original = lancamento_original.get('Descrição', '')
                                valor_original = lancamento_original.get('Valor', 0.0)

                                data_selecionada_str = lancamento_selecionado_exibicao.get('Data', '1900-01-01')
                                descricao_selecionada = lancamento_selecionado_exibicao.get('Descrição', '')
                                valor_selecionado = lancamento_selecionado_exibicao.get('Valor', 0.0)

                                if (data_original_str == data_selecionada_str and
                                    descricao_original == descricao_selecionada and
                                    abs(valor_original - valor_selecionado) < 0.01): # Comparação de float
                                     indice_selecionado = i
                                     break # Encontrou o índice original

                           if indice_selecionado is None:
                                raise ValueError("Índice original não encontrado.") # Força o erro se não encontrar

                      except Exception as e:
                           st.error(f"Erro ao encontrar o índice original do lançamento: {e}")
                           indice_selecionado = None # Reseta o índice se houver erro

                 # Agora, verifica se o usuário logado tem permissão para editar/excluir este lançamento
                 if indice_selecionado is not None:
                     lancamento_original = st.session_state.get("lancamentos", [])[indice_selecionado]
                     is_owner = lancamento_original.get('user_email') == st.session_state.get('usuario_atual_email')
                     is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'

                     if not (is_owner or is_admin):
                         st.warning("Você não tem permissão para gerenciar este lançamento.")
                         indice_selecionado = None # Invalida a seleção se não tiver permissão

            except ValueError as e:
                 st.warning(f"Por favor, selecione um lançamento válido. Detalhe: {e}")
                 indice_selecionado = None # Garante que o índice é None em caso de erro

        col_edit, col_delete = st.columns(2)

        if indice_selecionado is not None:
            with col_edit:
                if st.button("✏️ Editar Lançamento"):
                    st.session_state['editar_indice'] = indice_selecionado
                    # Carrega os dados do lançamento a ser editado para o estado
                    st.session_state['editar_lancamento'] = st.session_state.get("lancamentos", [])[indice_selecionado]
                    st.session_state['show_edit_modal'] = True
                    st.rerun()

            with col_delete:
                if st.button("🗑️ Excluir Lançamento", type="secondary"):
                    # Antes de excluir, verifica novamente a permissão
                     lancamento_a_excluir = st.session_state.get("lancamentos", [])[indice_selecionado]
                     is_owner = lancamento_a_excluir.get('user_email') == st.session_state.get('usuario_atual_email')
                     is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'

                     if is_owner or is_admin:
                         del st.session_state["lancamentos"][indice_selecionado]
                         salvar_lancamentos()
                         st.success("Lançamento excluído com sucesso!")
                         st.rerun()
                     else:
                         st.error("Você não tem permissão para excluir este lançamento.")


    # Se o modal de editar estiver ativo, renderiza o formulário de edição
    if st.session_state.get('show_edit_modal') and st.session_state.get('editar_indice') is not None:
        render_edit_lancamento_form()


def pagina_gerenciar_usuarios():
    if st.session_state.get('tipo_usuario_atual') != 'Administrador':
        st.warning("Acesso negado. Esta página é apenas para administradores.")
        return

    st.title("Gerenciar Usuários")

    usuarios_list = st.session_state.get('usuarios', [])
    df_usuarios = pd.DataFrame(usuarios_list)

    # Exclui a coluna de senha para exibição na tabela por segurança
    if 'Senha' in df_usuarios.columns:
        df_usuarios_display = df_usuarios.drop(columns=['Senha'])
    else:
        df_usuarios_display = df_usuarios.copy()

    # Adiciona colunas para botões de Ações
    df_usuarios_display['Ações'] = ""

    st.dataframe(df_usuarios_display, hide_index=True)

    st.markdown("---")
    st.subheader("Adicionar Novo Usuário")

    with st.form(key='add_usuario_form'):
        nome = st.text_input("Nome do Usuário")
        email = st.text_input("E-mail do Usuário")
        senha = st.text_input("Senha", type='password')
        tipo = st.selectbox("Tipo de Usuário", ["Cliente", "Administrador"])
        # Campo para adicionar categorias de receita personalizadas (opcional, separado por vírgulas)
        categorias_receita_str = st.text_input("Categorias de Receita (separadas por vírgula, opcional)")


        submit_add_user = st.form_submit_button("Adicionar Usuário")

        if submit_add_user:
            if not nome or not email or not senha:
                st.warning("Nome, E-mail e Senha são obrigatórios.")
            else:
                # Verifica se o e-mail já existe
                if any(u.get('Email') == email for u in usuarios_list):
                    st.error("Este e-mail já está cadastrado.")
                else:
                    # Processa as categorias de receita inseridas
                    categorias_personalizadas = [c.strip() for c in categorias_receita_str.split(',') if c.strip()]
                    novo_usuario = {
                        'Nome': nome,
                        'Email': email,
                        'Senha': senha, # Em uma aplicação real, a senha deve ser hasheada
                        'Tipo': tipo,
                        'categorias_receita': categorias_personalizadas # Salva as categorias personalizadas
                    }
                    st.session_state['usuarios'].append(novo_usuario)
                    salvar_usuarios()
                    st.success("Usuário adicionado com sucesso!")
                    st.rerun()


    st.markdown("---")
    st.subheader("Gerenciar Usuários Individuais")

    if not df_usuarios.empty:
        # Cria uma coluna combinada para seleção
        df_usuarios['Exibicao'] = df_usuarios.apply(lambda row: f"{row.get('Nome', 'Sem Nome')} ({row.get('Email', 'Sem Email')})", axis=1)
        usuarios_para_selectbox = df_usuarios['Exibicao'].tolist()
        opcoes_selecao_usuario = ["Selecione um usuário..."] + usuarios_para_selectbox
        selecao_usuario = st.selectbox("Selecione o usuário para Editar ou Excluir", opcoes_selecao_usuario)

        indice_usuario_selecionado = None
        if selecao_usuario != "Selecione um usuário...":
             # Encontra o índice do usuário selecionado na lista original
             # Como o selectbox reflete a ordem do DataFrame, podemos usar o índice do DataFrame
             try:
                 index_na_selecao_usuario = opcoes_selecao_usuario.index(selecao_usuario) - 1
                 if 0 <= index_na_selecao_usuario < len(usuarios_list):
                       # Encontra o índice original na lista global de usuários
                       # Podemos comparar pelo Email, que deve ser único
                       email_selecionado = usuarios_list[index_na_selecao_usuario].get('Email')
                       for i, usuario_original in enumerate(st.session_state.get('usuarios', [])):
                            if usuario_original.get('Email') == email_selecionado:
                                 indice_usuario_selecionado = i
                                 st.session_state['editar_usuario_index'] = i # Guarda o índice para edição
                                 st.session_state['editar_usuario_data'] = usuario_original # Guarda os dados para edição
                                 break
                       if indice_usuario_selecionado is None:
                            raise ValueError("Índice original do usuário não encontrado.")

             except ValueError as e:
                  st.warning(f"Por favor, selecione um usuário válido. Detalhe: {e}")
                  indice_usuario_selecionado = None
                  st.session_state['editar_usuario_index'] = None
                  st.session_state['editar_usuario_data'] = None


        col_edit_user, col_delete_user = st.columns(2)

        if indice_usuario_selecionado is not None:
            with col_edit_user:
                 # Renderiza o formulário de edição de usuário se um usuário estiver selecionado
                 # O formulário será um popup ou expander controlado por estado
                 if st.button("✏️ Editar Usuário"):
                      # O estado para edição já foi setado na lógica acima
                      st.session_state['show_edit_user_modal'] = True # Novo estado para modal de edição de usuário
                      st.rerun()

            with col_delete_user:
                # Impede que o admin logado se exclua
                if (indice_usuario_selecionado == st.session_state.get('usuario_atual_index') and
                    st.session_state.get('tipo_usuario_atual') == 'Administrador'):
                     st.warning("Você não pode excluir seu próprio usuário administrador.")
                else:
                    if st.button("🗑️ Excluir Usuário", type="secondary"):
                         excluir_usuario(indice_usuario_selecionado) # Chama a função de exclusão


    # Renderiza o formulário de edição de usuário se o estado permitir
    if st.session_state.get('show_edit_user_modal') and st.session_state.get('editar_usuario_index') is not None:
        render_edit_usuario_form()


# --- Novo formulário de Edição de Usuário (Pode ser um expander ou função separada) ---
# Adicionar estado para controlar a exibição do formulário de edição de usuário
if 'show_edit_user_modal' not in st.session_state:
     st.session_state['show_edit_user_modal'] = False


def render_edit_usuario_form():
     if not st.session_state.get('show_edit_user_modal') or st.session_state.get('editar_usuario_index') is None:
          return

     indice = st.session_state.get('editar_usuario_index')
     usuario_a_editar = st.session_state.get('editar_usuario_data')

     if usuario_a_editar is None:
          st.error("Dados do usuário para edição não encontrados.")
          st.session_state['show_edit_user_modal'] = False
          st.session_state['editar_usuario_index'] = None
          st.session_state['editar_usuario_data'] = None
          st.rerun()
          return

     st.subheader(f"Editar Usuário: {usuario_a_editar.get('Nome', 'Sem Nome')}")

     with st.form(key=f'edit_usuario_form_{indice}'):
          nome = st.text_input("Nome", value=usuario_a_editar.get('Nome', ''), key=f'edit_user_nome_{indice}')
          email = st.text_input("E-mail", value=usuario_a_editar.get('Email', ''), disabled=True, key=f'edit_user_email_{indice}') # E-mail não pode ser alterado
          senha = st.text_input("Nova Senha (Deixe em branco para manter a atual)", type='password', key=f'edit_user_senha_{indice}')
          tipo_atual = usuario_a_editar.get('Tipo', 'Cliente')
          tipo_index = ["Cliente", "Administrador"].index(tipo_atual) if tipo_atual in ["Cliente", "Administrador"] else 0
          tipo = st.selectbox("Tipo de Usuário", ["Cliente", "Administrador"], index=tipo_index, key=f'edit_user_tipo_{indice}')

          # Exibe e permite editar categorias de receita personalizadas
          categorias_receita_list = usuario_a_editar.get('categorias_receita', [])
          categorias_receita_str = ", ".join(categorias_receita_list)
          categorias_receita_editada_str = st.text_input("Categorias de Receita (separadas por vírgula)", value=categorias_receita_str, key=f'edit_user_categorias_{indice}')


          submit_edit_user = st.form_submit_button("Salvar Alterações")

          if submit_edit_user:
               if not nome:
                    st.warning("Nome é obrigatório.")
               else:
                    # Processa as categorias de receita editadas
                    categorias_personalizadas_editadas = [c.strip() for c in categorias_receita_editada_str.split(',') if c.strip()]

                    st.session_state['usuarios'][indice]['Nome'] = nome
                    if senha: # Atualiza a senha apenas se uma nova for fornecida
                         st.session_state['usuarios'][indice]['Senha'] = senha # Em uma aplicação real, a senha deve ser hasheada
                    st.session_state['usuarios'][indice]['Tipo'] = tipo
                    st.session_state['usuarios'][indice]['categorias_receita'] = categorias_personalizadas_editadas # Salva as categorias editadas


                    salvar_usuarios()
                    st.success("Usuário atualizado com sucesso!")
                    st.session_state['show_edit_user_modal'] = False
                    st.session_state['editar_usuario_index'] = None
                    st.session_state['editar_usuario_data'] = None
                    st.rerun()

     if st.button("Cancelar", key=f'cancel_edit_user_{indice}'):
          st.session_state['show_edit_user_modal'] = False
          st.session_state['editar_usuario_index'] = None
          st.session_state['editar_usuario_data'] = None
          st.rerun()


# --- Novo formulário de Gerenciamento de Categorias (Apenas para Admin/Usuário Logado) ---
# Adicionar estado para controlar a exibição do formulário de gerenciamento de categorias
if 'show_manage_categories_modal' not in st.session_state:
    st.session_state['show_manage_categories_modal'] = False

def pagina_gerenciar_categorias():
    # Permite que o usuário logado gerencie SUAS categorias de receita personalizadas
    if not st.session_state.get('autenticado'):
        st.warning("Você precisa estar logado para gerenciar categorias.")
        return

    st.title("Gerenciar Categorias de Receita")
    st.info("Aqui você pode adicionar ou remover categorias de receita personalizadas para seus lançamentos.")

    usuario_index = st.session_state.get('usuario_atual_index')
    if usuario_index is None or usuario_index >= len(st.session_state.get('usuarios', [])):
         st.error("Erro: Usuário logado não encontrado.")
         return # Sai se o índice do usuário logado for inválido


    # Acessa a lista de categorias de receita do usuário logado diretamente
    usuario_categorias_receita = st.session_state['usuarios'][usuario_index].get('categorias_receita', [])

    st.subheader("Categorias de Receita Atuais (Padrão + Suas)")
    # Combina as categorias padrão com as do usuário logado para exibição
    todas_unicas_receita_display = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + usuario_categorias_receita))

    if todas_unicas_receita_display:
        st.write(", ".join(todas_unicas_receita_display))
    else:
        st.info("Nenhuma categoria de receita personalizada adicionada ainda.")

    st.markdown("---")
    st.subheader("Adicionar Nova Categoria de Receita Personalizada")

    with st.form(key='add_categoria_form'):
        nova_categoria = st.text_input("Nome da Nova Categoria de Receita")
        submit_add_categoria = st.form_submit_button("Adicionar Categoria")

        if submit_add_categoria:
            if not nova_categoria.strip():
                st.warning("Por favor, insira um nome para a categoria.")
            else:
                 categoria_limpa = nova_categoria.strip()
                 # Verifica se a categoria já existe (case-insensitive e ignorando espaços extras)
                 categorias_existentes_lower = [c.strip().lower() for c in todas_unicas_receita_display]
                 if categoria_limpa.lower() in categorias_existentes_lower:
                     st.warning(f"A categoria '{categoria_limpa}' já existe.")
                 else:
                     # Adiciona a nova categoria à lista de categorias personalizadas do usuário
                     if 'categorias_receita' not in st.session_state['usuarios'][usuario_index]:
                           st.session_state['usuarios'][usuario_index]['categorias_receita'] = []

                     st.session_state['usuarios'][usuario_index]['categorias_receita'].append(categoria_limpa)
                     salvar_usuarios() # Salva a lista de usuários com a nova categoria
                     # Atualiza o estado da sessão com as categorias combinadas para o usuário logado
                     st.session_state['todas_categorias_receita'] = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + st.session_state['usuarios'][usuario_index]['categorias_receita']))
                     st.success(f"Categoria '{categoria_limpa}' adicionada com sucesso!")
                     st.rerun() # Recarrega para atualizar a lista exibida e o selectbox de adição


    st.markdown("---")
    st.subheader("Remover Categoria de Receita Personalizada")

    if usuario_categorias_receita: # Só exibe se houver categorias personalizadas para remover
        # Filtra as categorias que NÃO são padrão para permitir remoção
        categorias_para_remover = [c for c in usuario_categorias_receita if c not in CATEGORIAS_PADRAO_RECEITA]

        if categorias_para_remover:
             categoria_a_remover = st.selectbox("Selecione a Categoria Personalizada para Remover", ["Selecione..."] + categorias_para_remover)

             if categoria_a_remover != "Selecione...":
                 if st.button(f"Remover Categoria '{categoria_a_remover}'", type="secondary"):
                      # Remove a categoria da lista de categorias personalizadas do usuário
                      st.session_state['usuarios'][usuario_index]['categorias_receita'].remove(categoria_a_remover)
                      salvar_usuarios() # Salva a lista de usuários
                      # Atualiza o estado da sessão com as categorias combinadas para o usuário logado
                      st.session_state['todas_categorias_receita'] = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + st.session_state['usuarios'][usuario_index]['categorias_receita']))

                      # Opcional: Verificar lançamentos que usam essa categoria removida
                      # e talvez atribuí-los a "Sem Categoria" ou outra padrão.
                      # Por enquanto, mantemos a categoria nos lançamentos existentes.

                      st.success(f"Categoria '{categoria_a_remover}' removida com sucesso.")
                      st.rerun() # Recarrega para atualizar as listas


    # Botão para fechar o gerenciamento de categorias (se estiver em um modal)
    # if st.button("Voltar para Dashboard"): # Ou outro texto dependendo da navegação
    #      st.session_state['show_manage_categories_modal'] = False
    #      st.rerun()


# --- Funções de Navegação ---

def navegar_para(pagina):
    st.session_state['pagina_atual'] = pagina
    # Ao navegar para outra página, feche os modais/formulários abertos
    st.session_state['show_add_modal'] = False
    st.session_state['show_edit_modal'] = False
    st.session_state['editar_indice'] = None
    st.session_state['editar_lancamento'] = None
    st.session_state['show_edit_user_modal'] = False
    st.session_state['editar_usuario_index'] = None
    st.session_state['editar_usuario_data'] = None
    # st.session_state['show_manage_categories_modal'] = False # Se gerenciar categorias for um modal

    st.rerun()


def pagina_dashboard():
    if not st.session_state.get('autenticado'):
        st.warning("Por favor, faça login para acessar o dashboard.")
        return

    st.title(f"Dashboard Financeiro - Bem-vindo(a), {st.session_state.get('usuario_atual_nome', 'usuário')}")

    # Exibe o resumo financeiro
    exibir_resumo_central()

    # Exibe os lançamentos
    exibir_lancamentos() # Chama a função exibir_lancamentos corrigida

    # O formulário de adicionar/editar/excluir lançamentos está agora incorporado
    # na função exibir_lancamentos ou renderizado condicionalmente abaixo dela.


# --- Layout Principal ---

if st.session_state.get('autenticado'):
    # Barra lateral para navegação e logout
    st.sidebar.title("Menu")
    st.sidebar.button("📊 Dashboard", on_click=navegar_para, args=('dashboard',))

    # Botão de gerenciar usuários apenas para administradores
    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        st.sidebar.button("👥 Gerenciar Usuários", on_click=navegar_para, args=('gerenciar_usuarios',))

    # Botão para gerenciar categorias (visível para usuários autenticados)
    st.sidebar.button("📂 Gerenciar Categorias", on_click=navegar_para, args=('gerenciar_categorias',))


    st.sidebar.markdown("---")
    st.sidebar.button("🚪 Logout", on_click=navegar_para, args=('login',))
else:
    # Se não autenticado, exibe apenas a opção de login
    st.sidebar.title("Menu")
    st.sidebar.button("🔒 Login", on_click=navegar_para, args=('login',))


# --- Roteamento de Páginas ---
if st.session_state['pagina_atual'] == 'login':
    pagina_login()
elif st.session_state['pagina_atual'] == 'dashboard':
    pagina_dashboard()
elif st.session_state['pagina_atual'] == 'gerenciar_usuarios':
    pagina_gerenciar_usuarios()
elif st.session_state['pagina_atual'] == 'gerenciar_categorias':
     pagina_gerenciar_categorias()
