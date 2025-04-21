import streamlit as st
from datetime import datetime
# import json # Não precisamos mais importar json para usuários
import os # Podemos manter para lançamentos, mas USUARIOS_FILE não será usado
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
# USUARIOS_FILE = "usuarios.json" # Não precisamos mais deste arquivo

# --- Funções de Carregamento e Salvamento ---

# --- REMOVIDA a função salvar_usuarios, pois os usuários são hardcoded ---
# def salvar_usuarios():
#     with open(USUARIOS_FILE, "w") as f:
#         json.dump(st.session_state.get('usuarios', []), f)

# --- MODIFICADA a função carregar_usuarios para usar dados hardcoded ---
def carregar_usuarios():
    # Lista de usuários hardcoded no código
    usuarios_hardcoded = [
        {
            "ID": 1,
            "Nome": "Junior Fernandes",
            "Email": "valmirfernandescontabilidade@gmail.com",
            "Senha": "114316", # NUNCA FAÇA ISSO EM PRODUÇÃO! Use hashes!
            "Tipo": "Administrador",
            "categorias_receita": ["Serviços", "Vendas", "Consultoria"] # Categorias personalizadas
        },
         {
            "ID": 2,
            "Nome": "Junior Fernandes",
            "Email": "almirfernandescontabilidade@hotmail.com",
            "Senha": "123456", # NUNCA FAÇA ISSO EM PRODUÇÃO!
            "Tipo": "Cliente",
            "categorias_receita": ["Vendas", "Outras Receitas"] # Categorias personalizadas
        },
         {
            "ID": 3,
            "Nome": "Camila Garcia",
            "Email": "boatardecamila@gmail.com    ",
            "Senha": "123456", # NUNCA FAÇA ISSO EM PRODUÇÃO!
            "Tipo": "Cliente",
            "categorias_receita": ["Serviços"] # Categorias personalizadas
        }
        # Adicione mais usuários aqui conforme necessário
    ]

    # Atribui a lista hardcoded diretamente ao estado da sessão
    st.session_state['usuarios'] = usuarios_hardcoded

    # --- Mantém esta parte para compatibilidade, embora com hardcoded seria melhor garantir que
    #     'categorias_receita' já exista na lista acima ---
    for usuario in st.session_state['usuarios']:
         if 'categorias_receita' not in usuario:
              usuario['categorias_receita'] = []
    # ---------------------------------------------------------------------


# Funções de lançamento (mantidas, pois dependem do arquivo JSON)
def salvar_lancamentos():
    # Garante que 'user_email' está presente antes de salvar
    lancamentos_para_salvar = []
    for lancamento in st.session_state.get("lancamentos", []):
        if 'user_email' not in lancamento:
            # Isso pode acontecer se você tiver dados antigos sem user_email.
            # Neste caso, pode ser necessário adicionar um email padrão ou tratar
            # como um erro, dependendo da lógica de negócio.
            # Por enquanto, vamos adicionar um placeholder se faltar.
            lancamento['user_email'] = 'unknown@user.com'
        lancamentos_para_salvar.append(lancamento)

    try:
        with open(DATA_FILE, "w") as f:
            json.dump(lancamentos_para_salvar, f, indent=4) # Adicionado indent para legibilidade
    except Exception as e:
        st.error(f"Erro ao salvar lançamentos: {e}")


def carregar_lancamentos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                content = f.read()
                if content:
                    lancamentos = json.loads(content)
                    # Garante que cada lançamento tem o campo user_email (para compatibilidade)
                    # Se lançamentos antigos não tiverem, atribui um valor padrão ou trata.
                    for lancamento in lancamentos:
                         if 'user_email' not in lancamento:
                              lancamento['user_email'] = 'unknown@user.com' # Valor padrão para lançamentos sem usuário associado
                    st.session_state["lancamentos"] = lancamentos
                else:
                     st.session_state["lancamentos"] = []
        except json.JSONDecodeError:
            st.error("Erro ao decodificar o arquivo de lançamentos. Criando um novo.")
            st.session_state["lancamentos"] = []
            salvar_lancamentos()
        except Exception as e:
             st.error(f"Erro inesperado ao carregar lançamentos: {e}")
             st.session_state["lancamentos"] = []
             salvar_lancamentos()
    else:
        st.session_state["lancamentos"] = []


