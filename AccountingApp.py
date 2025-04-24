import streamlit as st
from datetime import datetime
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import io
import uuid
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
        
     # --- INCLUA O CÓDIGO DO ADMINISTRADOR AQUI ---
    novo_admin = {
        "Nome": "Junior Fernandes",
        "Email": "valmirfernandescontabilidade@gmail.com",
        "Senha": "114316", # Cuidado: Armazenar senhas em texto plano não é seguro. Considere usar hashing de senha.
        "Tipo": "Administrador",
        "categorias_receita": [],
        "SignatarioNome": "", # Pode preencher se necessário
        "SignatarioCargo": "" # Pode preencher se necessário
    }

    # Verifica se o usuário já existe antes de adicionar para evitar duplicação
    if not any(u.get('Email') == novo_admin['Email'] for u in st.session_state.get('usuarios', [])):
        st.session_state['usuarios'].append(novo_admin)
        salvar_usuarios() # Salva a lista atualizada de usuários de volta no arquivo
    # --- FIM DA INCLUSÃO ---


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
CATEGORIAS_PADRAO_RECEITA = ["Serviços", "Vendas"]
# O código original não tinha categorias padrão de despesa ou gestão delas por usuário.
# A Demonstração de Resultados agrupará despesas pelo campo 'Categorias' existente,
# mas sem gestão específica de categorias de despesa no UI.

