import streamlit as st
from datetime import datetime
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import io
import uuid
from fpdf import FPDF
from supabase import create_client, Client # --- ADAPTAÇÃO SUPABASE ---

# --- ADAPTAÇÃO SUPABASE ---
# Carregar credenciais do Supabase de .streamlit/secrets.toml
# Certifique-se que este arquivo existe e contém SUPABASE_URL e SUPABASE_KEY
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    st.success("Conectado ao Supabase!") # Mensagem de confirmação (opcional)
except Exception as e:
    st.error(f"Erro ao conectar ao Supabase: {e}")
    st.stop() # Para a execução se não conseguir conectar
# --- FIM ADAPTAÇÃO SUPABASE ---


# --- Estilo CSS para os botões de navegação ---
st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: #f0f2f6; /* Cor de fundo clara */
        color: #262730; /* Cor do texto escura */
        border-radius: 8px; /* Cantos arredondados */
        border: 1px solid #d4d7de; /* Borda
    sutil */
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

# --- REMOVENDO ARQUIVOS LOCAIS ---
# DATA_FILE = "lancamentos.json" # Removido
# USUARIOS_FILE = "usuarios.json" # Removido
# CATEGORIAS_FILE = "categorias.json" # Já removido no original

# --- Funções de Carregamento e Salvamento (AGORA USANDO SUPABASE) ---

# --- ADAPTAÇÃO SUPABASE: Funções de Usuários ---
def carregar_usuarios():
    # Tenta buscar todos os usuários da tabela 'usuarios'
    try:
        response = supabase.table("usuarios").select("*").execute()
        # A resposta do Supabase vem em response.data
        st.session_state['usuarios'] = response.data if response.data else []
        # Garante que cada usuário tem a lista de categorias (se a coluna jsonb for nula no DB, retorna None)
        for usuario in st.session_state['usuarios']:
            if 'categorias_receita' not in usuario or usuario['categorias_receita'] is None:
                usuario['categorias_receita'] = []

            if not usuario.get('email'):
                st.error(f"O usuário {usuario.get('nome', 'Sem Nome')} não possui e-mail. Corrija no Supabase para evitar erros.")
                st.stop()

    except Exception as e:
        st.error(f"Erro ao carregar usuários do Supabase: {e}")
        st.session_state['usuarios'] = [] # Define como lista vazia em caso de erro

    # --- INCLUA O CÓDIGO DO ADMINISTRADOR AQUI ---
    # Adapte esta parte para verificar se o admin existe NO SUPABASE antes de tentar inserir
    novo_admin = {
        "nome": "Junior Fernandes",
        "email": "valmirfernandescontabilidade@gmail.com",
        "senha": "114316", # Cuidado: Armazenar senhas em texto plano não é seguro. Considere usar hashing de senha.
        "tipo": "Administrador",
        "categorias_receita": [], # Inicializa com lista vazia
        "signatarioNome": "", # Pode preencher se necessário
        "signatarioCargo": "" # Pode preencher se necessário
    }

    # Verifica se o usuário já existe no Supabase antes de adicionar para evitar duplicação
    admin_existente = any(u.get('email') == novo_admin['email'] for u in st.session_state.get('usuarios', []))

    if not admin_existente:
        try:
            # Insere o novo admin no Supabase
            response = supabase.table("usuarios").insert(novo_admin).execute()
            if response.error:
                 st.error(f"Erro ao adicionar usuário administrador inicial: {response.error.message}")
            else:
                st.success("Usuário administrador inicial adicionado com sucesso!")
                # Após adicionar, recarregue a lista de usuários para incluir o novo admin
                carregar_usuarios()
        except Exception as e:
             st.error(f"Erro na operação de inserção do administrador: {e}")

    # --- FIM DA INCLUSÃO DO ADMIN ---


def salvar_usuario_supabase(usuario_data):
    if not usuario_data.get('email'):
        st.error("O campo de e-mail é obrigatório para salvar o usuário.")
        return False
    # Esta função é genérica para inserir ou atualizar lançamentos.
    # Se usuario_data tiver 'id', tenta atualizar. Caso contrário, insere.
    try:
        # Determine if it's an update or insert based on the presence AND validity of 'id'
        user_id = usuario_data.get('id') # Tenta obter o ID, retorna None se a chave não existir
        if user_id is not None: # Se 'id' existe E não é None, assumimos que é uma ATUALIZAÇÃO
            # É uma atualização
            # Cria uma cópia dos dados para remover o 'id' com segurança antes de enviar para o update
            update_data = usuario_data.copy()
            del update_data['id'] # Remove a chave 'id' do payload de dados para o update

            # Executa a operação de atualização no Supabase, filtrando pelo ID
            response = supabase.table("usuarios").update(update_data).eq("id", user_id).execute()
        else: # Se 'id' é None (chave não existe ou valor é None), assumimos que é uma INSERÇÃO
            # É uma inserção
            # Cria uma cópia dos dados para garantir que a chave 'id' NÃO esteja no payload de inserção
            insert_data = usuario_data.copy()
            if 'id' in insert_data:
                 # Remove a chave 'id' se ela existir (especialmente se for {"id": None, ...})
                 del insert_data['id']

            # Executa a operação de inserção no Supabase
            response = supabase.table("usuarios").insert(insert_data).execute()

        # Verifica se a resposta possui o atributo 'error' E se há um erro reportado (mantido do fix anterior)
        if hasattr(response, 'error') and response.error:
            st.error(f"Erro ao salvar usuário no Supabase: {response.error.message}")
            return False # Indica falha
        else:
            # Se não há atributo 'error' ou o erro é None, considera sucesso (ou um tipo diferente de resposta)
            st.success("Usuário salvo com sucesso!")
            # Após salvar, recarregue a lista de usuários para refletir a mudança
            carregar_usuarios() # Recarrega todos os usuários
            return True # Indica sucesso
    except Exception as e:
        st.error(f"Erro na operação de salvar usuário: {e}")
        return False # Indica falha


def excluir_usuario_db(user_id):
    # Esta função exclui um usuário baseado no ID do Supabase
    try:
        response = supabase.table("usuarios").delete().eq("id", user_id).execute()
        if hasattr(response, "erro") and response.error:
            st.error(f"Erro ao excluir usuário do Supabase: {response.error.message}")
            return False # Indica falha
        else:
            st.success("Usuário excluído com sucesso!")
            # Após excluir, recarregue a lista de usuários
            carregar_usuarios()
            return True # Indica sucesso
    except Exception as e:
        st.error(f"Erro na operação de exclusão do usuário: {e}")
        return False # Indica falha

# --- ADAPTAÇÃO SUPABASE: Funções de Lançamentos ---

def carregar_lancamentos():
    # Busca todos os lançamentos. A filtragem por usuário e data será feita localmente ou na query mais tarde.
    try:
        response = supabase.table("lancamentos").select("*").execute()
        st.session_state["lancamentos"] = response.data if response.data else []
        # Adiciona um ID temporário se não existir (para compatibilidade inicial, mas o Supabase já deve fornecer)
        # Certifique-se que sua tabela 'lancamentos' no Supabase tem um campo 'id' UUID gerado por padrão
        for lancamento in st.session_state["lancamentos"]:
            if 'id' not in lancamento or lancamento['id'] is None:
                 # Isso não deve acontecer se o Supabase estiver configurado corretamente
                 lancamento['id'] = str(uuid.uuid4()) # Cria um ID temporário (NÃO IDEAL)
                 st.warning("Alguns lançamentos não têm ID do Supabase. Considere corrigir a estrutura da tabela.")

    except Exception as e:
        st.error(f"Erro ao carregar lançamentos do Supabase: {e}")
        st.session_state["lancamentos"] = [] # Define como lista vazia em caso de erro