# --- Inicialização de Estado ---
if 'usuarios' not in st.session_state:
    # Agora apenas chama a função que carrega os usuários hardcoded
    carregar_usuarios()
    # Não precisa salvar_usuarios() aqui

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
# Carrega usuários *antes* de lançamentos, caso a lógica de lançamentos precise de info do usuário (embora neste código não precise diretamente)
# Isso já é feito acima: if 'usuarios' not in st.session_state: carregar_usuarios()
carregar_lancamentos() # Carrega os lançamentos de 'lancamentos.json'
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


# --- MODIFICADA a função excluir_usuario ---
# Agora ela apenas remove o usuário da lista hardcoded no estado da sessão.
# Nenhuma alteração persistirá após a reinicialização do script.
def excluir_usuario(index):
    if 0 <= index < len(st.session_state.get('usuarios', [])):
        # Remover da lista no estado da sessão
        del st.session_state['usuarios'][index]
        # Como os usuários são hardcoded, não há arquivo JSON para salvar.
        # A exclusão é APENAS para a sessão atual. Ao reiniciar o script, os usuários hardcoded voltam.
        st.warning("Usuário removido da lista (apenas para esta sessão). Usuários hardcoded retornarão ao reiniciar o script.")
        # st.success("Usuário excluído com sucesso!") # Mudei para warning para indicar a transitoriedade
        st.rerun()
    else:
        st.error("Índice de usuário inválido.")