# Inicializa a lista de categorias disponíveis para o usuário logado (será atualizada no login)
if 'todas_categorias_receita' not in st.session_state:
    st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy()  # Começa com as padrão


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
    # Escolhe o logo com base no tema carregado
    theme_base = st.get_option("theme.base")
    logo_path = "logo_dark.png" if theme_base == "dark" else "logo_light.png"
    st.image(logo_path, width=200)

    st.title("Junior Fernandes")
    st.title("Acesse seu Financeiro")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    # Botões lado a lado com o botão de link à esquerda
    col1, col2 = st.columns([1, 1])

    with col2:
        st.markdown(
            """
            <style>
            /* Define uma classe para o botão e move os estilos inline para cá */
            .button-hover-effect {
                width: 100%;
                padding: 8px;
                background-color: #003548; /* Cor de fundo padrão */
                color: #ffffff; /* Cor do texto padrão */
                border-radius: 8px;
                border: none;
                cursor: pointer; /* Adiciona cursor de mão para indicar que é clicável */
                text-align: center; /* Centraliza o texto */
                text-decoration: none; /* Remove sublinhado do link se aplicado ao a */
                display: inline-block; /* Necessário para aplicar padding e width corretamente */
                font-size: 16px; /* Opcional: define um tamanho de fonte */
                transition: background-color 0.3s ease; /* Transição suave para o hover */
            }

            /* Define os estilos para quando o mouse estiver sobre o botão */
            .button-hover-effect:hover {
                background-color: red; /* Fundo vermelho no hover */
                color: white; /* Letras brancas no hover (redundante se já for branco, mas explícito) */
            }
            </style>

            <a href='https://juniorfernandes.com/produtos' target='_blank'>
                <button class="button-hover-effect">
                    Tenha acesso à todos os produtos
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col1:
        login_button = st.button("Acessar meu financeiro", key="botao_entrar_login")

    if login_button:
        for i, usuario in enumerate(st.session_state.get('usuarios', [])):
            if usuario.get('Email') == email and usuario.get('Senha') == senha:
                st.session_state['autenticado'] = True
                st.session_state['usuario_atual_email'] = usuario.get('Email')
                st.session_state['usuario_atual_nome'] = usuario.get('Nome')
                st.session_state['tipo_usuario_atual'] = usuario.get('Tipo')
                st.session_state['usuario_atual_index'] = i

                usuario_categorias_receita = usuario.get('categorias_receita', [])
                todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + usuario_categorias_receita))
                st.session_state['todas_categorias_receita'] = todas_unicas_receita

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
            descricao = st.text_input("Descrição do lançamento", key="add_lanc_descricao_form")
            # Captura o tipo de lançamento selecionado primeiro
            tipo = st.selectbox("Tipo de Lançamento", ["Receita", "Despesa"], key="add_lanc_tipo_form")

            # Cria um placeholder para a Categoria
            categoria_placeholder = st.empty()

            categorias = ""  # Inicializa a variável de categoria
            # Só exibe o campo Categoria dentro do placeholder se o tipo for Receita (conforme original)
            if tipo == "Receita":
                # Usa a lista combinada de categorias de receita do usuário logado
                categorias_disponiveis = st.session_state.get('todas_categorias_receita', CATEGORIAS_PADRAO_RECEITA)
                categorias = categoria_placeholder.selectbox(
                    "Categoria de Receitas",
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
                            "Categorias": categorias,  # Salva a categoria (será vazia se não for Receita no original)
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
            descricao = st.text_input("Descrição", lancamento.get("Descrição", ""),
                                      key=f"edit_lanc_descricao_form_{indice}")
            # Captura o tipo de lançamento selecionado primeiro
            tipo = st.selectbox(
                "Tipo de Lançamento",
                ["Receita", "Despesa"],
                index=["Receita", "Despesa"].index(lancamento.get("Tipo de Lançamento", "Receita")),
                key=f"edit_lanc_tipo_form_{indice}",
            )

            # Cria um placeholder para a Categoria
            categoria_placeholder = st.empty()

            categoria = ""  # Inicializa a variável de categoria
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
                "Valor", value=lancamento.get("Valor", 0.0), format="%.2f", min_value=0.0,
                key=f"edit_lanc_valor_form_{indice}"
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
                            "Categorias": categoria,  # Salva a categoria (será vazia se não for Receita no original)
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

    lancamentos_para_resumo = []  # Inicializa a lista a ser usada para o resumo

    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        # --- ADICIONAR LÓGICA DE FILTRAGEM BASEADA NO SELECTBOX ---
        # Pega a seleção atual do selectbox de usuários (definido em exibir_lancamentos)
        usuario_selecionado_nome = st.session_state.get("selectbox_usuario_lancamentos", "Todos os Usuários")

        if usuario_selecionado_nome == "Todos os Usuários":
            lancamentos_para_resumo = st.session_state.get("lancamentos", [])
            st.info("Exibindo resumo de todos os lançamentos.")
        else:
            # Encontre o e-mail do usuário selecionado pelo nome
            usuario_selecionado_email = None
            for u in st.session_state.get('usuarios', []):
                if u.get('Nome', 'Usuário Sem Nome') == usuario_selecionado_nome:
                    usuario_selecionado_email = u.get('Email')
                    break

            if usuario_selecionado_email:
                # Filtra lançamentos pelo e-mail do usuário selecionado para o resumo
                lancamentos_para_resumo = [
                    l for l in st.session_state.get("lancamentos", [])
                    if l.get('user_email') == usuario_selecionado_email
                ]
                st.info(f"Exibindo resumo de {usuario_selecionado_nome}.")
            else:
                st.warning(f"Usuário {usuario_selecionado_nome} não encontrado para o resumo.")
                lancamentos_para_resumo = []  # Lista vazia se o usuário não for encontrado


    else:  # Código existente para usuários não administradores
        usuario_email = st.session_state.get('usuario_atual_email')
        lancamentos_para_resumo = [
            l for l in st.session_state.get("lancamentos", [])
            if l.get('user_email') == usuario_email
        ]
        st.info(f"Exibindo seus lançamentos, {st.session_state.get('usuario_atual_nome', 'usuário')}.")

    # --- Aplicar Filtro por Data ao Resumo ---
    data_inicio_filtro = st.session_state.get("data_inicio_filtro")
    data_fim_filtro = st.session_state.get("data_fim_filtro")

    lancamentos_para_resumo_filtrados = lancamentos_para_resumo # Começa com a lista já filtrada por usuário

    if data_inicio_filtro and data_fim_filtro:
        data_inicio_str = data_inicio_filtro.strftime("%Y-%m-%d")
        data_fim_str = data_fim_filtro.strftime("%Y-%m-%d")
        lancamentos_para_resumo_filtrados = [
            l for l in lancamentos_para_resumo
            if l.get('Data') and data_inicio_str <= l.get('Data') <= data_fim_str
        ]
    elif data_inicio_filtro:
        data_inicio_str = data_inicio_filtro.strftime("%Y-%m-%d")
        lancamentos_para_resumo_filtrados = [
            l for l in lancamentos_para_resumo
            if l.get('Data') and l.get('Data') >= data_inicio_str
        ]
    elif data_fim_filtro:
        data_fim_str = data_fim_filtro.strftime("%Y-%m-%d")
        lancamentos_para_resumo_filtrados = [
            l for l in lancamentos_para_resumo
            if l.get('Data') and l.get('Data') <= data_fim_str
        ]

    # Agora, o resumo será calculado usando a lista filtrada por data
    lancamentos_para_resumo = lancamentos_para_resumo_filtrados
    # --- Fim do Filtro por Data ao Resumo ---


    # Inicializa os totais antes do loop
    total_receitas = 0
    total_despesas = 0

    # Agora itera sobre a lista `lancamentos_para_resumo` (que agora inclui filtro por data)
    for lancamento in lancamentos_para_resumo:
        # AS PRÓXIMAS DUAS CONDIÇÕES DEVEM ESTAR INDENTADAS ASSIM:
        if lancamento.get("Tipo de Lançamento") == "Receita":
            total_receitas += lancamento.get("Valor", 0)
        elif lancamento.get("Tipo de Lançamento") == "Despesa":
            total_despesas += lancamento.get("Valor", 0)

    # O CÓDIGO CONTINUA AQUI, FORA DO LOOP FOR, MAS DENTRO DA FUNÇÃO
    total_geral = total_receitas - total_despesas

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div style="background-color:#ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05); text-align: center;">
                <div style="font-size: 22px; color: green;">🟢</div>
                <div style="font-size: 16px; color: #666;">Receitas</div>
                <div style="font-size: 20px; color: green;"><strong>R$ {total_receitas:.2f}</strong></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background-color:#ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05); text-align: center;">
                <div style="font-size: 22px; color: red;">🔴</div>
                <div style="font-size: 16px; color: #666;">Despesas</div>
                <div style="font-size: 20px; color: red;"><strong>R$ {total_despesas:.2f}</strong></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        cor_saldo = "green" if total_geral >= 0 else "red"
        icone_saldo = "📈" if total_geral >= 0 else "📉"
        st.markdown(
            f"""
            <div style="background-color:#ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.05); text-align: center;">
                <div style="font-size: 22px; color: {cor_saldo};">{icone_saldo}</div>
                <div style="font-size: 16px; color: #666;">Saldo</div>
                <div style="font-size: 20px; color: {cor_saldo};"><strong>R$ {total_geral:.2f}</strong></div>
            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown("---")


# Função para exportar lançamentos para Excel (mantida a original)
def exportar_lancamentos_para_excel(lancamentos_list):
    lancamentos_para_df = []
    for lancamento in lancamentos_list:
        lancamento_copy = lancamento.copy()
        if 'user_email' in lancamento_copy:  # Mantendo a remoção do user_email para o Excel conforme original
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
        pdf.add_font('Arial_Unicode', '',
                     'Arial_Unicode.ttf')  # Substitua 'Arial_Unicode.ttf' pelo caminho ou nome do seu arquivo .ttf
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_table = 'Arial_Unicode'
    except Exception as e:
        # st.warning(f"Erro ao carregar fonte personalizada para PDF: {e}. Usando fonte padrão.") # Mantendo o aviso na console
        pdf.set_font("Arial", '', 12)
        font_for_table = 'Arial'

    pdf.set_font("Arial", 'B', 12)  # Use negrito da fonte padrão para o título (conforme original)
    report_title = f"Relatório de Lançamentos - {usuario_nome}"
    pdf.cell(0, 10, report_title.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')
    pdf.ln(10)

    # Usa a fonte com suporte a acentos (se carregada) ou a padrão para os cabeçalhos e dados da tabela
    pdf.set_font(font_for_table, 'B', 10)  # Cabeçalhos em negrito
    col_widths = [20, 90, 40, 20, 25]
    headers = ["Data", "Descrição", "Categoria", "Tipo", "Valor"]

    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C', fill=False)
    pdf.ln()

    pdf.set_font(font_for_table, '', 10)  # Dados da tabela em fonte normal
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
        pdf.cell(col_widths[2], 10, categoria.encode('latin1', 'replace').decode('latin1') if categoria else "", 1, 0,
                 'C')
        pdf.cell(col_widths[3], 10, tipo.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        pdf.cell(col_widths[4], 10, valor_formatado.encode('latin1', 'replace').decode('latin1'), 1, 0, 'R')

        pdf.ln()

    # Adiciona assinaturas no final do PDF de lançamentos
    pdf.cell(0, 15, "", 0, 1)  # Adiciona 15mm de espaço vertical
    y_atual = pdf.get_y()
    pdf.line(10, y_atual, 200, y_atual)  # linha horizontal de margem a margem
    pdf.ln(5)

    signatario_nome = st.session_state.get('usuarios', [])[st.session_state.get('usuario_atual_index', 0)].get(
        "SignatarioNome", "")
    signatario_cargo = st.session_state.get('usuarios', [])[st.session_state.get('usuario_atual_index', 0)].get(
        "SignatarioCargo", "")

    if signatario_nome or signatario_cargo:
        pdf.set_font("Arial", '', 10) #(If I want to use bold font)pdf.set_font("Arial", 'B', 12)

        if signatario_nome:
            pdf.cell(0, 10, f"Assinado por: {signatario_nome}", 0, 1, 'C')

        if signatario_cargo:
            pdf.cell(0, 8, signatario_cargo, 0, 1, 'C')

    pdf_output = pdf.output(dest='S')
    return io.BytesIO(pdf_output.encode('latin1')) # No Github adicionar: .encode('latin1'))

#Criar gráfico de Donuts

def criar_grafico_donut(receitas_por_categoria):
    plt.figure(figsize=(7, 7), facecolor='none')

    labels = list(receitas_por_categoria.keys())
    values = list(receitas_por_categoria.values())

    cores_personalizadas = ['#003548', '#0077b6', '#00b4d8', '#90e0ef', '#caf0f8']

    # Cria o gráfico e captura os textos de label e autopct
    wedges, texts, autotexts = plt.pie(
        values,
        labels=labels,
        autopct='%1.1f%%',
        pctdistance=0.7,
        wedgeprops=dict(width=0.5),
        colors=cores_personalizadas
    )

       # Customiza o texto das labels (categorias como “Dízimos”)
    for text in texts:
        text.set_color('black')       # Cor do texto da categoria
        text.set_fontsize(14)         # Tamanho da fonte da categoria
        text.set_weight('bold')       # ← corrigido aqui

    # Customiza o texto das porcentagens dentro do gráfico
    for autotext in autotexts:
        autotext.set_color('white')   # Cor do texto percentual
        autotext.set_fontsize(14)     # Tamanho da fonte percentual
        autotext.set_weight('bold')   # ← corrigido aqui

    plt.title('Distribuição de Receitas', fontsize=16, fontweight='bold', color='#003548')


    temp_filename = f"/tmp/donut_{uuid.uuid4().hex}.png"
    plt.savefig(temp_filename, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()

    return temp_filename

# --- FUNÇÃO para gerar a Demonstração de Resultados em PDF ---
def gerar_demonstracao_resultados_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos. Se não encontrar, usa Arial padrão.
    # Certifique-se de ter um arquivo .ttf (como Arial.ttf) no mesmo diretório do seu script.
    try:
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')  # Substitua 'Arial_Unicode.ttf'
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_text = 'Arial_Unicode'
    except Exception as e:
        # st.warning(f"Erro ao carregar fonte personalizada para PDF: {e}. Usando fonte padrão (pode não suportar acentos).") # O warning aparece no log, não no PDF
        pdf.set_font("Arial", '', 12)
        font_for_text = 'Arial'

    pdf.set_font(font_for_text, 'B', 14)  # Título principal com fonte negrito
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
    pdf.set_font(font_for_text, 'B', 12)  # Título da seção em negrito
    pdf.cell(0, 10, "Receitas".encode('latin1', 'replace').decode('latin1'), 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10)  # Conteúdo da seção em fonte normal
    # Ordenar categorias de receita alfabeticamente para consistência
    for categoria in sorted(receitas_por_categoria.keys()):
        valor = receitas_por_categoria[categoria]
        # Garante alinhamento com duas células: categoria à esquerda, valor à direita
        pdf.cell(100, 7, f"- {categoria}".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10)  # Total em negrito
    pdf.set_text_color(0, 0, 255)	
    pdf.cell(100, 7, "Total Receitas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_receitas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')
    pdf.ln(10)  # Espaço após a seção de Receitas
	
    # --- Adicionar Despesas ao PDF ---
    pdf.set_font(font_for_text, 'B', 12)  # Título da seção em negrito
    pdf.set_text_color(0, 0, 0)	
    pdf.cell(0, 10, "Despesas".encode('latin1', 'replace').decode('latin1'), 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10)  # Conteúdo da seção em fonte normal
    # Ordenar categorias de despesa alfabeticamente

    # Classificação das Despesas Administrativas
    total_despesas = sum(despesas_por_categoria.values())	
    pdf.cell(100, 7, "Despesas Administrativas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_despesas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10)  # Total em negrito
    pdf.set_text_color(255, 0, 0)	
    pdf.cell(100, 7, "Total Despesas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_despesas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')
    pdf.ln(10)  # Espaço após a seção de Despesas

    # --- Adicionar Resultado Líquido ---
    resultado_liquido = total_receitas - total_despesas
    pdf.set_font(font_for_text, 'B', 12)  # Resultado em negrito

    # Cor do resultado líquido: Azul para positivo, Vermelho para negativo
    if resultado_liquido >= 0:
        pdf.set_text_color(0, 0, 255)  # Azul para lucro
    else:
        pdf.set_text_color(255, 0, 0)  # Vermelho para prejuízo

    pdf.cell(100, 10, "Resultado Líquido".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 10, f"R$ {resultado_liquido:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1,
             'R')

    # Resetar cor do texto para preto para qualquer texto futuro (se houver)
    pdf.set_text_color(0, 0, 0)

    y_atual = pdf.get_y()
    pdf.line(10, y_atual, 200, y_atual)  # linha horizontal de margem a margem
    pdf.ln(5)

    # --- Gráfico de Donut de Receitas ---
    if receitas_por_categoria:
    	donut_path = criar_grafico_donut(receitas_por_categoria)
    	pdf.image(donut_path, x=55, y=pdf.get_y(), w=100)
    	pdf.ln(110)
    y_atual = pdf.get_y()
    pdf.line(10, y_atual, 200, y_atual)  # linha horizontal de margem a margem
    pdf.ln(5)

    # --- Comentário Analítico ---
    comentario = ""

    if total_receitas == 0 and total_despesas == 0:
        comentario = "Análise do Período:\n1) Não foram encontrados lançamentos de receitas ou despesas registrados para o período selecionado.\n2) Para que seja possível gerar qualquer análise financeira relevante, é fundamental inserir suas movimentações de entrada e saída.\n3) Por favor, realize o registro de suas transações financeiras para visualizar os resultados e ter insights sobre sua situação."
    elif total_receitas > 0 and total_despesas == 0:
        comentario = "Análise do Período:\n1) Excelente desempenho financeiro neste período, pois foram registradas apenas receitas significativas, sem nenhuma despesa associada.\n2) Esta situação indica um fluxo de caixa extremamente positivo, demonstrando uma entrada líquida total de recursos.\n3) Continue monitorando de perto seus próximos períodos para manter este controle exemplar sobre as despesas e maximizar seus ganhos."
    elif total_receitas == 0 and total_despesas > 0:
        comentario = "Análise do Período:\n1) Cenário preocupante detectado, com o registro exclusivo de despesas durante este período e ausência total de receitas.\n2) Esta configuração resulta diretamente em um fluxo de caixa negativo acentuado, impactando sua saúde financeira.\n3) É de suma importância identificar a origem e a necessidade dessas despesas e, paralelamente, desenvolver estratégias eficazes para gerar receitas e reverter este quadro."
    else:
        proporcao_despesa = (total_despesas / total_receitas) if total_receitas else 0
        if proporcao_despesa < 0.5:
            comentario = f"Análise do Período:\n1) Muito bom controle de custos neste período, com suas despesas representando apenas {proporcao_despesa:.1%} das receitas totais.\n2) Esta proporção demonstra uma gestão financeira eficiente, resultando em uma excelente margem operacional e um saldo positivo robusto.\n3) Este superávit pode ser estrategicamente utilizado para investimentos, formação de reservas de segurança ou reinvestimento no crescimento."
        elif proporcao_despesa <= 1.0:
            comentario = f"Análise do Período:\n1) Suas despesas representam {proporcao_despesa:.1%} das receitas neste período, indicando que uma parte considerável das suas entradas está sendo consumida pelos custos operacionais ou pessoais.\n2) Embora haja um saldo positivo ou equilíbrio, esta proporção requer atenção constante para evitar aperto financeiro em momentos de menor receita.\n3) Recomenda-se realizar uma análise detalhada de cada item de despesa para identificar possíveis otimizações e buscar aumentar a margem de lucro ou economia."
        else:
            comentario = f"Análise do Período:\n1) Situação de prejuízo registrada, com as despesas ({total_despesas:.2f}) superando significativamente as receitas ({total_receitas:.2f}), representando {proporcao_despesa-1:.1%} a mais do que o arrecadado.\n2) Este desequilíbrio gera um fluxo de caixa negativo intenso, comprometendo a sustentabilidade financeira no longo prazo.\n3) É absolutamente crucial e urgente revisar cada gasto detalhadamente, identificar cortes necessários e implementar medidas imediatas para aumentar as receitas e reverter este cenário deficitário o mais rápido possível."

    # Título do comentário
    pdf.set_font(font_for_text, 'B', 11)
    pdf.cell(0, 8, "Comentários:".encode('latin1', 'replace').decode('latin1'), ln=1, align='C')

    # Corpo do comentário
    pdf.set_font(font_for_text, 'I', 10)
    pdf.multi_cell(0, 8, comentario.encode('latin1', 'replace').decode('latin1'))
    pdf.ln(5)


    # Assinaturas da DRE
    y_atual = pdf.get_y()
    pdf.line(10, y_atual, 200, y_atual)  # linha horizontal de margem a margem
    pdf.ln(5)

    signatario_nome = st.session_state.get('usuarios', [])[st.session_state.get('usuario_atual_index', 0)].get(
        "SignatarioNome", "")
    signatario_cargo = st.session_state.get('usuarios', [])[st.session_state.get('usuario_atual_index', 0)].get(
        "SignatarioCargo", "")

    if signatario_nome or signatario_cargo:
        pdf.set_font("Arial", '', 10)
        if signatario_nome:
            pdf.cell(0, 10, f"Assinado por: {signatario_nome}", 0, 1, 'C')

        if signatario_cargo:
            pdf.cell(0, 8, signatario_cargo, 0, 1, 'C')

    # Finaliza o PDF e retorna como BytesIO
    pdf_output = pdf.output(dest='S')
    return io.BytesIO(pdf_output.encode('latin1')) # No Github adicionar: .encode('latin1'))


def exibir_lancamentos():
    st.subheader("Lançamentos")

    # Define a variável antes dos blocos if/else e inicializa como lista vazia
    lancamentos_para_exibir = []
    usuario_email = st.session_state.get('usuario_atual_email')

    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        st.info("Visão do Administrador.")

        # --- ADICIONAR SELECTBOX PARA ESCOLHER O USUÁRIO ---
        # Crie uma lista de opções para o selectbox, incluindo a opção "Todos os Usuários"
        opcoes_usuarios = ["Todos os Usuários"] + [u.get('Nome', 'Usuário Sem Nome') for u in
                                                   st.session_state.get('usuarios', [])]

        # Adicione o selectbox
        usuario_selecionado_nome = st.selectbox(
            "Selecionar Lançamentos do Usuário:",
            opcoes_usuarios,
            key="selectbox_usuario_lancamentos"
        )
        # --- FIM DO SELECTBOX ---

        if usuario_selecionado_nome == "Todos os Usuários":
            lancamentos_para_exibir = st.session_state.get("lancamentos", [])
            st.info("Exibindo todos os lançamentos.")
            filename_suffix = "admin_todos"
            usuario_para_pdf_title = "Todos os Lançamentos"
        else:
            # Encontre o e-mail do usuário selecionado pelo nome
            usuario_selecionado_email = None
            for u in st.session_state.get('usuarios', []):
                if u.get('Nome', 'Usuário Sem Nome') == usuario_selecionado_nome:
                    usuario_selecionado_email = u.get('Email')
                    break

            if usuario_selecionado_email:
                # Filtra lançamentos pelo e-mail do usuário selecionado
                lancamentos_para_exibir = [
                    l for l in st.session_state.get("lancamentos", [])
                    if l.get('user_email') == usuario_selecionado_email
                ]
                st.info(f"Exibindo lançamentos de {usuario_selecionado_nome}.")
                filename_suffix = usuario_selecionado_nome.replace(" ", "_").lower()
                usuario_para_pdf_title = usuario_selecionado_nome
            else:
                st.warning(f"Usuário {usuario_selecionado_nome} não encontrado.")
                lancamentos_para_exibir = []  # Lista vazia se o usuário não for encontrado


    else:  # Código existente para usuários não administradores
        # Atribui diretamente à variável lancamentos_para_exibir no bloco else
        lancamentos_para_exibir = [
            l for l in st.session_state.get("lancamentos", [])
            if l.get('user_email') == usuario_email
        ]
        st.info(f"Exibindo seus lançamentos, {st.session_state.get('usuario_atual_nome', 'usuário')}.")
        filename_suffix = st.session_state.get('usuario_atual_nome', 'usuario').replace(" ", "_").lower()
        usuario_para_pdf_title = st.session_state.get('usuario_atual_nome', 'Usuário')

# --- Adicionar Filtro por Data ---
    st.subheader("Filtrar Lançamentos por Data")
    col_data_inicio, col_data_fim = st.columns(2)

    with col_data_inicio:
        data_inicio_filtro = st.date_input("Data de Início", value=None, key="data_inicio_filtro")

    with col_data_fim:
        data_fim_filtro = st.date_input("Data de Fim", value=None, key="data_fim_filtro")

    lancamentos_filtrados_por_data = lancamentos_para_exibir # Inicializa com a lista completa ou filtrada por usuário

    if data_inicio_filtro and data_fim_filtro:
        # Converte as datas de filtro para o formato 'YYYY-MM-DD' para comparação
        data_inicio_str = data_inicio_filtro.strftime("%Y-%m-%d")
        data_fim_str = data_fim_filtro.strftime("%Y-%m-%d")

        lancamentos_filtrados_por_data = [
            lancamento for lancamento in lancamentos_para_exibir
            if lancamento.get('Data') and data_inicio_str <= lancamento.get('Data') <= data_fim_str
        ]
        # Altera o formato de exibição na mensagem para DD/MM/YYYY
        st.info(f"Exibindo lançamentos de {data_inicio_filtro.strftime('%d/%m/%Y')} a {data_fim_filtro.strftime('%d/%m/%Y')}.")
    elif data_inicio_filtro:
        data_inicio_str = data_inicio_filtro.strftime("%Y-%m-%d")
        lancamentos_filtrados_por_data = [
            lancamento for lancamento in lancamentos_para_exibir
            if lancamento.get('Data') and lancamento.get('Data') >= data_inicio_str
        ]
        # Altera o formato de exibição na mensagem para DD/MM/YYYY
        st.info(f"Exibindo lançamentos a partir de {data_inicio_filtro.strftime('%d/%m/%Y')}.")
    elif data_fim_filtro:
        data_fim_str = data_fim_filtro.strftime("%Y-%m-%d")
        lancamentos_filtrados_por_data = [
            lancamento for lancamento in lancamentos_para_exibir
            if lancamento.get('Data') and lancamento.get('Data') <= data_fim_str
        ]
        # Altera o formato de exibição na mensagem para DD/MM/YYYY
        st.info(f"Exibindo lançamentos até {data_fim_filtro.strftime('%d/%m/%Y')}.")

    # Agora, a lista a ser exibida e exportada é 'lancamentos_filtrados_por_data'
    lancamentos_para_exibir = lancamentos_filtrados_por_data # Sobrescreve a lista original para usar a filtrada
    # --- Fim do Filtro por Data ---

    if not lancamentos_para_exibir:
        st.info("Nenhum lançamento encontrado para este usuário.")
        # Exibe os botões de exportação mesmo com lista vazia (arquivos estarão vazios ou com cabeçalho)
        col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1])
        with col_excel:
            excel_buffer = exportar_lancamentos_para_excel([])  # Passa lista vazia
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
        return  # Sai da função para não exibir a tabela vazia

    # Ordenar lançamentos por data (do mais recente para o mais antigo)
    try:
        # Usamos a lista que já foi filtrada/selecionada corretamente
        lancamentos_para_exibir.sort(key=lambda x: datetime.strptime(x.get('Data', '1900-01-01'), '%Y-%m-%d'),
                                     reverse=True)
    except ValueError:
        st.warning("Não foi possível ordenar os lançamentos por data devido a formato inválido.")

    # --- Botões de Exportação ---
    # Adicionamos uma terceira coluna para o novo botão da Demonstração de Resultados
    # AUMENTANDO A LARGURA DA COLUNA DE AÇÕES (último valor na lista)
    col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1])  # Mantendo 3 colunas para os botões de exportação

    with col_excel:
        excel_buffer = exportar_lancamentos_para_excel(lancamentos_para_exibir)
        if excel_buffer:  # Só exibe o botão se a geração do Excel for bem-sucedida
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
            label="📄 Exportar Lançamentos em PDF",  # Rótulo claro para a lista detalhada
            data=pdf_lista_buffer,
            file_name=f'lista_lancamentos_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
        )

    with col_pdf_dr:
        # Adicione o novo botão para a Demonstração de Resultados
        pdf_dr_buffer = gerar_demonstracao_resultados_pdf(lancamentos_para_exibir, usuario_para_pdf_title)
        st.download_button(
            label="📊 Exportar Relatório de Resultados em PDF",  # Rótulo para a Demonstração de Resultados
            data=pdf_dr_buffer,
            file_name=f'demonstracao_resultados_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
        )

    st.markdown("---")

    # AQUI ESTÁ A MODIFICAÇÃO: Aumentando a proporção da última coluna (Ações) para 4 ou 5
    # Você pode testar 4 ou 5. Vou usar 4 aqui, mas sinta-se à vontade para ajustar.
    col_header_data, col_header_descricao, col_header_tipo, col_header_categoria, col_header_valor, col_header_acoes = st.columns(
        [2, 3, 2, 2, 2, 4]  # Proporção da última coluna aumentada para 4
    )
    col_header_data.markdown("**Data**")
    col_header_descricao.markdown("**Descrição**")
    col_header_tipo.markdown("**Tipo**")
    col_header_categoria.markdown("**Categoria**")
    col_header_valor.markdown("**Valor**")
    col_header_acoes.markdown("**Ações: Editar/Excluir**")

    # Iteramos diretamente sobre a lista de lançamentos para exibir (que já está filtrada)
    for i, lancamento in enumerate(lancamentos_para_exibir):
        # Precisamos encontrar o índice original na lista completa para exclusão/edição
        # Isso é necessário porque removemos do índice na lista completa.
        # Se a lista de lançamentos for muito grande, isso pode ser ineficiente.
        # Uma alternativa seria armazenar o índice original no dicionário do lançamento.
        try:
            original_index = st.session_state.get("lancamentos", []).index(lancamento)
        except ValueError:
            # Se por algum motivo o lançamento não for encontrado na lista completa, pule
            continue

        # AQUI ESTÁ A MODIFICAÇÃO: Usando a mesma nova proporção para as colunas de dados
        col1, col2, col3, col4, col5, col6 = st.columns(
            [2, 3, 2, 2, 2, 4])  # Proporção da última coluna aumentada para 4
        try:
            data_formatada = datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            data_formatada = lancamento.get("Data", "Data Inválida")

        col1.write(data_formatada)
        col2.write(lancamento.get("Descrição", ""))
        col3.write(lancamento.get("Tipo de Lançamento", ""))
        col4.write(lancamento.get("Categorias", ""))
        col5.write(f"R$ {lancamento.get('Valor', 0.0):.2f}")

        with col6:
            is_owner = lancamento.get('user_email') == st.session_state.get('usuario_atual_email')
            is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'

            # Usamos o original_index para as chaves dos botões
            if (is_owner or is_admin) and not st.session_state.get('show_add_modal') and not st.session_state.get(
                    'show_edit_modal'):
                # Ajusta as colunas para os botões de ação - MANTENDO O DEFAULT DE [1, 1]
                # Como a coluna 6 principal ficou mais larga, as sub-colunas dentro dela
                # também ficarão mais largas automaticamente.
                col_editar, col_excluir = st.columns(2)  # Mantendo o default [1, 1]
                with col_editar:
                    if st.button("Editar", key=f"editar_{original_index}"):
                        st.session_state["editar_indice"] = original_index
                        st.session_state["editar_lancamento"] = st.session_state["lancamentos"][original_index].copy()
                        st.session_state['show_edit_modal'] = True
                        st.rerun()
                with col_excluir:
                    # Para excluir, removemos pelo original_index na lista completa
                    if st.button("Excluir", key=f"excluir_{original_index}"):
                        del st.session_state["lancamentos"][original_index]
                        salvar_lancamentos()
                        st.success("Lançamento excluído com sucesso!")
                        st.rerun()
            elif not (is_owner or is_admin):
                st.write("Sem permissão")


def pagina_dashboard():
    if not st.session_state.get('autenticado'):
        st.warning("Você precisa estar logado para acessar o dashboard.")
        return

    col_nav1, _ = st.columns(2)
    if col_nav1.button("⚙️ Configurações"):
        st.session_state['pagina_atual'] = 'configuracoes'
        st.rerun()

    st.title(f"Controle Financeiro - {st.session_state.get('usuario_atual_nome', 'Usuário')}")
    exibir_resumo_central()

    modal_ativo = st.session_state.get('show_add_modal') or st.session_state.get('show_edit_modal')

    if not modal_ativo:
        if st.button("➕ Adicionar Novo Lançamento"):
            st.session_state['show_add_modal'] = True
            st.rerun()
        exibir_lancamentos()  # Chama a função exibir_lancamentos corrigida

    elif st.session_state.get('show_add_modal'):
        render_add_lancamento_form()

    elif st.session_state.get('show_edit_modal'):
        render_edit_lancamento_form()


def pagina_configuracoes():
    if not st.session_state.get('autenticado'):
        st.warning("Você precisa estar logado para acessar as configurações.")
        return

    col_nav1, _ = st.columns(2)
    if col_nav1.button("📊 Voltar para os Lançamentos"):
        st.session_state['pagina_atual'] = 'dashboard'
        st.rerun()

    st.title("Configurações")

    usuario_logado_email = st.session_state.get('usuario_atual_email')
    usuario_logado_index = st.session_state.get('usuario_atual_index')

    # Verificação adicional para garantir que o índice do usuário logado é válido
    if usuario_logado_index is not None and 0 <= usuario_logado_index < len(st.session_state.get('usuarios', [])):
        usuario_logado = st.session_state['usuarios'][usuario_logado_index]

        st.subheader(f"Editar Meu Perfil ({usuario_logado.get('Tipo', 'Tipo Desconhecido')})")
        edit_nome_proprio = st.text_input("Nome", usuario_logado.get('Nome', ''), key="edit_meu_nome")
        st.text_input("E-mail", usuario_logado.get('Email', ''), disabled=True)
        nova_senha_propria = st.text_input("Nova Senha (deixe em branco para manter)", type="password", value="",
                                           key="edit_minha_nova_senha")
        confirmar_nova_senha_propria = st.text_input("Confirmar Nova Senha", type="password", value="",
                                                     key="edit_confirmar_minha_nova_senha")

        # CAMPOS DE ASSINATURA
        signatario_nome = st.text_input("Nome de quem assina os relatórios", usuario_logado.get('SignatarioNome', ''),
                                        key="signatario_nome")
        signatario_cargo = st.text_input("Cargo de quem assina os relatórios", usuario_logado.get('SignatarioCargo', ''),
                                         key="signatario_cargo")

        if st.button("Salvar Alterações no Perfil"):
            if nova_senha_propria == confirmar_nova_senha_propria:
                st.session_state['usuarios'][usuario_logado_index]['Nome'] = edit_nome_proprio
                if nova_senha_propria:
                    st.session_state['usuarios'][usuario_logado_index]['Senha'] = nova_senha_propria

                    # SALVA SIGNATÁRIO
                st.session_state['usuarios'][usuario_logado_index]['SignatarioNome'] = signatario_nome
                st.session_state['usuarios'][usuario_logado_index]['SignatarioCargo'] = signatario_cargo

                salvar_usuarios()
                st.success("Perfil atualizado com sucesso!")
                st.session_state['usuario_atual_nome'] = edit_nome_proprio
                st.rerun()
            else:
                st.error("As novas senhas não coincidem.")
    else:
        st.error("Erro ao carregar informações do seu usuário.")

    # --- Campo para adicionar e gerenciar categorias de Receitas (agora específicas por usuário) ---
    st.subheader("Gerenciar Categorias de Receitas")
    st.markdown("---")

    # Verificação adicional antes de tentar gerenciar categorias
    if usuario_logado_index is not None and 0 <= usuario_logado_index < len(st.session_state.get('usuarios', [])):
        # Garante que a chave 'categorias_receita' existe para o usuário logado (conforme original)
        if 'categorias_receita' not in st.session_state['usuarios'][usuario_logado_index]:
            st.session_state['usuarios'][usuario_logado_index]['categorias_receita'] = []

        usuario_categorias_atuais = st.session_state['usuarios'][usuario_logado_index]['categorias_receita']
        # Inclui as categorias padrão apenas para exibição e verificação de duplicidade
        todas_categorias_receita_disponiveis = CATEGORIAS_PADRAO_RECEITA + usuario_categorias_atuais

        nova_categoria_receita = st.text_input("Nome da Nova Categoria de Receita", key="nova_categoria_receita_input")
        if st.button("Adicionar Categoria de Receita"):
            if nova_categoria_receita:
                # Verifica se a categoria já existe (case-insensitive check) na lista combinada do usuário
                if nova_categoria_receita.lower() not in [c.lower() for c in todas_categorias_receita_disponiveis]:
                    # Adiciona a nova categoria à lista personalizada do usuário logado
                    st.session_state['usuarios'][usuario_logado_index]['categorias_receita'].append(
                        nova_categoria_receita)
                    salvar_usuarios()
                    # Atualiza a lista combinada de categorias na sessão para o usuário logado
                    st.session_state['todas_categorias_receita'] = list(dict.fromkeys(
                        CATEGORIAS_PADRAO_RECEITA + st.session_state['usuarios'][usuario_logado_index][
                            'categorias_receita']))

                    st.success(
                        f"Categoria '{nova_categoria_receita}' adicionada com sucesso às suas categorias de receita!")
                    st.rerun()  # Rerun para atualizar o selectbox imediatamente
                else:
                    st.warning(
                        f"A categoria '{nova_categoria_receita}' já existe nas suas categorias de receita ou nas padrão.")
            else:
                st.warning("Por favor, digite o nome da nova categoria de receita.")

        st.subheader("Suas Categorias de Receitas Personalizadas")
        # Exibe as categorias personalizadas com opção de exclusão
        if usuario_categorias_atuais:
            st.write("Clique no botão 'Excluir' ao lado de uma categoria personalizada para removê-la.")

            # Filtra lançamentos do usuário logado para verificar uso da categoria
            lancamentos_do_usuario = [
                l for l in st.session_state.get("lancamentos", [])
                if l.get('user_email') == usuario_logado_email and l.get('Tipo de Lançamento') == 'Receita'
            ]
            categorias_receita_em_uso = {l.get('Categorias') for l in lancamentos_do_usuario if l.get('Categorias')}

            # Itera sobre categorias personalizadas para exibir e permitir exclusão
            for i, categoria in enumerate(usuario_categorias_atuais):
                col_cat, col_del = st.columns([3, 1])
                col_cat.write(categoria)
                # Verifica se a categoria está em uso em algum lançamento de receita do usuário
                if categoria in categorias_receita_em_uso:
                    col_del.write("Em uso")
                else:
                    if col_del.button("Excluir", key=f"del_cat_receita_{i}"):
                        # Remove a categoria da lista personalizada do usuário
                        del st.session_state['usuarios'][usuario_logado_index]['categorias_receita'][i]
                        salvar_usuarios()
                        # Atualiza a lista combinada na sessão
                        st.session_state['todas_categorias_receita'] = list(dict.fromkeys(
                            CATEGORIAS_PADRAO_RECEITA + st.session_state['usuarios'][usuario_logado_index][
                                'categorias_receita']))
                        st.success(f"Categoria '{categoria}' excluída com sucesso!")
                        st.rerun()
        else:
            st.info("Você ainda não adicionou nenhuma categoria de receita personalizada.")

    else:
        st.error("Erro ao carregar informações de categorias para o seu usuário.")

    # --- Manter apenas a seção de Gerenciar Usuários para Admin ---
    # Removendo a seção de gerenciar categorias de Despesas que eu adicionei antes
    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        st.markdown("---")
        st.subheader("Gerenciar Usuários (Apenas Admin)")

        if st.session_state.get('editar_usuario_index') is not None:
            render_edit_usuario_form()
        else:
            with st.expander("Adicionar Novo Usuário", expanded=False):
                st.subheader("Adicionar Novo Usuário")
                with st.form(key="add_usuario_form"):
                    novo_nome = st.text_input("Nome", key="add_user_nome")
                    novo_email = st.text_input("E-mail", key="add_user_email")
                    nova_senha = st.text_input("Senha", type="password", key="add_user_senha")
                    novo_tipo = st.selectbox("Tipo", ["Cliente", "Administrador"], key="add_user_tipo")
                    submit_user_button = st.form_submit_button("Adicionar Usuário")

                    if submit_user_button:
                        if not novo_nome or not novo_email or not nova_senha or not novo_tipo:
                            st.warning("Por favor, preencha todos os campos para o novo usuário.")
                        elif any(u.get('Email') == novo_email for u in st.session_state.get('usuarios', [])):
                            st.warning(f"E-mail '{novo_email}' já cadastrado.")
                        else:
                            novo_usuario = {
                                "Nome": novo_nome,
                                "Email": novo_email,
                                "Senha": nova_senha,  # Em um app real, use hashing de senha!
                                "Tipo": novo_tipo,
                                "categorias_receita": [],
                                # Inicializa categorias personalizadas (mantido conforme original)
                                # Não adiciona categorias_despesa aqui, mantendo o original
                            }
                            st.session_state['usuarios'].append(novo_usuario)
                            salvar_usuarios()
                            st.success(f"Usuário '{novo_nome}' adicionado com sucesso!")
                            st.rerun()

            st.subheader("Lista de Usuários")
            if st.session_state.get('usuarios'):
                col_user_nome, col_user_email, col_user_tipo, col_user_acoes = st.columns([3, 4, 2, 3])
                col_user_nome.markdown("**Nome**")
                col_user_email.markdown("**E-mail**")
                col_user_tipo.markdown("**Tipo**")
                col_user_acoes.markdown("**Ações**")

                # Não liste o próprio usuário Admin para evitar que ele se exclua acidentalmente
                usuarios_para_listar = [u for u in st.session_state['usuarios'] if
                                        u.get('Email') != usuario_logado_email]

                for i, usuario in enumerate(usuarios_para_listar):
                    # Precisamos encontrar o índice ORIGINAL na lista completa para exclusão/edição
                    try:
                        original_user_index = st.session_state['usuarios'].index(usuario)
                    except ValueError:
                        continue  # Pula se não encontrar (não deveria acontecer)

                    col1, col2, col3, col4 = st.columns([3, 4, 2, 3])
                    col1.write(usuario.get('Nome', ''))
                    col2.write(usuario.get('Email', ''))
                    col3.write(usuario.get('Tipo', ''))

                    with col4:
                        col_edit_user, col_del_user = st.columns(2)
                        with col_edit_user:
                            if st.button("Editar", key=f"edit_user_{original_user_index}"):
                                st.session_state['editar_usuario_index'] = original_user_index
                                st.session_state['editar_usuario_data'] = st.session_state['usuarios'][
                                    original_user_index].copy()
                                st.rerun()
                        with col_del_user:
                            # Só permite excluir se não for o usuário logado
                            if usuario.get('Email') != usuario_logado_email:
                                if st.button("Excluir", key=f"del_user_{original_user_index}",
                                             help="Excluir este usuário"):
                                    # Confirmação simples (opcional)
                                    # if st.checkbox(f"Confirmar exclusão de {usuario.get('Nome', '')}", key=f"confirm_del_user_{original_user_index}"):
                                    excluir_usuario(original_user_index)
                            else:
                                st.write("Não pode excluir a si mesmo")

            else:
                st.info("Nenhum outro usuário cadastrado.")

    elif st.session_state.get('tipo_usuario_atual') == 'Cliente':
        st.markdown("---")
        st.subheader("Gerenciar Usuários")
        st.info("Esta seção está disponível apenas para administradores.")


def render_edit_usuario_form():
    if st.session_state.get('editar_usuario_index') is None:
        return

    index = st.session_state['editar_usuario_index']
    usuario_a_editar = st.session_state.get('usuarios', [])[index]

    # Verifica se o usuário logado é administrador e não está tentando editar a si mesmo através deste modal
    if st.session_state.get('tipo_usuario_atual') != 'Administrador' or usuario_a_editar.get(
            'Email') == st.session_state.get('usuario_atual_email'):
        st.error("Você não tem permissão para editar este usuário desta forma.")
        st.session_state['editar_usuario_index'] = None
        st.session_state['editar_usuario_data'] = None
        st.rerun()
        return

    with st.expander(f"Editar Usuário: {usuario_a_editar.get('Nome', '')}", expanded=True):
        st.subheader(f"Editar Usuário: {usuario_a_editar.get('Nome', '')}")
        with st.form(key=f"edit_usuario_form_{index}"):
            # Usamos a cópia em st.session_state['editar_usuario_data'] para preencher o formulário
            edit_nome = st.text_input("Nome", st.session_state['editar_usuario_data'].get('Nome', ''),
                                      key=f"edit_user_nome_{index}")
            st.text_input("E-mail", st.session_state['editar_usuario_data'].get('Email', ''), disabled=True,
                          key=f"edit_user_email_{index}")
            edit_senha = st.text_input("Nova Senha (deixe em branco para manter)", type="password", value="",
                                       key=f"edit_user_senha_{index}")
            edit_tipo = st.selectbox("Tipo", ["Cliente", "Administrador"], index=["Cliente", "Administrador"].index(
                st.session_state['editar_usuario_data'].get('Tipo', 'Cliente')), key=f"edit_user_tipo_{index}")

            submit_edit_user_button = st.form_submit_button("Salvar Edição do Usuário")

            if submit_edit_user_button:
                # Atualiza os dados na lista original
                st.session_state['usuarios'][index]['Nome'] = edit_nome
                if edit_senha:  # Atualiza a senha apenas se uma nova foi digitada
                    st.session_state['usuarios'][index]['Senha'] = edit_senha  # Lembre-se: em um app real, use hashing
                st.session_state['usuarios'][index]['Tipo'] = edit_tipo

                salvar_usuarios()
                st.success("Usuário atualizado com sucesso!")
                st.session_state['editar_usuario_index'] = None
                st.session_state['editar_usuario_data'] = None
                st.rerun()

        if st.button("Cancelar Edição", key=f"cancel_edit_user_form_{index}"):
            st.session_state['editar_usuario_index'] = None
            st.session_state['editar_usuario_data'] = None
            st.rerun()


# --- Navegação entre Páginas ---

if st.session_state.get('autenticado'):
    if st.session_state['pagina_atual'] == 'dashboard':
        pagina_dashboard()
    elif st.session_state['pagina_atual'] == 'configuracoes':
        pagina_configuracoes()
else:
    pagina_login()

# --- Logout ---
if st.session_state.get('autenticado'):
    if st.sidebar.button("Sair"):
        st.session_state['autenticado'] = False
        st.session_state['usuario_atual_email'] = None
        st.session_state['usuario_atual_nome'] = None
        st.session_state['tipo_usuario_atual'] = None
        st.session_state['usuario_atual_index'] = None
        st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy()  # Reseta categorias de receita
        # Não reseta categorias de despesa, pois não eram gerenciadas por usuário no original
        st.session_state['pagina_atual'] = 'dashboard'  # Redireciona para o login
        st.rerun()