def salvar_lancamento_supabase(lancamento_data):
    # Esta função é genérica para inserir ou atualizar lançamentos.
    # Se lancamento_data tiver 'id', tenta atualizar. Caso contrário, insere.
    try: # <-- Início do bloco try
        if 'id' in lancamento_data and lancamento_data['id'] is not None:
            # É uma atualização
            lancamento_id = lancamento_data.pop('id') # Remove o 'id' dos dados para a atualização
            response = supabase.table("lancamentos").update(lancamento_data).eq("id", lancamento_id).execute()
        else:
            # É uma inserção
            # Remova o ID temporário se ele existir e não for do Supabase (cuidado aqui!)
            # if 'id' in lancamento_data:
            #     del lancamento_data['id']
            response = supabase.table("lancamentos").insert(lancamento_data).execute()

        # Verifica se a resposta possui o atributo 'error' E se há um erro reportado
        if hasattr(response, 'error') and response.error:
            st.error(f"Erro ao salvar lançamento no Supabase: {response.error.message}")
            return False # Indica falha
        else:
            # Se não há atributo 'error' ou o erro é None, considera sucesso (ou um tipo diferente de resposta)
            st.success("Lançamento salvo com sucesso!")
            # Após salvar, recarregue a lista de lançamentos para refletir a mudança
            carregar_lancamentos() # Recarrega todos os lançamentos
            return True # Indica sucesso
    except Exception as e: # <-- O bloco except que precisa estar aqui, alinhado com o try
        st.error(f"Erro na operação de salvar lançamento: {e}")
        return False # Indica falha


def excluir_lancamento_db(lancamento_id):
    # Esta função exclui um lançamento baseado no ID do Supabase
    try:
        response = supabase.table("lancamentos").delete().eq("id", lancamento_id).execute()
        if hasattr (response, "erro") and response.error:
            st.error(f"Erro ao excluir lançamento do Supabase: {response.error.message}")
            return False # Indica falha
        else:
            st.success("Lançamento excluído com sucesso!")
            # Após excluir, recarregue a lista de lançamentos
            carregar_lancamentos() # Recarrega todos os lançamentos
            return True # Indica sucesso
    except Exception as e:
        st.error(f"Erro na operação de exclusão do lançamento: {e}")
        return False # Indica falha

# --- FIM ADAPTAÇÃO SUPABASE: Funções de Lançamentos e Usuários ---


# --- Inicialização de Estado ---
# A ordem de carregamento pode importar se usuários e lançamentos têm dependência
if 'usuarios' not in st.session_state:
    carregar_usuarios() # Carrega usuários do Supabase ao iniciar
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
    st.session_state['usuario_atual_index'] = None # Este índice pode ser menos relevante agora com IDs do DB

# Variáveis de estado para controlar a exibição dos "popups"
if 'show_add_modal' not in st.session_state:
    st.session_state['show_add_modal'] = False
if 'show_edit_modal' not in st.session_state:
    st.session_state['show_edit_modal'] = False
if 'editar_indice' not in st.session_state:
    st.session_state['editar_indice'] = None # Usaremos o ID do Supabase agora, não o índice da lista local
if 'editar_lancamento' not in st.session_state:
    st.session_state['editar_lancamento'] = None
if 'editar_usuario_index' not in st.session_state:
    st.session_state['editar_usuario_index'] = None # Usaremos o ID do Supabase agora para usuários
if 'editar_usuario_data' not in st.session_state:
    st.session_state['editar_usuario_data'] = None


# Carrega os lançamentos ao iniciar o app (DO SUPABASE)
carregar_lancamentos()
if "lancamentos" not in st.session_state:
    st.session_state["lancamentos"] = [] # Já tratado em carregar_lancamentos

# Define as categorias padrão de receita (conforme seu código original)
CATEGORIAS_PADRAO_RECEITA = ["Serviços", "Vendas"]
# O código original não tinha categorias padrão de despesa ou gestão delas por usuário.
# A Demonstração de Resultados agrupará despesas pelo campo 'Categorias' existente,
# mas sem gestão específica de categorias de despesa no UI.
# Inicializa a lista de categorias disponíveis para o usuário logado (será atualizada no login)
if 'todas_categorias_receita' not in st.session_state:
    st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy()  # Começa com as padrão


# Mantendo a estrutura original que não tinha 'todas_categorias_despesa' no estado

# --- ADAPTAÇÃO SUPABASE: Excluir Usuário ---
def excluir_usuario(index_local): # Mantive o nome da função, mas a lógica interna mudou
    # Antes de excluir o usuário, podemos verificar se há lançamentos associados
    # e decidir o que fazer (excluir lançamentos, reatribuir, etc.).
    # Por simplicidade, vamos apenas excluir o usuário do DB.

    # Encontre o ID do usuário na lista atual do session_state (carregada do DB)
    if 0 <= index_local < len(st.session_state.get('usuarios', [])):
        user_to_delete = st.session_state['usuarios'][index_local]
        user_id = user_to_delete.get('id') # Pega o ID do Supabase

        if user_id:
            excluir_usuario_db(user_id) # Chama a função que exclui no Supabase
            # A função excluir_usuario_db já recarrega a lista de usuários no session_state
        else:
             st.error("ID do usuário não encontrado para exclusão.")
    else:
         st.error("Índice de usuário inválido para exclusão.")

    st.rerun() # Rerun após a operação de exclusão

# --- FIM ADAPTAÇÃO SUPABASE: Excluir Usuário ---