def pagina_login():
    st.title("Login")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    login_button = st.button("Entrar")

    if login_button:
        # Percorre a lista de usuários hardcoded no estado da sessão
        for i, usuario in enumerate(st.session_state.get('usuarios', [])):
            # Compara com os campos 'Email' e 'Senha' da lista hardcoded
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
        # Mantendo a remoção do user_email para o Excel conforme original,
        # mesmo que agora o user_email seja obrigatório ao salvar lançamentos.
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
        # Ajuste o caminho ou nome do arquivo .ttf conforme necessário
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_table = 'Arial_Unicode'
    except Exception as e:
         # st.warning(f"Erro ao carregar fonte personalizada para PDF: {e}. Usando fonte padrão.") # Mantendo o aviso na console
         pdf.set_font("Arial", '', 12)
         font_for_table = 'Arial'


    pdf.set_font("Arial", 'B', 12) # Use negrito da fonte padrão para o título (conforme original)
    report_title = f"Relatório de Lançamentos - {usuario_nome}"
    # Encode/Decode para lidar com acentos usando latin1, se a fonte padrão não suportar unicode
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

        pdf.cell(col_widths[0], 10, data_formatada.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        pdf.cell(col_widths[1], 10, descricao.encode('latin1', 'replace').decode('latin1'), 1, 0, 'L')
        # Garante que a categoria, se vazia, não cause erro no encode
        pdf.cell(col_widths[2], 10, categoria.encode('latin1', 'replace').decode('latin1') if categoria else "", 1, 0, 'C')
        pdf.cell(col_widths[3], 10, tipo.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        pdf.cell(col_widths[4], 10, valor_formatado.encode('latin1', 'replace').decode('latin1'), 1, 0, 'R')

        pdf.ln()

    pdf_output = pdf.output(dest='S')
    return io.BytesIO(pdf_output)


# --- FUNÇÃO para gerar a Demonstração de Resultados em PDF ---
def gerar_demonstracao_resultados_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos. Se não encontrar, usa Arial padrão.
    # Certifique-se de ter um arquivo .ttf (como Arial.ttf) no mesmo diretório do seu script.
    try:
        # Ajuste o caminho ou nome do arquivo .ttf conforme necessário
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
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
    return io.BytesIO(pdf_output)


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
         # Botão para a nova função de exportação da Demonstração de Resultados
         pdf_dr_buffer = gerar_demonstracao_resultados_pdf(lancamentos_para_exibir, usuario_para_pdf_title)
         st.download_button(
            label="📊 Exportar DR PDF",
            data=pdf_dr_buffer,
            file_name=f'demonstracao_resultados_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
         )


    st.markdown("---")

    # Preparar dados para exibição na tabela do Streamlit
    # Remove 'user_email' para não exibir na tabela, mantendo a estrutura original
    lancamentos_para_tabela = []
    for l in lancamentos_para_exibir:
         l_copy = l.copy()
         if 'user_email' in l_copy:
              del l_copy['user_email']
         lancamentos_para_tabela.append(l_copy)

    # Converte para DataFrame para exibição
    df_lancamentos = pd.DataFrame(lancamentos_para_tabela)

    # Formata as colunas para exibição
    if not df_lancamentos.empty:
         # Formata data para exibição DD/MM/AAAA
        if 'Data' in df_lancamentos.columns:
            try:
                 df_lancamentos['Data'] = pd.to_datetime(df_lancamentos['Data']).dt.strftime('%d/%m/%Y')
            except Exception as e:
                 st.warning(f"Erro ao formatar a coluna 'Data' para exibição: {e}")

        # Formata valor para R$ X.XXX,XX
        if 'Valor' in df_lancamentos.columns:
             try:
                df_lancamentos['Valor'] = df_lancamentos['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
             except Exception as e:
                 st.warning(f"Erro ao formatar a coluna 'Valor' para exibição: {e}")

    # Exibe a tabela
    if not df_lancamentos.empty:
        st.dataframe(df_lancamentos, use_container_width=True, hide_index=True)

        # Botões de Ação (Editar/Excluir) - Adicionado tratamento de permissão
        st.subheader("Ações")
        # AUMENTANDO A LARGURA DA COLUNA DE AÇÕES (último valor na lista)
        cols_actions = st.columns([1, 1, 1]) # Colunas para Editar, Excluir, (placeholder)

        # Use um formulário para lidar com as ações de editar/excluir
        # Isso evita problemas de re-renderização com múltiplos botões
        with st.form(key="lancamento_actions_form"):
            st.markdown("Selecione a linha e clique em uma ação:")
            # Seleciona a linha com um radio button ou número
            linha_selecionada_indice = st.number_input(
                 "Número da Linha (a partir de 1)",
                 min_value=1,
                 max_value=len(lancamentos_para_exibir),
                 step=1,
                 key="selected_row_index"
            )
            # Ajusta para índice base 0 para acessar a lista
            indice_real_selecionado = linha_selecionada_indice - 1

            # Verifica se a linha selecionada é válida e se o usuário tem permissão para editar/excluir
            pode_interagir = False
            if 0 <= indice_real_selecionado < len(lancamentos_para_exibir):
                 lancamento_selecionado_data = lancamentos_para_exibir[indice_real_selecionado]
                 is_owner = lancamento_selecionado_data.get('user_email') == st.session_state.get('usuario_atual_email')
                 is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'
                 if is_owner or is_admin:
                      pode_interagir = True
                 else:
                     st.warning(f"Você não tem permissão para interagir com o lançamento na linha {linha_selecionada_indice}.")


            col_editar, col_excluir = st.columns(2) # Duas colunas dentro do formulário

            with col_editar:
                 edit_button = st.form_submit_button("✏️ Editar Lançamento", disabled=not pode_interagir)
            with col_excluir:
                 # Adicionado kind="secondary" para o estilo CSS de exclusão (ver CSS no início)
                 delete_button = st.form_submit_button("🗑️ Excluir Lançamento", disabled=not pode_interagir, kind="secondary")


            # --- Lógica de Ações (dentro do formulário) ---
            if edit_button and pode_interagir:
                # Define variáveis de estado para mostrar o modal de edição
                st.session_state['show_edit_modal'] = True
                st.session_state['editar_indice'] = indice_real_selecionado
                # Salva os dados atuais do lançamento no estado para preencher o formulário de edição
                st.session_state['editar_lancamento'] = lancamentos_para_exibir[indice_real_selecionado]
                st.rerun()

            if delete_button and pode_interagir:
                # Remove o lançamento da lista no estado da sessão
                del st.session_state["lancamentos"][indice_real_selecionado]
                salvar_lancamentos()
                st.success(f"Lançamento da linha {linha_selecionada_indice} excluído com sucesso!")
                st.rerun()

    st.markdown("---") # Separador visual

# --- FUNÇÃO para a página de Gestão de Usuários (Apenas para Admin) ---
# --- MODIFICADA para gerenciar a lista hardcoded no estado da sessão ---
def pagina_gestao_usuarios():
    if st.session_state.get('tipo_usuario_atual') != 'Administrador':
        st.error("Você não tem permissão para acessar esta página.")
        return

    st.title("Gestão de Usuários (Admin)")
    st.warning("A gestão de usuários é apenas para esta sessão, pois os usuários são hardcoded. Ao reiniciar o script, a lista hardcoded original será restaurada.")

    # Exibir lista de usuários
    st.subheader("Lista de Usuários")
    usuarios_df = pd.DataFrame(st.session_state.get('usuarios', []))

    # Oculta a coluna de senha por segurança (mesmo que hardcoded)
    if not usuarios_df.empty:
        # Mantém a coluna 'Senha' presente no DataFrame, mas a oculta na exibição
        # para que a lógica de exclusão/edição por índice funcione com o DataFrame subjacente
        column_config = {"Senha": st.column_config.Column(disabled=True, width="small")} # Oculta a coluna Senha
        # Remove 'categorias_receita' da exibição para simplificar
        if 'categorias_receita' in usuarios_df.columns:
             column_config['categorias_receita'] = st.column_config.Column(disabled=True, width="small")

        st.dataframe(usuarios_df, use_container_width=True, hide_index=False, column_config=column_config) # Exibe o índice

        # --- Ações de Usuário (Editar/Excluir) ---
        st.subheader("Ações de Usuário")
        # Formulário para ações de usuário
        with st.form(key="user_actions_form"):
            st.markdown("Selecione o Índice do Usuário (coluna 0 na tabela) e clique em uma ação:")
            user_index_input = st.number_input(
                "Índice do Usuário",
                min_value=0,
                max_value=len(st.session_state.get('usuarios', [])) - 1,
                step=1,
                format="%d", # Garante que seja exibido como inteiro
                key="selected_user_index_input"
            )

            col_editar_user, col_excluir_user = st.columns(2)

            with col_editar_user:
                edit_user_button = st.form_submit_button("✏️ Editar Usuário")
            with col_excluir_user:
                 # Adicionado kind="secondary" para o estilo CSS de exclusão
                delete_user_button = st.form_submit_button("🗑️ Excluir Usuário", kind="secondary")


            # Lógica de Ações de Usuário (dentro do formulário)
            if edit_user_button:
                 if 0 <= user_index_input < len(st.session_state.get('usuarios', [])):
                      st.session_state['show_edit_modal_user'] = True
                      st.session_state['editar_usuario_index'] = user_index_input
                      # Copia os dados para o estado para o formulário de edição
                      st.session_state['editar_usuario_data'] = st.session_state['usuarios'][user_index_input].copy()
                      st.rerun()
                 else:
                      st.error("Índice de usuário inválido.")

            if delete_user_button:
                 # Chama a função de exclusão modificada
                 if 0 <= user_index_input < len(st.session_state.get('usuarios', [])):
                    excluir_usuario(user_index_input)
                 else:
                    st.error("Índice de usuário inválido.")


    # --- Formulário de Adição de Usuário (fora das ações de tabela) ---
    st.subheader("Adicionar Novo Usuário")
    # Usa um formulário separado para adição
    with st.form(key="add_user_form"):
        novo_nome = st.text_input("Nome do Novo Usuário", key="add_user_nome")
        novo_email = st.text_input("E-mail do Novo Usuário", key="add_user_email")
        novo_senha = st.text_input("Senha do Novo Usuário", type="password", key="add_user_senha") # NUNCA FAÇA ISSO!
        novo_tipo = st.selectbox("Tipo de Usuário", ["Cliente", "Administrador"], key="add_user_tipo")
        # Campo para categorias de receita (opcional, texto separado por vírgulas)
        novo_categorias_receita_str = st.text_input("Categorias de Receita (separar por vírgula, ex: Vendas,Serviços)", key="add_user_categorias_receita")


        add_user_button = st.form_submit_button("Adicionar Usuário")

        if add_user_button:
            if novo_nome and novo_email and novo_senha and novo_tipo:
                # Verifica se o email já existe
                email_existente = any(u['Email'] == novo_email for u in st.session_state.get('usuarios', []))
                if email_existente:
                    st.warning(f"O e-mail '{novo_email}' já está em uso.")
                else:
                    # Processa as categorias de receita
                    categorias_list = [cat.strip() for cat in novo_categorias_receita_str.split(',') if cat.strip()]

                    novo_usuario = {
                        # Gere um ID simples (incrementando do último, ou use um UUID real)
                        "ID": len(st.session_state.get('usuarios', [])) + 1,
                        "Nome": novo_nome,
                        "Email": novo_email,
                        "Senha": novo_senha, # NUNCA FAÇA ISSO!
                        "Tipo": novo_tipo,
                        "categorias_receita": categorias_list # Salva como lista
                    }
                    # Adiciona à lista hardcoded no estado da sessão
                    st.session_state['usuarios'].append(novo_usuario)
                    # Como os usuários são hardcoded, não há arquivo JSON para salvar.
                    st.success("Usuário adicionado à lista (apenas para esta sessão). Usuários hardcoded retornarão ao reiniciar o script.")
                    st.rerun()
            else:
                st.warning("Por favor, preencha todos os campos para adicionar um usuário.")

    # --- Modal de Edição de Usuário (usando expander ou placeholder/modal) ---
    # Simulação de modal com expander
    # Verifica se o estado indica que o modal de edição deve ser exibido para um usuário
    if st.session_state.get('show_edit_modal_user') and st.session_state.get('editar_usuario_index') is not None:
        editar_idx = st.session_state['editar_usuario_index']
        usuario_a_editar = st.session_state['editar_usuario_data'] # Use a cópia no estado

        if usuario_a_editar:
            with st.expander(f"Editar Usuário: {usuario_a_editar.get('Nome')}", expanded=True):
                 # Formulário para edição
                 with st.form(key=f"edit_user_form_{editar_idx}"):
                    edited_nome = st.text_input("Nome", value=usuario_a_editar.get("Nome", ""), key=f"edit_user_nome_{editar_idx}")
                    edited_email = st.text_input("E-mail", value=usuario_a_editar.get("Email", ""), key=f"edit_user_email_{editar_idx}")
                    # Cuidado: Editar senha assim não é seguro. Deveria ser um campo separado para redefinir senha.
                    # Mantendo a estrutura original, mas com ressalva.
                    edited_senha = st.text_input("Senha", value=usuario_a_editar.get("Senha", ""), type="password", key=f"edit_user_senha_{editar_idx}") # NUNCA FAÇA ISSO!
                    edited_tipo = st.selectbox(
                        "Tipo de Usuário",
                        ["Cliente", "Administrador"],
                        index=["Cliente", "Administrador"].index(usuario_a_editar.get("Tipo", "Cliente")),
                        key=f"edit_user_tipo_{editar_idx}"
                    )
                    # Edição de categorias de receita (converte lista para string)
                    categorias_str_initial = ", ".join(usuario_a_editar.get('categorias_receita', []))
                    edited_categorias_receita_str = st.text_input(
                        "Categorias de Receita (separar por vírgula)",
                        value=categorias_str_initial,
                        key=f"edit_user_categorias_receita_{editar_idx}"
                    )


                    col_save_user, col_cancel_user = st.columns(2)
                    with col_save_user:
                         save_user_button = st.form_submit_button("Salvar Alterações")
                    with col_cancel_user:
                         cancel_edit_user_button = st.form_submit_button("Cancelar")

                    if save_user_button:
                         if edited_nome and edited_email and edited_senha and edited_tipo:
                              # Verifica se o email editado já existe para OUTRO usuário
                              email_existente_outro = any(
                                  u['Email'] == edited_email for i, u in enumerate(st.session_state.get('usuarios', [])) if i != editar_idx
                              )
                              if email_existente_outro:
                                  st.warning(f"O e-mail '{edited_email}' já está em uso por outro usuário.")
                              else:
                                  # Processa as categorias de receita editadas
                                  edited_categorias_list = [cat.strip() for cat in edited_categorias_receita_str.split(',') if cat.strip()]

                                  # Atualiza o usuário na lista hardcoded no estado da sessão
                                  st.session_state['usuarios'][editar_idx] = {
                                      "ID": usuario_a_editar.get("ID"), # Mantém o ID original
                                      "Nome": edited_nome,
                                      "Email": edited_email,
                                      "Senha": edited_senha, # NUNCA FAÇA ISSO!
                                      "Tipo": edited_tipo,
                                      "categorias_receita": edited_categorias_list
                                  }
                                  # Como os usuários são hardcoded, não há arquivo JSON para salvar.
                                  st.success("Usuário atualizado na lista (apenas para esta sessão). Usuários hardcoded retornarão ao reiniciar o script.")

                                  # Se o usuário editado for o usuário logado, atualiza as info de sessão
                                  if st.session_state.get('usuario_atual_index') == editar_idx:
                                        st.session_state['usuario_atual_email'] = edited_email
                                        st.session_state['usuario_atual_nome'] = edited_nome
                                        st.session_state['tipo_usuario_atual'] = edited_tipo
                                        # Atualiza as categorias de receita do usuário logado
                                        todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + edited_categorias_list))
                                        st.session_state['todas_categorias_receita'] = todas_unicas_receita


                                  st.session_state['show_edit_modal_user'] = False
                                  st.session_state['editar_usuario_index'] = None
                                  st.session_state['editar_usuario_data'] = None
                                  st.rerun()
                         else:
                             st.warning("Por favor, preencha todos os campos para editar o usuário.")

                    if cancel_edit_user_button:
                         st.session_state['show_edit_modal_user'] = False
                         st.session_state['editar_usuario_index'] = None
                         st.session_state['editar_usuario_data'] = None
                         st.rerun()


# --- Navegação e Renderização de Páginas ---

def renderizar_pagina():
    if not st.session_state.get('autenticado'):
        pagina_login()
    else:
        # Adiciona botões de navegação
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Dashboard"):
                st.session_state['pagina_atual'] = 'dashboard'
                st.rerun()
        with col2:
            # Botão de Gestão de Usuários apenas para Admin
            if st.session_state.get('tipo_usuario_atual') == 'Administrador':
                if st.button("Gerenciar Usuários"):
                    st.session_state['pagina_atual'] = 'gerenciar_usuarios'
                    # Fecha modais de lancamento ao navegar
                    st.session_state['show_add_modal'] = False
                    st.session_state['show_edit_modal'] = False
                    st.rerun()
        with col3:
            if st.button("Sair"):
                # Reseta o estado de autenticação e variáveis de usuário
                st.session_state['autenticado'] = False
                st.session_state['usuario_atual_email'] = None
                st.session_state['usuario_atual_nome'] = None
                st.session_state['tipo_usuario_atual'] = None
                st.session_state['usuario_atual_index'] = None
                st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy() # Reseta categorias
                # Fecha modais ao sair
                st.session_state['show_add_modal'] = False
                st.session_state['show_edit_modal'] = False
                st.session_state['show_edit_modal_user'] = False # Fecha modal de usuário também
                st.session_state['editar_usuario_index'] = None
                st.session_state['editar_usuario_data'] = None
                st.rerun()

        st.markdown("---") # Separador

        # Renderiza a página selecionada
        if st.session_state['pagina_atual'] == 'dashboard':
            st.title("Dashboard Financeiro")
            exibir_resumo_central()
            # Só renderiza os formulários de lançamento se não houver modais de edição/adição ativos
            if not st.session_state.get('show_add_modal') and not st.session_state.get('show_edit_modal'):
                 # Botão para abrir o formulário de adicionar lançamento
                 if st.button("➕ Adicionar Lançamento"):
                      st.session_state['show_add_modal'] = True
                      st.session_state['editar_indice'] = None # Garante que o modal de edição está fechado
                      st.rerun()
                 exibir_lancamentos()
            elif st.session_state.get('show_add_modal'):
                 render_add_lancamento_form() # Renderiza o formulário de adição
            elif st.session_state.get('show_edit_modal'):
                 render_edit_lancamento_form() # Renderiza o formulário de edição

        elif st.session_state['pagina_atual'] == 'gerenciar_usuarios':
             pagina_gestao_usuarios() # Renderiza a página de gestão de usuários


# --- Execução Principal ---
renderizar_pagina()
