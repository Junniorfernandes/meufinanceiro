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

# Função para exportar lançamentos para PDF (lista detalhada) - CORRIGIDA
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
    # Encode para latin1 e decode para latin1 para tentar lidar com acentos de forma básica na célula de título
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

        # Encode para latin1 e decode para latin1 para tentar lidar com acentos nos dados da tabela
        pdf.cell(col_widths[0], 10, data_formatada.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        pdf.cell(col_widths[1], 10, descricao.encode('latin1', 'replace').decode('latin1'), 1, 0, 'L')
        pdf.cell(col_widths[2], 10, categoria.encode('latin1', 'replace').decode('latin1') if categoria else "", 1, 0, 'C')
        pdf.cell(col_widths[3], 10, tipo.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        pdf.cell(col_widths[4], 10, valor_formatado.encode('latin1', 'replace').decode('latin1'), 1, 0, 'R')

        pdf.ln()

    pdf_output = pdf.output(dest='S')

    # CORREÇÃO: Codificar a string de saída para bytes
    pdf_output_bytes = pdf_output.encode('latin1') # Use a codificação 'latin1'

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
    pdf_output = pdf.output(dest='S')
    # CORREÇÃO: Codificar a string de saída para bytes
    pdf_output_bytes = pdf_output.encode('latin1') # Use a codificação 'latin1'

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
             label="📄 Exportar Lista Detalhada PDF",
             data=pdf_lista_buffer,
             file_name=f'lista_lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
             mime='application/pdf'
         )

    with col_pdf_dr:
         # Botão para a nova função de exportação da Demonstração de Resultados
         pdf_dr_buffer = gerar_demonstracao_resultados_pdf(lancamentos_para_exibir, usuario_para_pdf_title)
         st.download_button(
             label="📊 Exportar DR PDF",
             data=pdf_dr_buffer,
             file_name=f'demonstracao_resultados_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
             mime='application/pdf'
         )


    st.markdown("---")


    # --- Exibição da Tabela de Lançamentos com Botões de Ação ---
    st.subheader("Lista de Lançamentos")

    if lancamentos_para_exibir:
        # Aumentando a largura da coluna de Ações
        colunas = st.columns([0.1, 0.2, 0.3, 0.2, 0.2, 0.2, 0.3]) # Ajuste as proporções conforme necessário

        headers = ["#", "Data", "Descrição", "Categoria", "Tipo", "Valor", "Ações"]
        for col, header in zip(colunas, headers):
            col.write(f"**{header}**")

        # Itera sobre a lista filtrada/ordenada, usando enumerate para o índice
        for index, lancamento in enumerate(lancamentos_para_exibir):
            # Precisamos encontrar o índice ORIGINAL do lançamento na lista completa
            # para poder editar/excluir corretamente.
            # Buscamos o lançamento na lista COMPLETA pelo seu conteúdo.
            try:
                original_index = st.session_state["lancamentos"].index(lancamento)
            except ValueError:
                # Se por algum motivo não encontrar, pulamos ou tratamos o erro
                continue # Pula este lançamento se não for encontrado na lista original


            col1, col2, col3, col4, col5, col6, col7 = st.columns([0.1, 0.2, 0.3, 0.2, 0.2, 0.2, 0.3])

            with col1:
                st.write(original_index + 1) # Número da linha

            with col2:
                try:
                    data_formatada = datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y")
                except ValueError:
                    data_formatada = lancamento.get("Data", "Data Inválida")
                st.write(data_formatada)

            with col3:
                st.write(lancamento.get("Descrição", ""))

            with col4:
                # Exibe a categoria (vazia se não for receita no original)
                st.write(lancamento.get("Categorias", ""))

            with col5:
                st.write(lancamento.get("Tipo de Lançamento", ""))

            with col6:
                st.write(f"R$ {lancamento.get('Valor', 0.0):.2f}".replace('.', ','))

            with col7:
                # Container para os botões de ação para que fiquem na mesma coluna
                action_container = st.container()
                col_edit, col_delete = action_container.columns(2)


                is_owner = lancamento.get('user_email') == st.session_state.get('usuario_atual_email')
                is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'


                # Apenas o proprietário ou administrador pode editar/excluir
                if is_owner or is_admin:
                    with col_edit:
                        # Botão para editar
                        if st.button("✏️", key=f"edit_{original_index}"):
                            st.session_state['editar_indice'] = original_index
                            st.session_state['editar_lancamento'] = lancamento # Armazena os dados atuais para o formulário
                            st.session_state['show_edit_modal'] = True
                            st.rerun()

                    with col_delete:
                        # Botão para excluir (usa kind="secondary" para o estilo vermelho)
                        if st.button("🗑️", key=f"delete_{original_index}", kind="secondary"):
                            # Exclui da lista de lançamentos
                            del st.session_state["lancamentos"][original_index]
                            salvar_lancamentos()
                            st.success("Lançamento excluído com sucesso!")
                            st.rerun() # Recarrega a página para atualizar a lista
                else:
                    with col_edit:
                        st.empty() # Garante que o espaço fica vazio para não-proprietários/não-admins
                    with col_delete:
                         st.empty()


    st.markdown("---") # Linha separadora após a lista de lançamentos


def exibir_gestao_usuarios():
    if st.session_state.get('tipo_usuario_atual') != 'Administrador':
        st.error("Acesso negado. Apenas administradores podem gerenciar usuários.")
        return

    st.subheader("Gestão de Usuários")

    # Formulário para adicionar novo usuário
    with st.expander("Adicionar Novo Usuário"):
        with st.form("add_usuario_form", clear_on_submit=True):
            novo_nome = st.text_input("Nome do Usuário")
            novo_email = st.text_input("E-mail do Usuário")
            nova_senha = st.text_input("Senha", type="password")
            novo_tipo = st.selectbox("Tipo de Usuário", ["Cliente", "Administrador"])

            submitted = st.form_submit_button("Adicionar Usuário")

            if submitted:
                if novo_email and nova_senha and novo_nome and novo_tipo:
                    # Verifica se o email já existe
                    if any(u['Email'] == novo_email for u in st.session_state.get('usuarios', [])):
                        st.warning("E-mail já cadastrado.")
                    else:
                        novo_usuario = {
                            "Nome": novo_nome,
                            "Email": novo_email,
                            "Senha": nova_senha,
                            "Tipo": novo_tipo,
                            'categorias_receita': CATEGORIAS_PADRAO_RECEITA.copy() # Adiciona categorias padrão ao novo usuário
                        }
                        st.session_state['usuarios'].append(novo_usuario)
                        salvar_usuarios()
                        st.success(f"Usuário '{novo_nome}' adicionado com sucesso!")
                        st.rerun()
                else:
                    st.warning("Por favor, preencha todos os campos para adicionar um usuário.")

    st.markdown("---")

    # Exibição e edição de usuários existentes
    st.subheader("Lista de Usuários")
    usuarios = st.session_state.get('usuarios', [])

    if not usuarios:
        st.info("Nenhum usuário cadastrado ainda.")
    else:
        # Aumentando a largura da coluna de Categorias de Receita e Ações
        colunas_usuarios = st.columns([0.1, 0.2, 0.3, 0.15, 0.3, 0.3]) # Ajuste as proporções conforme necessário

        headers_usuarios = ["#", "Nome", "E-mail", "Tipo", "Categorias Receita", "Ações"]
        for col, header in zip(colunas_usuarios, headers_usuarios):
            col.write(f"**{header}**")

        for index, usuario in enumerate(usuarios):
            col1_u, col2_u, col3_u, col4_u, col5_u, col6_u = st.columns([0.1, 0.2, 0.3, 0.15, 0.3, 0.3])

            with col1_u:
                st.write(index + 1)

            with col2_u:
                st.write(usuario.get("Nome", ""))

            with col3_u:
                st.write(usuario.get("Email", ""))

            with col4_u:
                st.write(usuario.get("Tipo", ""))

            with col5_u:
                # Exibe as categorias de receita personalizadas, se existirem
                cats = usuario.get('categorias_receita', [])
                if cats:
                    st.write(", ".join(cats))
                else:
                    st.write("Nenhuma") # Ou um placeholder

            with col6_u:
                action_container_u = st.container()
                col_edit_u, col_delete_u = action_container_u.columns(2)

                # Não permite excluir o próprio usuário logado (para evitar se deslogar sem querer)
                if usuario.get('Email') != st.session_state.get('usuario_atual_email'):
                    with col_edit_u:
                        if st.button("✏️", key=f"edit_user_{index}"):
                            # Armazena os dados do usuário para edição
                            st.session_state['editar_usuario_index'] = index
                            st.session_state['editar_usuario_data'] = usuario
                            # Não usamos um modal separado para edição de usuário na estrutura original,
                            # mas podemos renderizar um formulário de edição condicionalmente.
                            st.rerun() # Recarrega para exibir o formulário de edição

                    with col_delete_u:
                        if st.button("🗑️", key=f"delete_user_{index}", kind="secondary"):
                            excluir_usuario(index)
                else:
                    with col_edit_u:
                        st.write("👤") # Ícone para indicar usuário atual (opcional)
                    with col_delete_u:
                        st.empty() # Espaço vazio para o botão de excluir


    # Formulário de Edição de Usuário (exibido condicionalmente)
    if st.session_state.get('editar_usuario_index') is not None:
        edit_index = st.session_state['editar_usuario_index']
        usuario_a_editar = st.session_state.get('editar_usuario_data')

        if usuario_a_editar:
            st.markdown("---")
            st.subheader(f"Editar Usuário: {usuario_a_editar.get('Nome', 'Desconhecido')}")

            with st.form(key=f"edit_usuario_form_{edit_index}"):
                edit_nome = st.text_input("Nome", value=usuario_a_editar.get("Nome", ""), key=f"edit_user_name_{edit_index}")
                # Email não é editável (usado como chave única)
                st.text_input("E-mail", value=usuario_a_editar.get("Email", ""), disabled=True, key=f"edit_user_email_{edit_index}")
                edit_senha = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password", key=f"edit_user_senha_{edit_index}")
                edit_tipo = st.selectbox(
                    "Tipo de Usuário",
                    ["Cliente", "Administrador"],
                    index=["Cliente", "Administrador"].index(usuario_a_editar.get("Tipo", "Cliente")),
                    key=f"edit_user_type_{edit_index}"
                )

                # Edição de Categorias de Receita do Usuário
                current_user_cats = usuario_a_editar.get('categorias_receita', [])
                # Remove duplicatas e mantém a ordem das originais + padrão para exibição
                all_available_cats = list(dict.fromkeys(current_user_cats + CATEGORIAS_PADRAO_RECEITA))

                edited_categorias_receita = st.multiselect(
                    "Categorias de Receita Personalizadas (selecione ou adicione)",
                    options=all_available_cats,
                    default=current_user_cats,
                    key=f"edit_user_cats_multi_{edit_index}"
                )
                # Campo para adicionar novas categorias de receita
                new_cat_receita = st.text_input("Adicionar Nova Categoria de Receita", key=f"add_new_cat_receita_{edit_index}")
                if st.button("Adicionar", key=f"btn_add_new_cat_receita_{edit_index}"):
                    if new_cat_receita and new_cat_receita not in edited_categorias_receita:
                        # Adiciona a nova categoria à lista que será salva
                        edited_categorias_receita.append(new_cat_receita)
                        # Atualiza o estado para refletir a nova categoria no multiselect e no salvamento
                        st.session_state[f"edit_user_cats_multi_{edit_index}"] = edited_categorias_receita
                        st.success(f"Categoria '{new_cat_receita}' adicionada para este usuário. Salve as alterações.")
                        st.rerun() # Recarrega para atualizar o multiselect

                # Mantendo a estrutura original: sem gestão de categorias de despesa por usuário

                col_save_u, col_cancel_u = st.columns(2)
                with col_save_u:
                    submit_edit_user = st.form_submit_button("Salvar Usuário")
                with col_cancel_u:
                    cancel_edit_user = st.form_submit_button("Cancelar")


                if submit_edit_user:
                    if edit_nome and edit_tipo:
                        # Atualiza os dados do usuário
                        st.session_state['usuarios'][edit_index]['Nome'] = edit_nome
                        if edit_senha: # Só atualiza a senha se um novo valor for fornecido
                            st.session_state['usuarios'][edit_index]['Senha'] = edit_senha
                        st.session_state['usuarios'][edit_index]['Tipo'] = edit_tipo
                        # Salva as categorias de receita editadas (lista de strings)
                        st.session_state['usuarios'][edit_index]['categorias_receita'] = edited_categorias_receita

                        salvar_usuarios()
                        st.success(f"Usuário '{edit_nome}' atualizado com sucesso!")
                        # Limpa o estado de edição
                        st.session_state['editar_usuario_index'] = None
                        st.session_state['editar_usuario_data'] = None
                        st.rerun()
                    else:
                        st.warning("Nome e Tipo de Usuário são obrigatórios.")

                if cancel_edit_user:
                    # Limpa o estado de edição sem salvar
                    st.session_state['editar_usuario_index'] = None
                    st.session_state['editar_usuario_data'] = None
                    st.rerun()


def pagina_dashboard():
    if not st.session_state.get('autenticado'):
        st.warning("Por favor, faça login para acessar o dashboard.")
        pagina_login()
        return

    st.title(f"Dashboard Financeiro - {st.session_state.get('usuario_atual_nome', 'Usuário')}")

    # Adiciona botões de navegação no sidebar
    st.sidebar.title("Navegação")
    if st.sidebar.button("Dashboard", key="nav_dashboard_sidebar"):
        st.session_state['pagina_atual'] = 'dashboard'
        # Reset modals when navigating
        st.session_state['show_add_modal'] = False
        st.session_state['show_edit_modal'] = False
        st.session_state['editar_indice'] = None
        st.session_state['editar_lancamento'] = None
        st.session_state['editar_usuario_index'] = None
        st.session_state['editar_usuario_data'] = None
        st.rerun()

    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        if st.sidebar.button("Gestão de Usuários", key="nav_users_sidebar"):
            st.session_state['pagina_atual'] = 'gestao_usuarios'
            # Reset modals when navigating
            st.session_state['show_add_modal'] = False
            st.session_state['show_edit_modal'] = False
            st.session_state['editar_indice'] = None
            st.session_state['editar_lancamento'] = None
            st.session_state['editar_usuario_index'] = None
            st.session_state['editar_usuario_data'] = None
            st.rerun()


    if st.sidebar.button("Sair", key="nav_logout_sidebar"):
        # Limpa todos os estados relevantes para logout
        st.session_state['autenticado'] = False
        st.session_state['usuario_atual_email'] = None
        st.session_state['usuario_atual_nome'] = None
        st.session_state['tipo_usuario_atual'] = None
        st.session_state['usuario_atual_index'] = None
        st.session_state['pagina_atual'] = 'login' # Redireciona para a página de login
        # Garante que as categorias do próximo usuário logado serão carregadas corretamente
        st.session_state.pop('todas_categorias_receita', None)
        # Reset modals on logout
        st.session_state['show_add_modal'] = False
        st.session_state['show_edit_modal'] = False
        st.session_state['editar_indice'] = None
        st.session_state['editar_lancamento'] = None
        st.session_state['editar_usuario_index'] = None
        st.session_state['editar_usuario_data'] = None

        st.rerun()

    st.markdown("---")


    # Renderiza o formulário de adicionar lançamento se show_add_modal for True
    if st.session_state.get('show_add_modal'):
        render_add_lancamento_form()

    # Renderiza o formulário de editar lançamento se show_edit_modal for True
    if st.session_state.get('show_edit_modal'):
        render_edit_lancamento_form()

    # Renderiza o botão "Adicionar Lançamento" APENAS se nenhum modal estiver ativo
    if not st.session_state.get('show_add_modal') and not st.session_state.get('show_edit_modal'):
        if st.button("➕ Adicionar Novo Lançamento"):
            st.session_state['show_add_modal'] = True
            st.rerun() # Recarrega para exibir o formulário de adição


    st.markdown("---")

    exibir_resumo_central()
    exibir_lancamentos() # Chama a função exibir_lancamentos corrigida


# --- Lógica Principal de Navegação ---
if st.session_state.get('pagina_atual') == 'login':
    pagina_login()
elif st.session_state.get('pagina_atual') == 'dashboard':
    pagina_dashboard()
elif st.session_state.get('pagina_atual') == 'gestao_usuarios':
    exibir_gestao_usuarios()