def pagina_login():
    # Escolhe o logo com base no tema carregado
    theme_base = st.get_option("theme.base")
    logo_path = "logo_dark.png" if theme_base == "dark" else "logo_light.png" # Certifique-se que estes arquivos existem
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
            .button-hover-effect {
                display: inline-block;
                width: 100%;
                padding: 0.5em 1em;
                background-color: #003548;
                color: #ffffff !important;
                text-align: center;
                text-decoration: none !important;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                border: none;
                transition: background-color 0.3s ease;
            }
    
            .button-hover-effect:hover {
                background-color: #D6110F;
                color: #ffffff !important;
                text-decoration: none !important;
            }
            </style>
    
            <a href='https://juniorfernandes.com/produtos' target='_blank' class='button-hover-effect'>
                Tenha acesso à todos os produtos
            </a>
            """,
            unsafe_allow_html=True
        )




    with col1:
        login_button = st.button("Acessar meu financeiro", key="botao_entrar_login")

    if login_button:
        # --- ADAPTAÇÃO SUPABASE: Autenticação ---
        # Busca o usuário pelo email e verifica a senha localmente (AINDA INSEGURO PELA SENHA EM TEXTO PLANO)
        # Uma abordagem melhor seria usar o módulo de autenticação do Supabase
        usuario_encontrado = None
        for i, usuario in enumerate(st.session_state.get('usuarios', [])):
            if usuario.get('email') == email and usuario.get('senha') == senha:
                usuario_encontrado = usuario
                st.session_state['usuario_atual_index'] = i # Mantém o índice local por compatibilidade, mas o ID do DB é melhor
                break

        if usuario_encontrado:
            st.session_state['autenticado'] = True
            st.session_state['usuario_atual_email'] = usuario_encontrado.get('email')
            st.session_state['usuario_atual_nome'] = usuario_encontrado.get('nome')
            st.session_state['tipo_usuario_atual'] = usuario_encontrado.get('tipo')

            # Carrega as categorias de receita personalizadas do usuário logado
            usuario_categorias_receita = usuario_encontrado.get('categorias_receita', [])
            todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + usuario_categorias_receita))
            st.session_state['todas_categorias_receita'] = todas_unicas_receita

            st.success(f"Login realizado com sucesso, {st.session_state['usuario_atual_nome']}!")
            st.rerun()
        else:
            st.error("E-mail ou senha incorretos.")
        # --- FIM ADAPTAÇÃO SUPABASE: Autenticação ---


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
            elif tipo == "Despesa":
                # Categorias de despesas fixas
                categorias_despesas = ["Despesas Administrativas", "Imobilizado"]
                categorias = categoria_placeholder.selectbox(
                    "Categoria de Despesas",
                    categorias_despesas,
                    key="add_lanc_categoria_despesa_form"
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
                            # SUPABASE: O ID será gerado pelo Supabase na inserção, não inclua aqui.
                            "Data": data_obj,
                            "Descrição": descricao,
                            "Categorias": categorias,  # Salva a categoria (será vazia se não for Receita no original)
                            "Tipo de Lançamento": tipo,
                            "Valor": valor,
                            "user_email": st.session_state['usuario_atual_email']
                        }
                        # --- ADAPTAÇÃO SUPABASE: Salvar Lançamento ---
                        if salvar_lancamento_supabase(novo_lancamento): # Chama a nova função que salva no Supabase
                            st.session_state['show_add_modal'] = False
                            st.rerun() # Rerun após salvar no Supabase
                        # --- FIM ADAPTAÇÃO SUPABASE ---
                    except ValueError:
                        st.error("Formato de data inválido. Use DD/MM/AAAA.")

        # Botão cancelar FORA do formulário
        if st.button("Cancelar", key="cancel_add_form_button"):
            st.session_state['show_add_modal'] = False
            st.rerun()


def render_edit_lancamento_form():
    # --- ADAPTAÇÃO SUPABASE: Usando ID para editar ---
    if not st.session_state.get('autenticado') or st.session_state.get('editar_lancamento') is None:
        return

    # O lancamento_a_editar agora é o dicionário completo do lançamento, incluindo o 'id' do Supabase
    lancamento_a_editar = st.session_state.get('editar_lancamento')
    lancamento_id = lancamento_a_editar.get('id')

    if lancamento_id is None:
         st.error("ID do lançamento a ser editado não encontrado.")
         st.session_state['editar_lancamento'] = None
         st.session_state['show_edit_modal'] = False
         st.rerun()
         return


    is_owner = lancamento_a_editar.get('user_email') == st.session_state.get('usuario_atual_email')
    is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'

    if not (is_owner or is_admin):
        st.error("Você não tem permissão para editar este lançamento.")
        st.session_state['editar_lancamento'] = None
        st.session_state['show_edit_modal'] = False
        st.rerun()
        return

    with st.expander("Editar Lançamento", expanded=True):
        st.subheader(f"Editar Lançamento (ID: {lancamento_id})") # Mostra o ID para debug

        # O formulário contém os campos e o botão de submissão
        # Use o ID do lançamento no key do formulário para garantir unicidade
        with st.form(key=f"edit_lancamento_form_{lancamento_id}"):
            # Usa os dados do lancamento_a_editar para preencher o formulário
            data_str = st.text_input(
                "Data (DD/MM/AAAA)",
                datetime.strptime(lancamento_a_editar.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y"),
                key=f"edit_lanc_data_form_{lancamento_id}"
            )
            descricao = st.text_input("Descrição", lancamento_a_editar.get("Descrição", ""),
                                       key=f"edit_lanc_descricao_form_{lancamento_id}")
            # Captura o tipo de lançamento selecionado primeiro
            tipo = st.selectbox(
                "Tipo de Lançamento",
                ["Receita", "Despesa"],
                index=["Receita", "Despesa"].index(lancamento_a_editar.get("Tipo de Lançamento", "Receita")),
                key=f"edit_lanc_tipo_form_{lancamento_id}",
            )

            # Cria um placeholder para a Categoria
            categoria_placeholder = st.empty()

            categoria = "" # Inicializa a variável de categoria
            # Só exibe o campo Categoria dentro do placeholder se o tipo for Receita (conforme original)
            if tipo == "Receita":
                # Encontra o índice da categoria atual na lista combinada do usuário logado
                current_category = lancamento_a_editar.get("Categorias", "")
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
                    key=f"edit_lanc_categoria_receita_form_{lancamento_id}",
                )
            # Seu código original não tinha seleção de categoria para Despesa na edição.
            # A Demonstração de Resultados usará o que estiver no campo 'Categorias' para Despesas,
            # mesmo que não haja um selectbox para definir isso na UI original.
            valor = st.number_input(
                "Valor", value=lancamento_a_editar.get("Valor", 0.0), format="%.2f", min_value=0.0,
                key=f"edit_lanc_valor_form_{lancamento_id}"
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
                        # Cria um dicionário com os dados atualizados, incluindo o ID do Supabase
                        lancamento_atualizado = {
                            "id": lancamento_id, # Inclui o ID para a função de salvar/atualizar
                            "Data": data_obj,
                            "Descrição": descricao,
                            "Categorias": categoria,  # Salva a categoria (será vazia se não for Receita no original)
                            "Tipo de Lançamento": tipo,
                            "Valor": valor,
                            "user_email": lancamento_a_editar.get('user_email') # Mantém o email original do usuário
                        }
                        # --- ADAPTAÇÃO SUPABASE: Salvar Edição ---
                        if salvar_lancamento_supabase(lancamento_atualizado): # Chama a função de salvar/atualizar no Supabase
                            st.session_state['editar_lancamento'] = None
                            st.session_state['show_edit_modal'] = False
                            st.rerun() # Rerun após salvar no Supabase
                        # --- FIM ADAPTAÇÃO SUPABASE ---
                    except ValueError:
                        st.error("Formato de data inválido. Use DD/MM/AAAA.")

        # Botão cancelar FORA do formulário
        if st.button("Cancelar Edição", key=f"cancel_edit_form_button_{lancamento_id}"):
            st.session_state['editar_lancamento'] = None
            st.session_state['show_edit_modal'] = False
            st.rerun()
    # --- FIM ADAPTAÇÃO SUPABASE: Usando ID para editar ---


def exibir_resumo_central():
    st.subheader("Resumo Financeiro")

    lancamentos_para_resumo = []  # Inicializa a lista a ser usada para o resumo

    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        # --- ADICIONAR LÓGICA DE FILTRAGEM BASEADA NO SELECTBOX ---
        # Pega a seleção atual do selectbox de usuários (definido em exibir_lancamentos)
        usuario_selecionado_nome = st.session_state.get("selectbox_usuario_lancamentos", "Todos os Usuários")

        if usuario_selecionado_nome == "Todos os Usuários":
            # Use a lista completa carregada do Supabase
            lancamentos_para_resumo = st.session_state.get("lancamentos", [])
            st.info("Exibindo resumo de todos os lançamentos.")
        else:
            # Encontre o e-mail do usuário selecionado pelo nome na lista carregada do Supabase
            usuario_selecionado_email = None
            for u in st.session_state.get('usuarios', []):
                if u.get('nome', 'Usuário Sem Nome') == usuario_selecionado_nome:
                    usuario_selecionado_email = u.get('email')
                    break

            if usuario_selecionado_email:
                # Filtra lançamentos localmente pelo e-mail do usuário selecionado para o resumo
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
        # Filtra lançamentos localmente pelo e-mail do usuário logado
        lancamentos_para_resumo = [
            l for l in st.session_state.get("lancamentos", [])
            if l.get('user_email') == usuario_email
        ]
        st.info(f"Exibindo seus lançamentos, {st.session_state.get('usuario_atual_nome', 'usuário')}.")

    # --- Aplicar Filtro por Data ao Resumo ---
    # A filtragem por data já foi aplicada na lista lancamentos_para_exibir na função exibir_lancamentos
    # que é usada para popular a tabela. Aqui no resumo, vamos refiltrar a lista
    # lancamentos_para_resumo com base nos filtros de data aplicados na seção de lançamentos.
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

    # Agora, o resumo será calculado usando a lista filtrada por data E por usuário
    lancamentos_para_resumo = lancamentos_para_resumo_filtrados
    # --- Fim do Filtro por Data ao Resumo ---


    # Inicializa os totais antes do loop
    total_receitas = 0
    total_despesas = 0

    # Agora itera sobre a lista `lancamentos_para_resumo` (que agora inclui filtro por data e usuário)
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


# Função para exportar lançamentos para Excel (mantida a original, adaptada para o novo formato de dados)
def exportar_lancamentos_para_excel(lancamentos_list):
    lancamentos_para_df = []
    for lancamento in lancamentos_list:
        lancamento_copy = lancamento.copy()
        # --- ADAPTAÇÃO SUPABASE: Remove o 'id' e 'user_email' se existirem antes de exportar ---
        if 'id' in lancamento_copy:
            del lancamento_copy['id']
        if 'user_email' in lancamento_copy:
            del lancamento_copy['user_email']
        # --- FIM ADAPTAÇÃO SUPABASE ---
        lancamentos_para_df.append(lancamento_copy)

    df = pd.DataFrame(lancamentos_para_df)

    if not df.empty:
        if 'Data' in df.columns:
            try:
                # As datas vêm como string 'YYYY-MM-DD' do Supabase, converte para datetime e depois para DD/MM/YYYY
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


# Função para exportar lançamentos para PDF (lista detalhada) - Mantida a original, adaptada para o novo formato de dados
def exportar_lancamentos_para_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos. Se não encontrar, usa Arial padrão.
    # Certifique-se de ter um arquivo .ttf (como Arial.ttf) no mesmo diretório do seu script.
    try:
        # Substitua 'Arial_Unicode.ttf' pelo caminho ou nome do seu arquivo .ttf
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_table = 'Arial_Unicode'
    except Exception as e:
        # st.warning(f"Erro ao carregar fonte personalizada para PDF: {e}. Usando fonte padrão.") # Mantendo o aviso na console
        pdf.set_font("Arial", '', 12)
        font_for_table = 'Arial'

    pdf.set_font("Arial", 'B', 12)  # Use negrito da fonte padrão para o título (conforme original)
    report_title = f"Relatório de Lançamentos - {usuario_nome}"
    # Use 'latin1' para codificação no FPDF se estiver tendo problemas com acentos no PDF
    pdf.cell(0, 10, report_title.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')
    pdf.ln(10)

    # --- RESUMO FINANCEIRO ANTES DA TABELA ---
    total_receitas = sum(l.get("Valor", 0) for l in lancamentos_list if l.get("Tipo de Lançamento") == "Receita")
    total_despesas = sum(l.get("Valor", 0) for l in lancamentos_list if l.get("Tipo de Lançamento") == "Despesa")
    saldo = total_receitas - total_despesas
    
    pdf.set_font(font_for_table, 'B', 11)
    pdf.cell(0, 8, "Resumo Financeiro", ln=True)
    
    pdf.set_font(font_for_table, 'B', 10)
    
    # Entradas (normal)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f"Total de Entradas: R$ {total_receitas:.2f}".replace('.', ','), ln=True)
    
    # Saídas (vermelho)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(0, 8, f"Total de Saídas:   R$ {total_despesas:.2f}".replace('.', ','), ln=True)
    
    # Saldo (preto ou vermelho, dependendo do valor)
    if saldo < 0:
        pdf.set_text_color(255, 0, 0)
    else:
        pdf.set_text_color(0, 0, 255)
    
    pdf.cell(0, 8, f"Saldo do Período: R$ {saldo:.2f}".replace('.', ','), ln=True)
    
    # Resetar cor
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    # --- FIM DO RESUMO ---
    
    y_atual = pdf.get_y()
    pdf.line(10, y_atual, 200, y_atual)  # linha horizontal de margem a margem
    pdf.ln(5)

    # Usa a fonte com suporte a acentos (se carregada) ou a padrão para os cabeçalhos e dados da tabela
    pdf.set_font(font_for_table, 'B', 10) # Cabeçalhos em negrito
    col_widths = [20, 90, 40, 20, 25]
    headers = ["Data", "Descrição", "Categoria", "Tipo", "Valor"]

    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C', fill=False)
    pdf.ln()

    pdf.set_font(font_for_table, '', 10)  # Dados da tabela em fonte normal
    for lancamento in lancamentos_list:
        try:
            # Datas vêm do Supabase como 'YYYY-MM-DD', formatar para DD/MM/YYYY
            data_formatada = datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            data_formatada = lancamento.get("Data", "Data Inválida") # Mantém o valor original se a conversão falhar

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

    # --- ADAPTAÇÃO SUPABASE: Buscar dados do signatário da lista de usuários carregada do DB ---
    signatario_nome = ""
    signatario_cargo = ""
    usuario_atual_email = st.session_state.get('usuario_atual_email')
    for u in st.session_state.get('usuarios', []):
        if u.get('email') == usuario_atual_email:
            signatario_nome = u.get("signatarioNome", "")
            signatario_cargo = u.get("signatarioCargo", "")
            break # Encontrou o usuário logado, pode sair do loop
    # --- FIM ADAPTAÇÃO SUPABASE ---

    if signatario_nome or signatario_cargo:
        pdf.set_font("Arial", '', 10) #(If I want to use bold font)pdf.set_font("Arial", 'B', 12)

        if signatario_nome:
            pdf.cell(0, 10, f"Assinado por: {signatario_nome}".encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')

        if signatario_cargo:
            pdf.cell(0, 8, signatario_cargo.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')

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

    plt.title('Distribuição de Receitas', fontsize=20, fontweight='bold', color='#003548')


    temp_filename = f"/tmp/donut_{uuid.uuid4().hex}.png"
    plt.savefig(temp_filename, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()

    return temp_filename

# --- FUNÇÃO para gerar a Demonstração de Resultados em PDF ---
# Mantida a original, usa a lista de lançamentos filtrada por data e usuário
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

    pdf.set_font(font_for_text, 'B', 14) # Título principal com fonte negrito
    report_title = f"Demonstração de Resultados - {usuario_nome}"
    pdf.cell(0, 10, report_title.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')
    pdf.ln(10)

    # --- Processar dados para a Demonstração de Resultados (usa a lista filtrada) ---
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
            total_receitas += valor # Movido para dentro do if Receita para somar apenas receitas
        elif tipo == "Despesa":
            if categoria not in despesas_por_categoria:
                despesas_por_categoria[categoria] = 0
            despesas_por_categoria[categoria] += valor
            total_despesas += valor # Movido para dentro do if Despesa para somar apenas despesas

    # --- Adicionar Receitas ao PDF ---
    pdf.set_font(font_for_text, 'B', 12) # Título da seção em negrito
    pdf.set_text_color(0, 0, 0)
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
    pdf.set_text_color(0, 0, 255)
    pdf.cell(100, 7, "Total Receitas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_receitas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')
    pdf.ln(10)  # Espaço após a seção de Receitas

    # --- Adicionar Despesas ao PDF ---
    pdf.set_font(font_for_text, 'B', 12) # Título da seção em negrito
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Despesas".encode('latin1', 'replace').decode('latin1'), 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10) # Conteúdo da seção em fonte normal
    # Ordenar categorias de despesa alfabeticamente

    # Classificação das Despesas Administrativas (Mantido conforme sua lógica original)
    # total_despesas já calculado acima iterando sobre a lista filtrada
    pdf.cell(100, 7, "Despesas Administrativas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_despesas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10) # Total em negrito
    pdf.set_text_color(255, 0, 0)
    pdf.cell(100, 7, "Total Despesas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_despesas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')
    pdf.ln(10)  # Espaço após a seção de Despesas

    # --- Adicionar Resultado Líquido ---
    resultado_liquido = total_receitas - total_despesas
    pdf.set_font(font_for_text, 'B', 12) # Resultado em negrito

    # Cor do resultado líquido: Azul para positivo, Vermelho para negativo
    if resultado_liquido >= 0:
        pdf.set_text_color(0, 0, 255)  # Azul para lucro
    else:
        pdf.set_text_color(255, 0, 0) # Vermelho para prejuízo

    pdf.cell(100, 10, "Resultado Líquido".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 10, f"R$ {resultado_liquido:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1,
             'R')

    # Resetar cor do texto para preto para qualquer texto futuro (se houver)
    pdf.set_text_color(0, 0, 0)

    y_atual = pdf.get_y()
    pdf.line(10, y_atual, 200, y_atual)  # linha horizontal de margem a margem
    pdf.ln(5)

    #Análise de Gáficos
    pdf.set_font("Arial", size=14, style='B')
    pdf.set_text_color(0, 22, 60)
    pdf.cell(0, 10, "Análise de Gráficos".encode('latin1', 'replace').decode('latin1'), ln=True, align="C")
    pdf.ln(5)

    # --- Gráfico de Donut de Receitas ---
    if receitas_por_categoria:
        donut_path = criar_grafico_donut(receitas_por_categoria)
        pdf.image(donut_path, x=55, y=pdf.get_y(), w=100)
        pdf.ln(110)

    pdf.add_page()

    # --- Gráfico de Barras ----
    plt.figure(figsize=(3, 3.2), facecolor='none') # Ajuste aqui largura x altura

    ax = plt.gca()
    for spine in ax.spines.values():
         spine.set_visible(False)  # Remove borda do gráfico

    categorias_grafico_barras = ['Receitas', 'Despesas']
    valores_grafico_barras = [total_receitas, total_despesas]
    cores_barras = ['#00163C', '#FF0000']  # Cores personalizadas

    barras = plt.bar(categorias_grafico_barras, valores_grafico_barras, color=cores_barras)

    for bar in barras:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + max(valores_grafico_barras)*0.02, f"R$ {yval:.2f}", ha='center', va='bottom', fontsize=10, fontweight='bold', color='black')

    plt.title('Comparativo de Receita x Despesa', fontsize=12, fontweight='bold', color='#003548', pad=20)
    plt.ylabel('Valores (R$)', fontsize=10, fontweight='bold')
    plt.xticks(fontsize=10, fontweight='bold')
    plt.yticks(fontsize=9)
    plt.tight_layout()

    barras_path = f"/tmp/barras_{uuid.uuid4().hex}.png"
    plt.savefig(barras_path, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()

    pdf.image(barras_path, x=55, y=pdf.get_y(), w=100)
    pdf.ln(100)

    y_atual = pdf.get_y()
    pdf.line(10, y_atual, 200, y_atual)  # linha horizontal de margem a margem
    pdf.ln(5)

    # --- Monthly Revenue Bar Chart ---
    plt.figure(figsize=(8, 4), facecolor='none')
    
    # Process data for monthly revenue chart
    monthly_revenue = {}
    for lancamento in lancamentos_list:
        if lancamento.get("Tipo de Lançamento") == "Receita":
            try:
                # Extract month from date
                date_obj = datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d")
                month_key = date_obj.strftime("%b")  # Short month name
                month_num = date_obj.month  # Month number for sorting
                
                if month_key not in monthly_revenue:
                    monthly_revenue[month_key] = {"value": 0, "month_num": month_num}
                monthly_revenue[month_key]["value"] += lancamento.get("Valor", 0)
            except ValueError:
                continue
    
    # Sort months chronologically
    sorted_months = sorted(monthly_revenue.items(), key=lambda x: x[1]["month_num"])
    months = [m[0] for m in sorted_months]
    revenue_values = [m[1]["value"] for m in sorted_months]
    
    # Create the revenue bar chart
    ax = plt.gca()
    for spine in ax.spines.values():
        spine.set_visible(False)  # Remove border
    
    bars = plt.bar(months, revenue_values, color='#00163C')  # Blue color as requested
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, height + max(revenue_values)*0.02,
                f'R$ {height:.2f}', ha='center', va='bottom', fontsize=14, fontweight='bold', color='black')
    
    plt.title('Receita Mensal', fontsize=16, fontweight='bold', color='#003548', pad=20)
    plt.ylabel('Valores (R$)', fontsize=14, fontweight='bold')
    plt.xticks(fontsize=14, fontweight='bold')
    plt.yticks(fontsize=12)
    plt.tight_layout()
    
    # Set background color for the bars to ensure white text is visible
    for bar in bars:
        bar.set_edgecolor('none')
    
    revenue_bars_path = f"/tmp/revenue_bars_{uuid.uuid4().hex}.png"
    plt.savefig(revenue_bars_path, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()
    
    pdf.image(revenue_bars_path, x=30, y=pdf.get_y(), w=150)
    pdf.ln(80)
    
    # --- Monthly Expense Bar Chart ---
    plt.figure(figsize=(8, 4), facecolor='none')
    
    # Process data for monthly expense chart
    monthly_expense = {}
    for lancamento in lancamentos_list:
        if lancamento.get("Tipo de Lançamento") == "Despesa":
            try:
                # Extract month from date
                date_obj = datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d")
                month_key = date_obj.strftime("%b")  # Short month name
                month_num = date_obj.month  # Month number for sorting
                
                if month_key not in monthly_expense:
                    monthly_expense[month_key] = {"value": 0, "month_num": month_num}
                monthly_expense[month_key]["value"] += lancamento.get("Valor", 0)
            except ValueError:
                continue
    
    # Sort months chronologically
    sorted_months = sorted(monthly_expense.items(), key=lambda x: x[1]["month_num"])
    months = [m[0] for m in sorted_months]
    expense_values = [m[1]["value"] for m in sorted_months]
    
    # Create the expense bar chart
    ax = plt.gca()
    for spine in ax.spines.values():
        spine.set_visible(False)  # Remove border
    
    bars = plt.bar(months, expense_values, color='#FF0000')  # Red color as requested
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + max(expense_values)*0.02 if expense_values else 0,
                f'R$ {height:.2f}', ha='center', va='bottom', fontsize=14, fontweight='bold', color='black')
    
    plt.title('Despesa Mensal', fontsize=16, fontweight='bold', color='#003548', pad=20)
    plt.ylabel('Valores (R$)', fontsize=14, fontweight='bold')
    plt.xticks(fontsize=14, fontweight='bold')
    plt.yticks(fontsize=12)
    plt.tight_layout()
    
    # Set background color for the bars to ensure white text is visible
    for bar in bars:
        bar.set_edgecolor('none')
    
    expense_bars_path = f"/tmp/expense_bars_{uuid.uuid4().hex}.png"
    plt.savefig(expense_bars_path, bbox_inches='tight', transparent=True, dpi=300)
    plt.close()
    
    pdf.image(expense_bars_path, x=30, y=pdf.get_y(), w=150)
    pdf.ln(80)

    #pdf.add_page()  # <<<< QUEBRA AQUI PARA NOVA PÁGINA
    pdf.cell(0, 15, "", 0, 1)

    y_atual = pdf.get_y()
    pdf.line(10, y_atual, 200, y_atual)  # linha horizontal de margem a margem
    pdf.ln(5)

    pdf.set_text_color(0, 0, 0) # Resetando o texto para preto

    # --- Comentário Analítico (Usa os totais calculados da lista filtrada) ---
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

    # --- ADAPTAÇÃO SUPABASE: Buscar dados do signatário da lista de usuários carregada do DB ---
    signatario_nome = ""
    signatario_cargo = ""
    usuario_atual_email = st.session_state.get('usuario_atual_email')
    for u in st.session_state.get('usuarios', []):
        if u.get('email') == usuario_atual_email:
            signatario_nome = u.get("signatarioNome", "")
            signatario_cargo = u.get("signatarioCargo", "")
            break # Encontrou o usuário logado
    # --- FIM ADAPTAÇÃO SUPABASE ---

    if signatario_nome or signatario_cargo:
        pdf.set_font("Arial", '', 10)
        if signatario_nome:
            pdf.cell(0, 10, f"Assinado por: {signatario_nome}".encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')

        if signatario_cargo:
            pdf.cell(0, 8, signatario_cargo.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')

    # Finaliza o PDF e retorna como BytesIO
    pdf_output = pdf.output(dest='S')
    return io.BytesIO(pdf_output.encode('latin1')) # No Github adicionar: .encode('latin1'))


# --- ADAPTAÇÃO SUPABASE: Função para carregar lançamentos com filtros (OPCIONALMENTE DO BANCO) ---
# Decidi manter o carregamento de todos os dados no início e filtrar localmente
# para minimizar as mudanças profundas na estrutura existente. Para grandes volumes,
# seria mais eficiente filtrar na query do Supabase.
def carregar_lancamentos_para_exibir(email_usuario=None, data_inicio=None, data_fim=None, todos_lancamentos=None):
    """Carrega lançamentos do Supabase e aplica filtros opcionais."""
    # Aqui vamos usar a lista completa já carregada em st.session_state["lancamentos"]
    # Se você tiver muitos lançamentos, considere mover a lógica de filtro para a query do Supabase
    # usando a função carregar_lancamentos_filtrados que mostrei no exemplo anterior.

    lancamentos = todos_lancamentos if todos_lancamentos is not None else st.session_state.get("lancamentos", [])
    lancamentos_filtrados = lancamentos # Começa com a lista base

    if email_usuario:
        lancamentos_filtrados = [
            l for l in lancamentos_filtrados
            if l.get('user_email') == email_usuario
        ]

    if data_inicio and data_fim:
        data_inicio_str = data_inicio.strftime("%Y-%m-%d")
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        lancamentos_filtrados = [
            l for l in lancamentos_filtrados
            if l.get('Data') and data_inicio_str <= l.get('Data') <= data_fim_str
        ]
    elif data_inicio:
        data_inicio_str = data_inicio.strftime("%Y-%m-%d")
        lancamentos_filtrados = [
            l for l in lancamentos_filtrados
            if l.get('Data') and l.get('Data') >= data_inicio_str
        ]
    elif data_fim:
        data_fim_str = data_fim_fim.strftime("%Y-%m-%d")
        lancamentos_filtrados = [
            l for l in lancamentos_filtrados
            if l.get('Data') and l.get('Data') <= data_fim_str
        ]

    return lancamentos_filtrados

# --- FIM ADAPTAÇÃO SUPABASE: Função de carregar lançamentos com filtros ---


def exibir_lancamentos():
    st.subheader("Lançamentos")

    # Define a variável antes dos blocos if/else e inicializa como lista vazia
    lancamentos_para_exibir = []
    usuario_email = st.session_state.get('usuario_atual_email')
    filename_suffix = st.session_state.get('usuario_atual_nome', 'usuario').replace(" ", "_").lower()
    usuario_para_pdf_title = st.session_state.get('usuario_atual_nome', 'Usuário')


    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        st.info("Visão do Administrador.")

        # --- ADICIONAR SELECTBOX PARA ESCOLHER O USUÁRIO ---
        # Crie uma lista de opções para o selectbox, incluindo a opção "Todos os Usuários"
        # Use a lista de usuários carregada do Supabase
        opcoes_usuarios = ["Todos os Usuários"] + [u.get('nome', 'Usuário Sem Nome') for u in
                                                   st.session_state.get('usuarios', [])]

        # Adicione o selectbox
        usuario_selecionado_nome = st.selectbox(
            "Selecionar Lançamentos do Usuário:",
            opcoes_usuarios,
            key="selectbox_usuario_lancamentos"
        )
        # --- FIM DO SELECTBOX ---

        if usuario_selecionado_nome == "Todos os Usuários":
            # Carrega todos os lançamentos do Supabase (já feito na inicialização)
            # A filtragem por data será aplicada abaixo
            lancamentos_base = st.session_state.get("lancamentos", [])
            st.info("Exibindo todos os lançamentos.")
            filename_suffix = "admin_todos"
            usuario_para_pdf_title = "Todos os Lançamentos"
        else:
            # Encontre o e-mail do usuário selecionado pelo nome
            usuario_selecionado_email = None
            for u in st.session_state.get('usuarios', []):
                if u.get('nome', 'Usuário Sem Nome') == usuario_selecionado_nome:
                    usuario_selecionado_email = u.get('email')
                    break

            if usuario_selecionado_email:
                # Filtra lançamentos localmente pelo e-mail do usuário selecionado
                lancamentos_base = [
                    l for l in st.session_state.get("lancamentos", [])
                    if l.get('user_email') == usuario_selecionado_email
                ]
                st.info(f"Exibindo lançamentos de {usuario_selecionado_nome}.")
                filename_suffix = usuario_selecionado_nome.replace(" ", "_").lower()
                usuario_para_pdf_title = usuario_selecionado_nome
            else:
                st.warning(f"Usuário {usuario_selecionado_nome} não encontrado.")
                lancamentos_base = []  # Lista vazia se o usuário não for encontrado


    else:  # Código existente para usuários não administradores
        # Atribui diretamente à variável lancamentos_para_exibir no bloco else
        # Filtra lançamentos localmente pelo e-mail do usuário logado
        lancamentos_base = [
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
        # Mantém as keys para que o estado seja preservado
        data_inicio_filtro = st.date_input("Data de Início", value=st.session_state.get("data_inicio_filtro", None), key="data_inicio_filtro")

    with col_data_fim:
        # Mantém as keys para que o estado seja preservado
        data_fim_filtro = st.date_input("Data de Fim", value=st.session_state.get("data_fim_filtro", None), key="data_fim_filtro")

    # --- Aplica a filtragem por data sobre a lista base (já filtrada por usuário) ---
    lancamentos_para_exibir = lancamentos_base # Começa com a lista base

    if data_inicio_filtro and data_fim_filtro:
        # Converte as datas de filtro para o formato 'YYYY-MM-DD' para comparação com os dados do DB
        data_inicio_str = data_inicio_filtro.strftime("%Y-%m-%d")
        data_fim_str = data_fim_filtro.strftime("%Y-%m-%d")

        lancamentos_para_exibir = [
            lancamento for lancamento in lancamentos_base
            if lancamento.get('Data') and data_inicio_str <= lancamento.get('Data') <= data_fim_str
        ]
        # Altera o formato de exibição na mensagem para DD/MM/YYYY
        st.info(f"Exibindo lançamentos de {data_inicio_filtro.strftime('%d/%m/%Y')} a {data_fim_filtro.strftime('%d/%m/%Y')}.")
    elif data_inicio_filtro:
        data_inicio_str = data_inicio_filtro.strftime("%Y-%m-%d")
        lancamentos_para_exibir = [
            lancamento for lancamento in lancamentos_base
            if lancamento.get('Data') and lancamento.get('Data') >= data_inicio_str
        ]
        # Altera o formato de exibição na mensagem para DD/MM/YYYY
        st.info(f"Exibindo lançamentos a partir de {data_inicio_filtro.strftime('%d/%m/%Y')}.")
    elif data_fim_filtro:
        data_fim_str = data_fim_filtro.strftime("%Y-%m-%d")
        lancamentos_para_exibir = [
            lancamento for lancamento in lancamentos_base
            if lancamento.get('Data') and lancamento.get('Data') <= data_fim_str
        ]
        # Altera o formato de exibição na mensagem para DD/MM/YYYY
        st.info(f"Exibindo lançamentos até {data_fim_filtro.strftime('%d/%m/%Y')}.")

    # Agora, a lista a ser exibida e exportada é 'lancamentos_para_exibir'
    # st.session_state["lancamentos"] já contém todos os lançamentos do DB,
    # a lista lancamentos_para_exibir é uma sub-lista filtrada para exibição e exportação.
    # --- Fim do Filtro por Data ---

    if not lancamentos_para_exibir:
        st.info("Nenhum lançamento encontrado para este usuário e/ou período.")
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

    # Ordenar lançamentos por data (do mais recente para o mais antigo) - Ordena a lista filtrada
    try:
        # Usamos a lista que já foi filtrada/selecionada corretamente
        lancamentos_para_exibir.sort(key=lambda x: datetime.strptime(x.get('Data', '1900-01-01'), '%Y-%m-%d'),
                                      reverse=True)
    except ValueError:
        st.warning("Não foi possível ordenar os lançamentos por data devido a formato inválido.")

    # --- Botões de Exportação ---
    # Adicionamos uma terceira coluna para o novo botão da Demonstração de Resultados
    # AUMENTANDO A LARGURA DA COLUNA DE AÇÕES (último valor na lista)
    col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1]) # Mantendo 3 colunas para os botões de exportação

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

    # Iteramos diretamente sobre a lista de lançamentos para exibir (que já está filtrada e ordenada)
    for i, lancamento in enumerate(lancamentos_para_exibir):
        # --- ADAPTAÇÃO SUPABASE: Usar o 'id' do Supabase para identificar o lançamento ---
        lancamento_id = lancamento.get('id')
        if lancamento_id is None:
             st.warning(f"Lançamento sem ID encontrado: {lancamento}. Pulando.")
             continue # Pula lançamentos sem ID (não deveria acontecer com o Supabase configurado)

        # AQUI ESTÁ A MODIFICAÇÃO: Usando a mesma nova proporção para as colunas de dados
        col1, col2, col3, col4, col5, col6 = st.columns(
            [2, 3, 2, 2, 2, 4])  # Proporção da última coluna aumentada para 4
        try:
            # Datas vêm do Supabase como 'YYYY-MM-DD', formatar para DD/MM/YYYY para exibição
            data_formatada = datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            data_formatada = lancamento.get("Data", "Data Inválida") # Mantém o valor original se a conversão falhar

        col1.write(data_formatada)
        col2.write(lancamento.get("Descrição", ""))
        col3.write(lancamento.get("Tipo de Lançamento", ""))
        col4.write(lancamento.get("Categorias", ""))
        col5.write(f"R$ {lancamento.get('Valor', 0.0):.2f}")

        with col6:
            is_owner = lancamento.get('user_email') == st.session_state.get('usuario_atual_email')
            is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'

            # Usamos o ID do Supabase para as chaves dos botões
            if (is_owner or is_admin) and not st.session_state.get('show_add_modal') and not st.session_state.get(
                    'show_edit_modal'):
                # Ajusta as colunas para os botões de ação - MANTENDO O DEFAULT DE [1, 1]
                # Como a coluna 6 principal ficou mais larga, as sub-colunas dentro dela
                # também ficarão mais largas automaticamente.
                col_editar, col_excluir = st.columns(2) # Mantendo o default [1, 1]
                with col_editar:
                    # Ao clicar em editar, armazena o dicionário COMPLETO do lançamento, incluindo o 'id'
                    if st.button("Editar", key=f"editar_{lancamento_id}"):
                        st.session_state["editar_lancamento"] = lancamento # Armazena o dicionário completo
                        st.session_state['show_edit_modal'] = True
                        st.rerun()
                with col_excluir:
                    # Para excluir, usamos o ID do Supabase
                    # --- ADAPTAÇÃO SUPABASE: Chamar a função de exclusão do DB ---
                    if st.button("Excluir", key=f"excluir_{lancamento_id}"):
                         if excluir_lancamento_db(lancamento_id): # Chama a função que exclui no Supabase
                             st.rerun() # Rerun após exclusão bem-sucedida
                    # --- FIM ADAPTAÇÃO SUPABASE ---
            elif not (is_owner or is_admin):
                st.write("Sem permissão")

        # --- FIM ADAPTAÇÃO SUPABASE: Usar o 'id' do Supabase ---


def pagina_dashboard():
    if not st.session_state.get('autenticado'):
        st.warning("Você precisa estar logado para acessar o dashboard.")
        return

    col_nav1, _ = st.columns(2)
    if col_nav1.button("⚙️ Configurações"):
        st.session_state['pagina_atual'] = 'configuracoes'
        st.rerun()

    st.title(f"Controle Financeiro - {st.session_state.get('usuario_atual_nome', 'Usuário')}")
    # exibir_resumo_central() # Chamado dentro de exibir_lancamentos agora ou precisa adaptar para usar a lista filtrada?
                             # Deixei chamado separadamente, ele refiltra a lista completa.

    modal_ativo = st.session_state.get('show_add_modal') or st.session_state.get('show_edit_modal')

    if not modal_ativo:
        if st.button("➕ Adicionar Novo Lançamento"):
            st.session_state['show_add_modal'] = True
            st.rerun()
        # Exibe o resumo e os lançamentos filtrados
        exibir_resumo_central() # Chame o resumo antes dos lançamentos se quiser o layout original
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
    # --- ADAPTAÇÃO SUPABASE: Encontre o usuário logado pela lista do session_state (carregada do DB) ---
    usuario_logado = None
    usuario_logado_id = None
    for u in st.session_state.get('usuarios', []):
        if u.get('email') == usuario_logado_email:
            usuario_logado = u
            usuario_logado_id = u.get('id') # Pega o ID do Supabase
            break
    # --- FIM ADAPTAÇÃO SUPABASE ---


    # Verificação adicional para garantir que o usuário logado foi encontrado
    if usuario_logado:
        st.subheader(f"Editar Meu Perfil ({usuario_logado.get('tipo', 'Tipo Desconhecido')})")
        edit_nome_proprio = st.text_input("Nome", usuario_logado.get('nome', ''), key="edit_meu_nome")
        st.text_input("E-mail", usuario_logado.get('email', ''), disabled=True)
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
                # --- ADAPTAÇÃO SUPABASE: Atualizar usuário logado no DB ---
                dados_para_atualizar = {
                    "nome": edit_nome_proprio,
                    "email": usuario_logado.get('email'),  # Add this line to include email
                    "signatarioNome": signatario_nome,
                    "signatarioCargo": signatario_cargo,
                }
                if nova_senha_propria:
                     dados_para_atualizar["senha"] = nova_senha_propria # Repito: use hashing em produção!
                
                # Chame a função de salvar/atualizar, passando o ID do usuário logado
                if salvar_usuario_supabase({"id": usuario_logado_id, **dados_para_atualizar}): # Inclui o ID e os dados
                     st.session_state['usuario_atual_nome'] = edit_nome_proprio # Atualiza o nome na sessão
                     st.rerun() # Rerun após salvar no Supabase
                # --- FIM ADAPTAÇÃO SUPABASE ---
            else:
                st.error("As novas senhas não coincidem.")
    else:
        st.error("Erro ao carregar informações do seu usuário.")

    # --- Campo para adicionar e gerenciar categorias de Receitas (agora específicas por usuário) ---
    st.subheader("Gerenciar Categorias de Receitas")
    st.markdown("---")

    # Verificação adicional antes de tentar gerenciar categorias (usa a variável usuario_logado já encontrada)
    if usuario_logado:
        # Garante que a chave 'categorias_receita' existe para o usuário logado
        if 'categorias_receita' not in usuario_logado or usuario_logado['categorias_receita'] is None:
             usuario_logado['categorias_receita'] = [] # Inicializa se for None

        usuario_categorias_atuais = usuario_logado['categorias_receita']
        # Inclui as categorias padrão apenas para exibição e verificação de duplicidade
        todas_categorias_receita_disponiveis = CATEGORIAS_PADRAO_RECEITA + usuario_categorias_atuais

        nova_categoria_receita = st.text_input("Nome da Nova Categoria de Receita", key="nova_categoria_receita_input")
        if st.button("Adicionar Categoria de Receita"):
            if nova_categoria_receita:
                # Verifica se a categoria já existe (case-insensitive check) na lista combinada do usuário
                if nova_categoria_receita.lower() not in [c.lower() for c in todas_categorias_receita_disponiveis]:
                    # --- ADAPTAÇÃO SUPABASE: Adicionar categoria na lista do usuário no DB ---
                    novas_categorias_receita_usuario = usuario_categorias_atuais + [nova_categoria_receita]
                    dados_para_atualizar = {
                        "categorias_receita": novas_categorias_receita_usuario,
                        "email": usuario_logado.get('email')  # Add this line to include email
                    }


                    if salvar_usuario_supabase({"id": usuario_logado_id, **dados_para_atualizar}): # Atualiza no Supabase
                        # A função salvar_usuario_supabase já recarrega a lista de usuários no session_state
                        # e a lógica de login/inicialização já atualiza st.session_state['todas_categorias_receita']
                        st.success(
                            f"Categoria '{nova_categoria_receita}' adicionada com sucesso às suas categorias de receita!")
                        st.rerun() # Rerun após salvar no Supabase
                    # --- FIM ADAPTAÇÃO SUPABASE ---
                else:
                    st.warning(
                        f"A categoria '{nova_categoria_receita}' já existe nas suas categorias de receita ou nas padrão.")
            else:
                st.warning("Por favor, digite o nome da nova categoria de receita.")

        st.subheader("Suas Categorias de Receitas Personalizadas")
        # Exibe as categorias personalizadas com opção de exclusão
        if usuario_categorias_atuais:
            st.write("Clique no botão 'Excluir' ao lado de uma categoria personalizada para removê-la.")
    
            # Filtra lançamentos do usuário logado para verificar uso da categoria (usa a lista carregada do DB)
            lancamentos_do_usuario = [
                l for l in st.session_state.get("lancamentos", [])
                if l.get('user_email') == usuario_logado_email and l.get('Tipo de Lançamento') == 'Receita'
            ]
            categorias_receita_em_uso = {l.get('Categorias') for l in lancamentos_do_usuario if l.get('Categorias')}

            # Itera sobre categorias personalizadas para exibir e permitir exclusão
            # Percorra uma CÓPIA da lista se for modificar durante a iteração
            for i, categoria in enumerate(list(usuario_categorias_atuais)): # Itera sobre uma cópia
                col_cat, col_del = st.columns([3, 1])
                col_cat.write(categoria)
                # Verifica se a categoria está em uso em algum lançamento de receita do usuário
                if categoria in categorias_receita_em_uso:
                    col_del.write("Em uso")
                else:
                    # --- ADAPTAÇÃO SUPABASE: Excluir categoria da lista do usuário no DB ---
                    if col_del.button("Excluir", key=f"del_cat_receita_{categoria}_{i}"): # Use categoria no key para unicidade
                        novas_categorias_receita_usuario = [c for c in usuario_categorias_atuais if c != categoria]
                        dados_para_atualizar = {
                            "id": usuario_logado_id,
                            "categorias_receita": novas_categorias_receita_usuario,
                            "email": usuario_logado.get("email")  # <- ESSENCIAL para evitar o erro
                        }
                        if salvar_usuario_supabase({"id": usuario_logado_id, **dados_para_atualizar}): # Atualiza no Supabase
                            # A função salvar_usuario_supabase já recarrega a lista de usuários no session_state
                            # e a lógica de login/inicialização já atualiza st.session_state['todas_categorias_receita']
                            st.success(f"Categoria '{categoria}' excluída com sucesso!")
                            st.rerun() # Rerun após salvar no Supabase
                    # --- FIM ADAPTAÇÃO SUPABASE ---
        else:
            st.info("Você ainda não adicionou nenhuma categoria de receita personalizada.")

    else:
        st.error("Erro ao carregar informações de categorias para o seu usuário.")

    # --- Manter apenas a seção de Gerenciar Usuários para Admin ---
    # Removendo a seção de gerenciar categorias de Despesas que eu adicionei antes
    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        st.markdown("---")
        st.subheader("Gerenciar Usuários (Apenas Admin)")

        # --- ADAPTAÇÃO SUPABASE: Controle de edição de usuário por ID do DB ---
        if st.session_state.get('editar_usuario_data') is not None: # Verifica se há dados de usuário para editar
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
                        # Verifica se o email já existe na lista carregada do Supabase
                        elif any(u.get('email') == novo_email for u in st.session_state.get('usuarios', [])):
                            st.warning(f"E-mail '{novo_email}' já cadastrado.")
                        else:
                            # --- ADAPTAÇÃO SUPABASE: Salvar novo usuário no DB ---
                            novo_usuario_data = {
                                "nome": novo_nome,
                                "email": novo_email,
                                "senha": nova_senha, # Em um app real, use hashing de senha!
                                "tipo": novo_tipo,
                                "categorias_receita": [], # Inicializa categorias personalizadas
                                # Não adiciona categorias_despesa aqui, mantendo o original
                            }
                            if salvar_usuario_supabase(novo_usuario_data): # Chama a função que salva no Supabase
                                st.success(f"Usuário '{novo_nome}' adicionado com sucesso!")
                                st.rerun() # Rerun após salvar no Supabase
                            # --- FIM ADAPTAÇÃO SUPABASE ---

            st.subheader("Lista de Usuários")
            if st.session_state.get('usuarios'):
                col_user_nome, col_user_email, col_user_tipo, col_user_acoes = st.columns([3, 4, 2, 3])
                col_user_nome.markdown("**Nome**")
                col_user_email.markdown("**E-mail**")
                col_user_tipo.markdown("**Tipo**")
                col_user_acoes.markdown("**Ações**")

                # Não liste o próprio usuário Admin logado para evitar que ele se exclua acidentalmente
                usuarios_para_listar = [u for u in st.session_state.get('usuarios', []) if
                                        u.get('email') != usuario_logado_email]

                # --- ADAPTAÇÃO SUPABASE: Iterar sobre a lista carregada do DB e usar IDs ---
                for i, usuario in enumerate(usuarios_para_listar):
                    user_id = usuario.get('id') # Pega o ID do Supabase
                    if user_id is None:
                        st.warning(f"Usuário sem ID encontrado na lista: {usuario}. Pulando.")
                        continue # Pula usuários sem ID

                    col1, col2, col3, col4 = st.columns([3, 4, 2, 3])
                    col1.write(usuario.get('nome', ''))
                    col2.write(usuario.get('email', ''))
                    col3.write(usuario.get('tipo', ''))

                    with col4:
                        col_edit_user, col_del_user = st.columns(2)
                        with col_edit_user:
                            # Ao clicar em editar, armazena o dicionário COMPLETO do usuário, incluindo o 'id'
                            if st.button("Editar", key=f"edit_user_{user_id}"): # Usa o ID do Supabase para o key
                                st.session_state['editar_usuario_data'] = usuario # Armazena o dicionário completo
                                st.session_state['editar_usuario_index'] = i # Mantém o índice local para render_edit_usuario_form (pode ser adaptado para usar só o ID)
                                st.rerun()
                        with col_del_user:
                            # Só permite excluir se não for o usuário logado
                            if usuario.get('email') != usuario_logado_email:
                                # --- ADAPTAÇÃO SUPABASE: Chamar a função de exclusão do DB ---
                                if st.button("Excluir", key=f"del_user_{user_id}", help="Excluir este usuário"): # Usa o ID do Supabase para o key
                                    if excluir_usuario_db(user_id): # Chama a função que exclui no Supabase
                                         st.rerun() # Rerun após exclusão bem-sucedida
                                # --- FIM ADAPTAÇÃO SUPABASE ---
                            else:
                                st.write("Não pode excluir a si mesmo")
                # --- FIM ADAPTAÇÃO SUPABASE: Iterar sobre a lista carregada do DB ---

            else:
                st.info("Nenhum outro usuário cadastrado.")

    elif st.session_state.get('tipo_usuario_atual') == 'Cliente':
        st.markdown("---")
        st.subheader("Gerenciar Usuários")
        st.info("Esta seção está disponível apenas para administradores.")


# --- ADAPTAÇÃO SUPABASE: Função para renderizar formulário de edição de usuário (USA DADOS DO DB) ---
def render_edit_usuario_form():
    # Verifica se há dados de usuário para editar armazenados na sessão
    if st.session_state.get('editar_usuario_data') is None:
        return

    # Pega os dados do usuário a ser editado diretamente do session_state (carregado do DB)
    usuario_a_editar = st.session_state['editar_usuario_data']
    user_id = usuario_a_editar.get('id') # Pega o ID do Supabase

    if user_id is None:
        st.error("ID do usuário a ser editado não encontrado.")
        st.session_state['editar_usuario_data'] = None
        st.session_state['editar_usuario_index'] = None
        st.rerun()
        return

    # Verifica se o usuário logado é administrador e não está tentando editar a si mesmo através deste modal
    usuario_logado_email = st.session_state.get('usuario_atual_email')
    if st.session_state.get('tipo_usuario_atual') != 'Administrador' or usuario_a_editar.get('email') == usuario_logado_email:
        st.error("Você não tem permissão para editar este usuário desta forma.")
        st.session_state['editar_usuario_data'] = None
        st.session_state['editar_usuario_index'] = None
        st.rerun()
        return

    # Use o ID do Supabase no key do expander e do formulário
    with st.expander(f"Editar Usuário: {usuario_a_editar.get('nome', '')} (ID: {user_id})", expanded=True):
        st.subheader(f"Editar Usuário: {usuario_a_editar.get('nome', '')}")
        with st.form(key=f"edit_usuario_form_{user_id}"): # Usa o ID do Supabase para o key do formulário
            # Usa os dados do usuario_a_editar (carregados do DB) para preencher o formulário
            edit_nome = st.text_input("Nome", usuario_a_editar.get('nome', ''),
                                      key=f"edit_user_nome_{user_id}") # Usa o ID no key
            st.text_input("E-mail", usuario_a_editar.get('email', ''), disabled=True,
                          key=f"edit_user_email_{user_id}") # Usa o ID no key
            edit_senha = st.text_input("Nova Senha (deixe em branco para manter)", type="password", value="",
                                     key=f"edit_user_senha_{user_id}") # Usa o ID no key
            edit_tipo = st.selectbox("Tipo", ["Cliente", "Administrador"], index=["Cliente", "Administrador"].index(
                usuario_a_editar.get('tipo', 'Cliente')), key=f"edit_user_tipo_{user_id}") # Usa o ID no key

            submit_edit_user_button = st.form_submit_button("Salvar Edição do Usuário")

            if submit_edit_user_button:
                # --- ADAPTAÇÃO SUPABASE: Atualizar usuário no DB ---
                dados_para_atualizar = {
                    "nome": edit_nome,  # Changed to lowercase for consistency
                    "email": usuario_a_editar.get('email'),  # Add this line to include email
                    "tipo": edit_tipo,  # Changed to lowercase for consistency
                }

                if edit_senha: # Atualiza a senha apenas se uma nova foi digitada
                    dados_para_atualizar["Senha"] = edit_senha # Lembre-se: em um app real, use hashing

                # Chame a função de salvar/atualizar, passando o ID do usuário e os dados
                if salvar_usuario_supabase({"id": user_id, **dados_para_atualizar}): # Inclui o ID e os dados
                    st.success("Usuário atualizado com sucesso!")
                    st.session_state['editar_usuario_data'] = None
                    st.session_state['editar_usuario_index'] = None # Limpa o índice local também
                    st.rerun() # Rerun após salvar no Supabase
                # --- FIM ADAPTAÇÃO SUPABASE ---

        # Botão cancelar FORA do formulário (usa o ID do Supabase para o key)
        if st.button("Cancelar Edição", key=f"cancel_edit_user_form_{user_id}"):
            st.session_state['editar_usuario_data'] = None
            st.session_state['editar_usuario_index'] = None # Limpa o índice local também
            st.rerun()
# --- FIM ADAPTAÇÃO SUPABASE: Função para renderizar formulário de edição de usuário ---


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
        st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy() # Reseta categorias de receita
        # Não reseta categorias de despesa, pois não eram gerenciadas por usuário no original
        st.session_state['pagina_atual'] = 'dashboard' # Redireciona para o login
        # Limpa dados de edição em sessão ao sair
        st.session_state['editar_lancamento'] = None
        st.session_state['show_edit_modal'] = False
        st.session_state['editar_usuario_data'] = None
        st.session_state['editar_usuario_index'] = None
        st.session_state['show_add_modal'] = False # Garante que o modal de adicionar fecha
        st.rerun()
