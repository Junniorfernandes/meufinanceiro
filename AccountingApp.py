import streamlit as st
from datetime import datetime
import json
import os
import pandas as pd
import io
from fpdf import FPDF # Certifique-se de que a biblioteca fpdf2 está instalada (pip install fpdf2)

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
        json.dump(st.session_state.get('usuarios', []), f, indent=4) # Adicionado indent para melhor leitura do JSON

def carregar_usuarios():
    # Lista de usuários a serem adicionados caso o arquivo não exista ou esteja vazio/inválido
    usuarios_iniciais_padrao = [
        {
            "Nome": "Junior Fernandes",
            "Email": "valmirfernandescontabilidade@gmail.com",
            "Senha": "114316", # **Aviso: Senha em texto plano, inseguro para produção!**
            "Tipo": "Administrador" # Mapeando 'Função' para 'Tipo' conforme seu código
        },
        {
            "Nome": "Junior Fernandes",
            "Email": "valmirfernandescontabilidade@hmail.com",
            "Senha": "123456", # **Aviso: Senha em texto plano, inseguro para produção!**
            "Tipo": "Cliente" # Mapeando 'Função' para 'Tipo' conforme seu código
        },
        {
            "Nome": "Camila Garcia",
            "Email": "boatardecamila@gmail.com",
            "Senha": "123456", # **Aviso: Senha em texto plano, inseguro para produção!**
            "Tipo": "Cliente" # Mapeando 'Função' para 'Tipo' conforme seu código
        }
    ]

    if os.path.exists(USUARIOS_FILE):
        try:
            with open(USUARIOS_FILE, "r") as f:
                content = f.read()
                if content:
                    usuarios = json.loads(content)
                    # Garante que cada usuário tem a lista de categorias_receita (se não existir)
                    # Seu código original já faz isso, o que é bom.
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
        json.dump(st.session_state.get("lancamentos", []), f, indent=4) # Adicionado indent

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
# Garante que a função carregar_usuarios é chamada antes de qualquer operação com st.session_state['usuarios']
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
# if "lancamentos" not in st.session_state: # Esta linha é redundante após carregar_lancamentos()
#     st.session_state["lancamentos"] = []

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
    # Adicionar validação para não excluir o último admin
    admins = [u for u in st.session_state.get('usuarios', []) if u.get('Tipo') == 'Administrador']
    if len(admins) == 1 and st.session_state['usuarios'][index].get('Tipo') == 'Administrador':
        st.warning("Não é possível excluir o último usuário administrador.")
        return

    # Antes de excluir o usuário, podemos verificar se há lançamentos associados
    # e decidir o que fazer (excluir lançamentos, reatribuir, etc.).
    # Por simplicidade, vamos apenas excluir o usuário e MANTER seus lançamentos por enquanto.
    # Uma abordagem melhor seria desvincular os lançamentos ou ter uma opção para excluí-los também.
    st.session_state['usuarios'].pop(index)
    salvar_usuarios()
    st.success("Usuário excluído com sucesso!")
    st.rerun()


def pagina_login():
    st.title("Login")
    email = st.text_input("E-mail", key="login_email")
    senha = st.text_input("Senha", type="password", key="login_senha")
    login_button = st.button("Entrar", key="login_button")

    if login_button:
        for i, usuario in enumerate(st.session_state.get('usuarios', [])):
            # Comparação agora usa as chaves corretas ('Email', 'Senha', 'Nome', 'Tipo')
            if usuario.get('Email') == email and usuario.get('Senha') == senha:
                st.session_state['autenticado'] = True
                st.session_state['usuario_atual_email'] = usuario.get('Email')
                st.session_state['usuario_atual_nome'] = usuario.get('Nome')
                st.session_state['tipo_usuario_atual'] = usuario.get('Tipo')
                st.session_state['usuario_atual_index'] = i # Guarda o índice do usuário logado

                # Carrega as categorias personalizadas de receita do usuário logado e combina com as padrão
                usuario_categorias_receita = usuario.get('categorias_receita', [])
                todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEita + usuario_categorias_receita))
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
            descricao = st.text_input("Descrição", key="add_lanc_descricao_form")
            # Captura o tipo de lançamento selecionado primeiro
            tipo = st.selectbox("Tipo de Lançamento", ["Receita", "Despesa"], key="add_lanc_tipo_form")

            # Cria um placeholder para a Categoria
            categoria_placeholder = st.empty()

            categoria = "" # Inicializa a variável de categoria
            # Só exibe o campo Categoria dentro do placeholder se o tipo for Receita (conforme original)
            if tipo == "Receita":
                # Usa a lista combinada de categorias de receita do usuário logado
                categorias_disponiveis = st.session_state.get('todas_categorias_receita', CATEGORIAS_PADRAO_RECEITA)
                categoria = categoria_placeholder.selectbox(
                    "Categoria",
                    categorias_disponiveis,
                    key="add_lanc_categoria_receita_form"
                )
            # Se o tipo não for Receita, o placeholder permanece vazio, e 'categoria' continua ""
            # Seu código original não tinha seleção de categoria para Despesa aqui.

            valor = st.number_input("Valor", format="%.2f", min_value=0.0, key="add_lanc_valor_form")

            # Botão de submissão DENTRO do formulário
            submit_button = st.form_submit_button("Adicionar Lançamento")

            if submit_button:
                # Validação de categoria apenas para Receita (conforme original)
                if not data_str or not descricao or valor is None or (tipo == "Receita" and not categoria):
                    st.warning("Por favor, preencha todos os campos obrigatórios.")
                else:
                    try:
                        data_obj = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                        novo_lancamento = {
                            "Data": data_obj,
                            "Descrição": descricao,
                            "Categorias": categoria, # Salva a categoria (será vazia se não for Receita no original)
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
        # if st.button("Cancelar", key="cancel_add_form_button"): # Este botão não é necessário se o formulário está no expander
        #      st.session_state['show_add_modal'] = False
        #      st.rerun()


def render_edit_lancamento_form():
    if not st.session_state.get('autenticado') or st.session_state.get('editar_indice') is None:
        return

    indice = st.session_state["editar_indice"]
    # Use try-except para lidar com índice inválido de forma mais segura
    try:
         lancamento_a_editar = st.session_state.get("lancamentos", [])[indice]
    except IndexError:
         st.error("Lançamento a ser editado não encontrado ou índice inválido.")
         st.session_state['editar_indice'] = None
         st.session_state['editar_lancamento'] = None
         st.session_state['show_edit_modal'] = False
         st.rerun()
         return


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
        # Note: A chave do formulário deve ser única por instância, então f"edit_lancamento_form_{indice}" é bom.
        with st.form(key=f"edit_lancamento_form_{indice}"):
            lancamento = st.session_state["editar_lancamento"] # Use o lancamento salvo no state para pré-popular

            # Use o lancamento carregado para pré-popular os campos
            data_str = st.text_input(
                "Data (DD/MM/AAAA)",
                datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y"),
                key=f"edit_lanc_data_form_{indice}"
            )
            descricao = st.text_input("Descrição", lancamento.get("Descrição", ""), key=f"edit_lanc_descricao_form_{indice}")

            # Encontra o índice correto para o selectbox de Tipo
            tipo_options = ["Receita", "Despesa"]
            try:
                default_tipo_index = tipo_options.index(lancamento.get("Tipo de Lançamento", "Receita"))
            except ValueError:
                default_tipo_index = 0 # Default para Receita se o tipo salvo for inválido

            tipo = st.selectbox(
                "Tipo de Lançamento",
                tipo_options,
                index=default_tipo_index,
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
                     default_index_categoria = categorias_disponiveis.index(current_category)
                 except ValueError:
                     # Se a categoria salva não estiver na lista atual, use a primeira opção
                     default_index_categoria = 0
                     if current_category and current_category != "Sem Categoria":
                         st.warning(f"A categoria salva '{current_category}' não está na lista de categorias de receita. Selecione uma nova.")
                     # Adicionar a categoria antiga à lista temporariamente para seleção se desejado?
                     # Ex: categorias_disponiveis = list(dict.fromkeys([current_category] + categorias_disponiveis))
                     # Mas isso complica o gerenciamento de categorias. Mantendo a lógica original.


                 categoria = categoria_placeholder.selectbox(
                    "Categoria",
                    categorias_disponiveis,
                    index=default_index_categoria,
                    key=f"edit_lanc_categoria_receita_form_{indice}",
                )
            else:
                 # Para despesas, apenas exibe a categoria salva como texto (sem opção de edição na UI original)
                 # Ou você pode adicionar um campo de texto para editar a categoria de despesa aqui se quiser.
                 # Mantendo o comportamento original que não editava a categoria de despesa.
                 categoria = lancamento.get("Categorias", "") # Mantém a categoria existente

            valor = st.number_input(
                "Valor", value=lancamento.get("Valor", 0.0), format="%.2f", min_value=0.0, key=f"edit_lanc_valor_form_{indice}"
            )

            # Botão de submissão DENTRO do formulário
            submit_button = st.form_submit_button("Salvar Edição")

            if submit_button:
                 # Validação de categoria apenas para Receita (conforme original)
                 # A validação da categoria para Receita precisa verificar se 'categoria' foi preenchida SE o tipo for Receita
                 # Se o tipo for Despesa, a categoria pode ser vazia ou o valor do campo 'Categorias' existente.
                if not data_str or not descricao or valor is None or (tipo == "Receita" and not categoria):
                    st.warning("Por favor, preencha todos os campos obrigatórios (Data, Descrição, Valor e Categoria para Receita).")
                else:
                    try:
                        data_obj = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                        # Atualiza o lançamento no estado
                        st.session_state["lancamentos"][indice] = {
                            "Data": data_obj,
                            "Descrição": descricao,
                            "Categorias": categoria, # Salva a categoria (será a selecionada para Receita, ou a antiga para Despesa)
                            "Tipo de Lançamento": tipo,
                            "Valor": valor,
                            "user_email": lancamento_a_editar.get('user_email') # Mantém o email do usuário original
                        }
                        salvar_lancamentos()
                        st.success("Lançamento editado com sucesso!")
                        # Limpa as variáveis de estado de edição para fechar o formulário
                        st.session_state['editar_indice'] = None
                        st.session_state['editar_lancamento'] = None
                        st.session_state['show_edit_modal'] = False
                        st.rerun()
                    except ValueError:
                        st.error("Formato de data inválido. Use DD/MM/AAAA.")

        # Botão cancelar FORA do formulário
        # if st.button("Cancelar Edição", key=f"cancel_edit_form_button_{indice}"): # Este botão não é necessário se o formulário está no expander
        #     st.session_state['editar_indice'] = None
        #     st.session_state['editar_lancamento'] = None
        #     st.session_state['show_edit_modal'] = False
        #     st.rerun()


def exibir_resumo_central():
    st.subheader("Resumo Financeiro")

    if st.session_state.get('tipo_usuario_atual') == 'Administrador':
        lancamentos_filtrados = st.session_state.get("lancamentos", [])
        st.info("Exibindo resumo de TODOS os lançamentos (Admin view).")
    else:
        usuario_email = st.session_state.get('usuario_atual_email')
        lancamentos_filtrados = [
            l for l in st.session_state.get("lancamentos", [])
            if l.get('user_email') == usuario_email # Filtra por user_email
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

    # Ajustar cor do total geral
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
    # Prepara os dados, excluindo a coluna 'user_email' para a exportação
    lancamentos_para_df = []
    for lancamento in lancamentos_list:
        lancamento_copy = lancamento.copy()
        if 'user_email' in lancamento_copy:
            del lancamento_copy['user_email']
        lancamentos_para_df.append(lancamento_copy)

    df = pd.DataFrame(lancamentos_para_df)

    if not df.empty:
        # Formata a coluna Data para DD/MM/AAAA
        if 'Data' in df.columns:
             try:
                df['Data'] = pd.to_datetime(df['Data']).dt.strftime('%d/%m/%Y')
             except Exception as e:
                 st.warning(f"Erro ao formatar a coluna 'Data' para exportação Excel: {e}")

        # Formata a coluna Valor para R$ X,XX com vírgula
        if 'Valor' in df.columns:
             try:
                df['Valor'] = df['Valor'].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))
             except Exception as e:
                 st.warning(f"Erro ao formatar a coluna 'Valor' para exportação Excel: {e}")

    output = io.BytesIO()
    try:
        # Use 'openpyxl' engine para arquivos .xlsx
        df.to_excel(output, index=False, sheet_name='Lançamentos', engine='openpyxl')
        output.seek(0)
        return output
    except ImportError:
        st.error("A biblioteca 'openpyxl' é necessária para exportar para Excel. Instale com `pip install openpyxl`.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o arquivo Excel: {e}")
        return None

# Função para exportar lançamentos para PDF (lista detalhada) - Mantida a original, ajustada para fpdf2
def exportar_lancamentos_para_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF() # Usando fpdf2
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos. Se não encontrar, usa Arial padrão.
    # Certifique-se de ter um arquivo .ttf (como Arial_Unicode.ttf) no mesmo diretório do seu script.
    # Você pode precisar instalar a fonte no seu sistema ou colocar o arquivo .ttf junto com o script.
    try:
        # Substitua 'Arial_Unicode.ttf' pelo nome do arquivo da fonte que você tem e suporta acentos.
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_text = 'Arial_Unicode'
    except Exception as e:
         # Fallback para fonte padrão se a fonte personalizada não carregar
         # st.warning(f"Erro ao carregar fonte personalizada para PDF: {e}. Usando fonte padrão (pode não suportar acentos corretamente).")
         pdf.set_font("Arial", '', 12)
         font_for_text = 'Arial'


    pdf.set_font(font_for_text, 'B', 12) # Título principal com negrito
    report_title = f"Relatório de Lançamentos - {usuario_nome}"
    # Encoding 'latin1' é uma tentativa comum para lidar com acentos básicos no FPDF original. fpdf2 tem melhor suporte.
    # pdf.cell(0, 10, report_title.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C') # Linha original
    pdf.cell(0, 10, report_title, 0, 1, 'C') # fpdf2 lida melhor com UTF-8
    pdf.ln(10)

    # Usa a fonte com suporte a acentos (se carregada) ou a padrão para os cabeçalhos e dados da tabela
    pdf.set_font(font_for_text, 'B', 10) # Cabeçalhos em negrito
    col_widths = [25, 60, 35, 25, 30] # Ajustado largura das colunas para caber melhor
    headers = ["Data", "Descrição", "Categoria", "Tipo", "Valor"]

    # Adiciona cabeçalhos da tabela
    for i, header in enumerate(headers):
        # pdf.cell(col_widths[i], 10, header.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C', fill=False) # Original encoding
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C', fill=False) # fpdf2
    pdf.ln()

    pdf.set_font(font_for_text, '', 10) # Dados da tabela em fonte normal
    for lancamento in lancamentos_list:
        try:
            data_formatada = datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            data_formatada = lancamento.get("Data", "Data Inválida")

        descricao = lancamento.get("Descrição", "")
        categoria = lancamento.get("Categorias", "") if lancamento.get("Categorias") else "Sem Categoria" # Usa "Sem Categoria" se vazio
        tipo = lancamento.get("Tipo de Lançamento", "")
        valor_formatado = f"R$ {lancamento.get('Valor', 0.0):.2f}".replace('.', ',')

        # Adiciona células da tabela
        # pdf.cell(col_widths[0], 10, data_formatada.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C') # Original encoding
        # pdf.cell(col_widths[1], 10, descricao.encode('latin1', 'replace').decode('latin1'), 1, 0, 'L')
        # pdf.cell(col_widths[2], 10, categoria.encode('latin1', 'replace').decode('latin1') if categoria else "", 1, 0, 'C')
        # pdf.cell(col_widths[3], 10, tipo.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        # pdf.cell(col_widths[4], 10, valor_formatado.encode('latin1', 'replace').decode('latin1'), 1, 0, 'R')

        # Usando fpdf2 sem encoding 'latin1' manual
        pdf.cell(col_widths[0], 10, data_formatada, 1, 0, 'C')
        # MultiCell para descrição caso seja longa
        # Calcular altura necessária para a célula da descrição
        desc_height = pdf.get_string_width(descricao) / (col_widths[1] - 2) * pdf.font_size # Aproximação simples
        desc_height = max(desc_height, 1) * pdf.font_size * 0.35 # Ajuste para altura da linha
        row_height = max(10, desc_height + 4) # Altura mínima 10, mas ajusta se descrição for longa

        x = pdf.get_x()
        y = pdf.get_y()
        pdf.multi_cell(col_widths[1], 10, descricao, 1, 'L', fill=False) # MultiCell for description
        pdf.set_xy(x + col_widths[1], y) # Move cursor back after MultiCell


        pdf.cell(col_widths[2], 10, categoria, 1, 0, 'C')
        pdf.cell(col_widths[3], 10, tipo, 1, 0, 'C')
        pdf.cell(col_widths[4], 10, valor_formatado, 1, 0, 'R')

        pdf.ln() # New line after each row

    pdf_output = pdf.output(dest='S')
    return io.BytesIO(pdf_output)


# --- FUNÇÃO para gerar a Demonstração de Resultados em PDF ---
def gerar_demonstracao_resultados_pdf(lancamentos_list, usuario_nome="Usuário"):
    pdf = FPDF() # Usando fpdf2
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos. Se não encontrar, usa Arial padrão.
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
    # pdf.cell(0, 10, report_title.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C') # Original encoding
    pdf.cell(0, 10, report_title, 0, 1, 'C') # fpdf2
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
    # pdf.cell(0, 10, "Receitas".encode('latin1', 'replace').decode('latin1'), 0, 1, 'L') # Original encoding
    pdf.cell(0, 10, "Receitas", 0, 1, 'L') # fpdf2
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10) # Conteúdo da seção em fonte normal
    # Ordenar categorias de receita alfabeticamente para consistência
    for categoria in sorted(receitas_por_categoria.keys()):
        valor = receitas_por_categoria[categoria]
        # Garante alinhamento com duas células: categoria à esquerda, valor à direita
        # pdf.cell(100, 7, f"- {categoria}".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L') # Original encoding
        # pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R') # Original encoding
        pdf.cell(100, 7, f"- {categoria}", 0, 0, 'L') # fpdf2
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ','), 0, 1, 'R') # fpdf2

    pdf.set_font(font_for_text, 'B', 10) # Total em negrito
    # pdf.cell(100, 7, "Total Receitas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L') # Original encoding
    # pdf.cell(0, 7, f"R$ {total_receitas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R') # Original encoding
    pdf.cell(100, 7, "Total Receitas", 0, 0, 'L') # fpdf2
    pdf.cell(0, 7, f"R$ {total_receitas:.2f}".replace('.', ','), 0, 1, 'R') # fpdf2
    pdf.ln(10) # Espaço após a seção de Receitas

    # --- Adicionar Despesas ao PDF ---
    pdf.set_font(font_for_text, 'B', 12) # Título da seção em negrito
    # pdf.cell(0, 10, "Despesas".encode('latin1', 'replace').decode('latin1'), 0, 1, 'L') # Original encoding
    pdf.cell(0, 10, "Despesas", 0, 1, 'L') # fpdf2
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10) # Conteúdo da seção em fonte normal
     # Ordenar categorias de despesa alfabeticamente
    for categoria in sorted(despesas_por_categoria.keys()):
        valor = despesas_por_categoria[categoria]
        # pdf.cell(100, 7, f"- {categoria}".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L') # Original encoding
        # pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R') # Original encoding
        pdf.cell(100, 7, f"- {categoria}", 0, 0, 'L') # fpdf2
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ','), 0, 1, 'R') # fpdf2

    pdf.set_font(font_for_text, 'B', 10) # Total em negrito
    # pdf.cell(100, 7, "Total Despesas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L') # Original encoding
    # pdf.cell(0, 7, f"R$ {total_despesas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R') # Original encoding
    pdf.cell(100, 7, "Total Despesas", 0, 0, 'L') # fpdf2
    pdf.cell(0, 7, f"R$ {total_despesas:.2f}".replace('.', ','), 0, 1, 'R') # fpdf2
    pdf.ln(10) # Espaço após a seção de Despesas

    # --- Adicionar Resultado Líquido ---
    resultado_liquido = total_receitas - total_despesas
    pdf.set_font(font_for_text, 'B', 12) # Resultado em negrito

    # Cor do resultado líquido: Azul para positivo, Vermelho para negativo
    if resultado_liquido >= 0:
        pdf.set_text_color(0, 0, 255) # Azul para lucro
    else:
        pdf.set_text_color(255, 0, 0) # Vermelho para prejuízo

    # pdf.cell(100, 10, "Resultado Líquido".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L') # Original encoding
    # pdf.cell(0, 10, f"R$ {resultado_liquido:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R') # Original encoding
    pdf.cell(100, 10, "Resultado Líquido", 0, 0, 'L') # fpdf2
    pdf.cell(0, 10, f"R$ {resultado_liquido:.2f}".replace('.', ','), 0, 1, 'R') # fpdf2

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
        # Nome do arquivo sem acentos ou espaços
        filename_suffix = st.session_state.get('usuario_atual_nome', 'usuario').replace(" ", "_").lower()
        # Tenta remover acentos e caracteres especiais para o nome do arquivo
        import unicodedata
        filename_suffix = ''.join(c for c in unicodedata.normalize('NFD', filename_suffix) if unicodedata.category(c) != 'Mn')
        filename_suffix = ''.join(e for e in filename_suffix if e.isalnum() or e == '_')


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
         # Botão para a nova função de exportação (Demonstração de Resultados)
         pdf_dr_buffer = gerar_demonstracao_resultados_pdf(lancamentos_para_exibir, usuario_para_pdf_title)
         st.download_button(
            label="📊 Exportar DR PDF",
            data=pdf_dr_buffer,
            file_name=f'demonstracao_resultados_{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
         )

    st.markdown("---")

    # --- Exibir Tabela de Lançamentos ---
    st.subheader("Tabela de Lançamentos")

    # Cria um DataFrame para exibição (removendo 'user_email')
    lancamentos_para_df_tabela = []
    for lancamento in lancamentos_para_exibir:
        lancamento_copy = lancamento.copy()
        # Não remove 'user_email' aqui se você quiser exibir quem fez o lançamento (útil para admin)
        # Mas para a visualização normal do cliente, pode ser removido
        if st.session_state.get('tipo_usuario_atual') != 'Administrador' and 'user_email' in lancamento_copy:
             del lancamento_copy['user_email'] # Remove user_email para clientes
        lancamentos_para_df_tabela.append(lancamento_copy)

    df_tabela = pd.DataFrame(lancamentos_para_df_tabela)

    if not df_tabela.empty:
        # Formatar colunas para exibição na tabela Streamlit
        if 'Data' in df_tabela.columns:
             try:
                 df_tabela['Data'] = pd.to_datetime(df_tabela['Data']).dt.strftime('%d/%m/%Y')
             except Exception:
                 pass # Ignora erro de formatação na tabela de exibição

        if 'Valor' in df_tabela.columns:
             try:
                 df_tabela['Valor'] = df_tabela['Valor'].apply(lambda x: f"R$ {x:.2f}".replace('.', ','))
             except Exception:
                 pass # Ignora erro de formatação na tabela de exibição


        # Reordenar colunas para melhor visualização se 'user_email' estiver presente
        cols = df_tabela.columns.tolist()
        if 'user_email' in cols:
            # Move user_email para o final
            cols.remove('user_email')
            cols.append('user_email')
            df_tabela = df_tabela[cols]


        # Adicionar colunas de Ação (Editar e Excluir)
        df_tabela['Ações'] = ""

        # Exibe a tabela interativa
        # Utiliza key para evitar problemas de re-renderização com ações
        edited_df = st.data_editor(
            df_tabela,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ações": st.column_config.Column(
                    "Ações",
                    width="medium"
                )
            },
            key=f"lancamentos_editor_{filename_suffix}" # Chave única para o data_editor
        )

        # Capturar as ações dos botões dentro do data_editor é mais complexo.
        # Uma abordagem comum é ter botões separados para cada linha APÓS o data_editor,
        # ou usar st.column_config.Button, mas isso não permite múltiplos botões por célula diretamente.
        # Vamos manter a abordagem original de botões separados abaixo da tabela ou usar um modal/popup.

        # Implementando os botões de Ação ao lado de cada linha da tabela
        # Isso exige iterar sobre os lançamentos originais (filtrados) e renderizar Streamlit elements.
        # Isso substitui a coluna "Ações" no data_editor por botões reais abaixo.

        st.markdown("---")
        st.subheader("Ações nos Lançamentos")

        # Cria colunas para os botões Ação (correspondendo às colunas da tabela visualmente)
        # Ajustar larguras para alinhar com a tabela acima
        col_widths_actions = [25, 60, 35, 25, 30, 30] # Adiciona espaço para os botões (total 190 + 10 margem)
        cols_actions = st.columns(col_widths_actions)

        # Cabeçalhos das colunas de ação para alinhamento visual (opcional)
        # for i, header in enumerate(["Data", "Descrição", "Categoria", "Tipo", "Valor", "Ações"]):
        #      cols_actions[i].write(f"**{header}**") # Pode ficar visualmente confuso, omitindo por enquanto

        for i, lancamento in enumerate(lancamentos_para_exibir):
            # Encontra o índice original na lista completa de lançamentos (necessário para exclusão/edição)
            try:
                original_index = st.session_state.get('lancamentos', []).index(lancamento)
            except ValueError:
                continue # Pula se o lançamento não for encontrado (nunca deveria acontecer aqui)

            # Exibe os dados do lançamento (opcional, para alinhamento visual)
            # cols_actions[0].write(datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y"))
            # cols_actions[1].write(lancamento.get("Descrição", ""))
            # cols_actions[2].write(lancamento.get("Categorias", ""))
            # cols_actions[3].write(lancamento.get("Tipo de Lançamento", ""))
            # cols_actions[4].write(f"R$ {lancamento.get('Valor', 0.0):.2f}".replace('.', ','))

            # Botões de Ação na última coluna
            # Usar chaves únicas para cada botão
            col_editar, col_excluir = cols_actions[-1].columns(2) # Divide a última coluna para 2 botões menores

            # Verifica permissão para editar/excluir
            is_owner = lancamento.get('user_email') == st.session_state.get('usuario_atual_email')
            is_admin = st.session_state.get('tipo_usuario_atual') == 'Administrador'

            if is_owner or is_admin:
                # Botão Editar
                if col_editar.button("✏️", key=f"edit_lancamento_{original_index}", help="Editar Lançamento"):
                    # Salva o índice e os dados do lançamento no estado para exibir o formulário de edição
                    st.session_state['editar_indice'] = original_index
                    st.session_state['editar_lancamento'] = st.session_state.get("lancamentos", [])[original_index] # Salva uma cópia dos dados atuais
                    st.session_state['show_edit_modal'] = True
                    st.session_state['show_add_modal'] = False # Fecha modal de adicionar se aberto
                    st.rerun() # Força a re-renderização para mostrar o formulário de edição

                # Botão Excluir
                # Adiciona uma confirmação simples
                # if col_excluir.button("🗑️", key=f"delete_lancamento_{original_index}", help="Excluir Lançamento", type="secondary"):
                #     # Exclui o lançamento da lista e salva
                #     st.session_state["lancamentos"].pop(original_index)
                #     salvar_lancamentos()
                #     st.success("Lançamento excluído com sucesso!")
                #     st.rerun() # Força a re-renderização

                # Implementação de exclusão com confirmação via modal/popup
                if col_excluir.button("🗑️", key=f"confirm_delete_lancamento_{original_index}", help="Excluir Lançamento", type="secondary"):
                    # Salva o índice do item a ser excluído e exibe o modal de confirmação
                    st.session_state['confirm_delete_index'] = original_index
                    st.session_state['show_confirm_delete_modal'] = True
                    st.rerun() # Força re-renderização para mostrar o modal

        # --- Modal de Confirmação de Exclusão (Lançamento) ---
        if st.session_state.get('show_confirm_delete_modal', False):
             with st.expander("Confirmar Exclusão", expanded=True):
                 delete_index = st.session_state.get('confirm_delete_index')
                 if delete_index is not None and delete_index < len(st.session_state.get('lancamentos', [])):
                     lancamento_para_deletar = st.session_state['lancamentos'][delete_index]
                     st.warning(f"Tem certeza que deseja excluir o lançamento: '{lancamento_para_deletar.get('Descrição', 'Sem Descrição')}' de {f'R$ {lancamento_para_deletar.get('Valor', 0.0):.2f}'.replace('.', ',')}?")
                     col_confirm_del, col_cancel_del = st.columns(2)
                     if col_confirm_del.button("Sim, Excluir", key="confirm_delete_yes", type="secondary"):
                         st.session_state["lancamentos"].pop(delete_index)
                         salvar_lancamentos()
                         st.success("Lançamento excluído com sucesso!")
                         st.session_state['show_confirm_delete_modal'] = False
                         st.session_state['confirm_delete_index'] = None
                         st.rerun() # Força a re-renderização
                     if col_cancel_del.button("Não, Cancelar", key="confirm_delete_no"):
                         st.session_state['show_confirm_delete_modal'] = False
                         st.session_state['confirm_delete_index'] = None
                         st.rerun() # Força a re-renderização
                 else:
                     st.error("Erro: Lançamento a ser excluído não encontrado.")
                     st.session_state['show_confirm_delete_modal'] = False
                     st.session_state['confirm_delete_index'] = None


def exibir_usuarios():
    if st.session_state.get('tipo_usuario_atual') != 'Administrador':
        st.warning("Acesso negado. Somente administradores podem gerenciar usuários.")
        return

    st.subheader("Gerenciar Usuários")

    # Formulário para Adicionar Novo Usuário (agora no expander)
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
                    # Verificar se o email já existe
                    emails_existentes = [u.get('Email') for u in st.session_state.get('usuarios', [])]
                    if novo_email in emails_existentes:
                        st.error(f"O e-mail '{novo_email}' já está cadastrado.")
                    else:
                        novo_usuario_data = {
                            "Nome": novo_nome,
                            "Email": novo_email,
                            "Senha": nova_senha, # **Aviso: Senha em texto plano!**
                            "Tipo": novo_tipo,
                            "categorias_receita": CATEGORIAS_PADRAO_RECEITA.copy() # Adiciona categorias padrão para novos usuários
                            # Você pode adicionar mais chaves aqui conforme necessário
                        }
                        st.session_state['usuarios'].append(novo_usuario_data)
                        salvar_usuarios()
                        st.success(f"Usuário '{novo_nome}' adicionado com sucesso!")
                        st.rerun() # Recarrega a página para mostrar o novo usuário na lista

    st.markdown("---")
    st.subheader("Lista de Usuários")

    # Exibe a tabela de usuários
    usuarios_para_df = []
    for user in st.session_state.get('usuarios', []):
        # Cria uma cópia e remove a senha para não exibir na tabela
        user_copy = user.copy()
        if 'Senha' in user_copy:
            user_copy['Senha'] = '********' # Esconde a senha
        # Remove categorias_receita da exibição da tabela principal
        if 'categorias_receita' in user_copy:
             del user_copy['categorias_receita']
        usuarios_para_df.append(user_copy)

    df_usuarios = pd.DataFrame(usuarios_para_df)

    if df_usuarios.empty:
        st.info("Nenhum usuário cadastrado (além dos iniciais, se o arquivo estava vazio).")
    else:
        # Adicionar colunas de Ação (Editar e Excluir)
        df_usuarios['Ações'] = ""

        # Exibe a tabela interativa de usuários
        # Apenas administradores podem editar/excluir
        edited_df_users = st.data_editor(
            df_usuarios,
            use_container_width=True,
            hide_index=True,
            column_config={
                 # Oculta o ID interno da tabela, se houver
                # "index": None, # Isso não funciona para o índice do DataFrame se ele não for nomeado
                "Ações": st.column_config.Column(
                    "Ações",
                    width="medium"
                ),
                 # Permite editar o Tipo e Nome diretamente na tabela? Talvez sim.
                "Nome": st.column_config.TextColumn("Nome", disabled=False),
                "Email": st.column_config.TextColumn("Email", disabled=True), # Email não deve ser editável diretamente aqui
                "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Cliente", "Administrador"], disabled=False),
                "Senha": st.column_config.TextColumn("Senha", disabled=True), # Senha não deve ser editável diretamente aqui (mostra ****)

            },
             # Desabilita edição para não-admins
            disabled=st.session_state.get('tipo_usuario_atual') != 'Administrador',
            key="usuarios_editor" # Chave única para o data_editor de usuários
        )

        # Detectar mudanças no data_editor (edição inline de Nome/Tipo)
        # Streamlit não fornece um callback direto para edição no data_editor.
        # É comum comparar o DataFrame original com o edited_df_users após cada rerun.
        # No entanto, a forma mais robusta de lidar com edição de usuários é via formulário (modal/expander)
        # e exclusão via botão, pois a senha não pode ser editada inline de forma segura.
        # Vamos focar em adicionar os botões de Ação (Editar e Excluir) separadamente abaixo da tabela.

        st.markdown("---")
        st.subheader("Ações nos Usuários")

        # Cria colunas para os botões Ação (correspondendo às colunas da tabela visualmente)
        # Ajustar larguras para alinhar com a tabela acima
        # Lembre-se de que o DF exibido não tem 'categorias_receita' e a senha está mascarada.
        # Use as colunas relevantes: Nome, Email, Senha(masked), Tipo, Ações
        # Larguras aproximadas: Nome(50), Email(60), Senha(30), Tipo(30), Ações(30)
        col_widths_user_actions = [50, 60, 30, 30, 30] # Total 200
        cols_user_actions = st.columns(col_widths_user_actions)


        # Iterar sobre a lista original de usuários (st.session_state['usuarios']) para obter os índices corretos
        for i, usuario in enumerate(st.session_state.get('usuarios', [])):
             # Opcional: Exibir os dados do usuário para alinhamento visual com os botões
             # cols_user_actions[0].write(usuario.get("Nome", ""))
             # cols_user_actions[1].write(usuario.get("Email", ""))
             # cols_user_actions[2].write("********") # Mostra a senha mascarada
             # cols_user_actions[3].write(usuario.get("Tipo", ""))


             # Botões de Ação na última coluna
             col_editar_user, col_excluir_user = cols_user_actions[-1].columns(2) # Divide a última coluna

             # Botão Editar Usuário
             if col_editar_user.button("✏️", key=f"edit_usuario_{i}", help="Editar Usuário"):
                 # Salva o índice e os dados do usuário no estado para exibir o formulário de edição
                 st.session_state['editar_usuario_index'] = i
                 st.session_state['editar_usuario_data'] = st.session_state['usuarios'][i].copy() # Salva uma cópia dos dados atuais
                 st.session_state['show_edit_user_modal'] = True # Flag para exibir o modal/expander de edição
                 st.session_state['show_confirm_delete_user_modal'] = False # Fecha outros modais
                 st.rerun() # Força a re-renderização

             # Botão Excluir Usuário
             # Adicionar modal de confirmação
             if col_excluir_user.button("🗑️", key=f"confirm_delete_usuario_{i}", help="Excluir Usuário", type="secondary"):
                  # Salva o índice do usuário a ser excluído e exibe o modal de confirmação
                  st.session_state['confirm_delete_user_index'] = i
                  st.session_state['show_confirm_delete_user_modal'] = True
                  st.session_state['show_edit_user_modal'] = False # Fecha outros modais
                  st.rerun() # Força re-renderização para mostrar o modal

        # --- Modal de Edição de Usuário ---
        if st.session_state.get('show_edit_user_modal', False):
             editar_index = st.session_state.get('editar_usuario_index')
             usuario_data = st.session_state.get('editar_usuario_data')

             if editar_index is not None and usuario_data:
                  with st.expander("Editar Usuário", expanded=True):
                       st.subheader(f"Editar Usuário: {usuario_data.get('Nome', 'Nome Desconhecido')}")
                       with st.form(key=f"edit_usuario_form_{editar_index}"):
                            # Exibe o Email, mas desabilitado
                            st.text_input("E-mail (Não Editável)", value=usuario_data.get('Email', ''), disabled=True, key=f"edit_user_email_disabled_{editar_index}")

                            edited_nome = st.text_input("Nome", value=usuario_data.get('Nome', ''), key=f"edit_user_nome_{editar_index}")
                            # Edição de Senha deve ser separada ou com confirmação forte
                            # Por simplicidade, vamos adicionar um campo de senha opcional aqui.
                            # Se o campo for deixado em branco, a senha não é alterada.
                            # Se for preenchido, a senha é atualizada (ainda em texto plano, AVISO!).
                            edited_senha = st.text_input("Nova Senha (Deixe em branco para não alterar)", type="password", key=f"edit_user_senha_{editar_index}")

                            tipo_options = ["Cliente", "Administrador"]
                            try:
                                default_tipo_index = tipo_options.index(usuario_data.get('Tipo', 'Cliente'))
                            except ValueError:
                                default_tipo_index = 0

                            edited_tipo = st.selectbox("Tipo", tipo_options, index=default_tipo_index, key=f"edit_user_tipo_{editar_index}")

                            # --- Edição de Categorias de Receita do Usuário ---
                            st.markdown("#### Categorias de Receita (exclusivas deste usuário)")
                            # Usa o multiselect com as categorias salvas para este usuário + categorias padrão
                            categorias_atuais_usuario = usuario_data.get('categorias_receita', [])
                            # Combina categorias atuais com padrão para mostrar no multiselect
                            todas_disponiveis_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + categorias_atuais_usuario))
                            selected_categorias_receita = st.multiselect(
                                "Selecione as categorias de Receita para este usuário:",
                                todas_disponiveis_receita,
                                default=categorias_atuais_usuario, # Pre-seleciona as salvas
                                key=f"edit_user_categorias_receita_{editar_index}"
                            )

                            # Opção para adicionar uma nova categoria diretamente aqui
                            nova_categoria_input = st.text_input("Adicionar nova categoria de receita:", key=f"new_cat_input_{editar_index}")
                            add_categoria_button = st.button("Adicionar esta categoria à lista", key=f"add_new_cat_button_{editar_index}")

                            if add_categoria_button and nova_categoria_input:
                                 nova_categoria_input_stripped = nova_categoria_input.strip()
                                 if nova_categoria_input_stripped and nova_categoria_input_stripped not in todas_disponiveis_receita:
                                      # Adiciona a nova categoria tanto na lista de seleção quanto na lista do usuário no estado temporário
                                      todas_disponiveis_receita.append(nova_categoria_input_stripped)
                                      selected_categorias_receita.append(nova_categoria_input_stripped)
                                      st.session_state['editar_usuario_data']['categorias_receita'] = selected_categorias_receita # Atualiza no estado temp
                                      st.success(f"Categoria '{nova_categoria_input_stripped}' adicionada para este usuário. Salve para confirmar.")
                                      st.rerun() # Rerender para atualizar o multiselect


                            submit_edit_usuario_button = st.form_submit_button("Salvar Alterações do Usuário")

                            if submit_edit_usuario_button:
                                if not edited_nome or not edited_tipo:
                                    st.warning("Nome e Tipo são obrigatórios.")
                                else:
                                     # Encontra o índice real do usuário na lista principal novamente para garantir
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
                                             # Não salva as alterações
                                             st.session_state['show_edit_user_modal'] = False
                                             st.session_state['editar_usuario_index'] = None
                                             st.session_state['editar_usuario_data'] = None
                                             st.rerun()
                                             return


                                     # Atualiza os dados do usuário na lista principal
                                     st.session_state['usuarios'][real_index]['Nome'] = edited_nome
                                     st.session_state['usuarios'][real_index]['Tipo'] = edited_tipo
                                     # Atualiza a senha APENAS se uma nova senha foi fornecida
                                     if edited_senha:
                                          st.session_state['usuarios'][real_index]['Senha'] = edited_senha # **Aviso: Senha em texto plano!**
                                     # Atualiza as categorias de receita
                                     st.session_state['usuarios'][real_index]['categorias_receita'] = selected_categorias_receita


                                     salvar_usuarios()
                                     st.success("Dados do usuário atualizados com sucesso!")
                                     # Limpa as variáveis de estado de edição para fechar o formulário
                                     st.session_state['show_edit_user_modal'] = False
                                     st.session_state['editar_usuario_index'] = None
                                     st.session_state['editar_usuario_data'] = None
                                     # Se o usuário logado editou seu próprio tipo ou nome, atualiza as variáveis de sessão
                                     if real_index == st.session_state.get('usuario_atual_index'):
                                         st.session_state['usuario_atual_nome'] = edited_nome
                                         st.session_state['tipo_usuario_atual'] = edited_tipo
                                         # As categorias de receita já foram atualizadas acima
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
             if delete_index is not None and delete_index < len(st.session_state.get('usuarios', [])):
                 usuario_para_deletar = st.session_state['usuarios'][delete_index]
                 st.warning(f"Tem certeza que deseja excluir o usuário: '{usuario_para_deletar.get('Nome', 'Nome Desconhecido')}' ({usuario_para_deletar.get('Email', 'Email Desconhecido')})?")

                 # Adicionar a validação para não excluir o último administrador AQUI TAMBÉM
                 admins_count = len([u for u in st.session_state.get('usuarios', []) if u.get('Tipo') == 'Administrador'])
                 if usuario_para_deletar.get('Tipo') == 'Administrador' and admins_count == 1:
                     st.error("Não é possível excluir o último usuário administrador.")
                     if st.button("Fechar", key="cancel_delete_user_last_admin"):
                         st.session_state['show_confirm_delete_user_modal'] = False
                         st.session_state['confirm_delete_user_index'] = None
                         st.rerun()
                     return # Sai da função para não mostrar os botões de confirmação

                 col_confirm_del_user, col_cancel_del_user = st.columns(2)
                 if col_confirm_del_user.button("Sim, Excluir Usuário", key="confirm_delete_user_yes", type="secondary"):
                     # Exclui o usuário
                     st.session_state['usuarios'].pop(delete_index)
                     salvar_usuarios()
                     st.success("Usuário excluído com sucesso!")
                     st.session_state['show_confirm_delete_user_modal'] = False
                     st.session_state['confirm_delete_user_index'] = None
                     # Se o usuário logado for o excluído (altamente improvável por UI, mas seguro verificar), desautentica
                     if delete_index == st.session_state.get('usuario_atual_index'):
                          st.session_state['autenticado'] = False
                          st.session_state['usuario_atual_email'] = None
                          st.session_state['usuario_atual_nome'] = None
                          st.session_state['tipo_usuario_atual'] = None
                          st.session_state['usuario_atual_index'] = None
                          st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy() # Reseta categorias
                     st.rerun() # Força a re-renderização
                 if col_cancel_del_user.button("Não, Cancelar", key="confirm_delete_user_no"):
                     st.session_state['show_confirm_delete_user_modal'] = False
                     st.session_state['confirm_delete_user_index'] = None
                     st.rerun() # Força a re-renderização
             else:
                 st.error("Erro: Usuário a ser excluído não encontrado.")
                 st.session_state['show_confirm_delete_user_modal'] = False
                 st.session_state['confirm_delete_user_index'] = None


def gerenciar_categorias():
     if st.session_state.get('tipo_usuario_atual') != 'Administrador':
        st.warning("Acesso negado. Somente administradores podem gerenciar categorias padrão.")
        return

     st.subheader("Gerenciar Categorias Padrão de Receita")
     st.info("Estas categorias aparecem para todos os novos usuários e como base para todos os usuários.")

     # Exibe as categorias padrão atuais
     st.write("Categorias Padrão Atuais:", CATEGORIAS_PADRAO_RECEITA)

     # Formulário para adicionar nova categoria padrão
     with st.form("add_categoria_padrao_form"):
          nova_cat_padrao = st.text_input("Nova Categoria Padrão de Receita:")
          add_cat_padrao_button = st.form_submit_button("Adicionar Categoria Padrão")

          if add_cat_padrao_button and nova_cat_padrao:
               nova_cat_padrao_stripped = nova_cat_padrao.strip()
               if nova_cat_padrao_stripped and nova_cat_padrao_stripped not in CATEGORIAS_PADRAO_RECEITA:
                    # Como CATEGORIAS_PADRAO_RECEITA é uma constante global, não podemos modificá-la diretamente.
                    # O melhor seria carregar/salvar categorias padrão de um arquivo também, ou gerenciar
                    # apenas as categorias POR USUÁRIO.
                    # Dado que CATEGORIAS_PADRAO_RECEITA é uma constante, adicionar via UI não faz sentido a menos que a tornemos mutável
                    # e salvemos em algum lugar.
                    # Por agora, vamos apenas avisar que não pode adicionar se for uma constante.
                    st.warning("As categorias padrão são fixas no código. Esta funcionalidade de adicionar via UI não está implementada para categorias padrão.")
                    # st.session_state['categorias_padrao_mutavel'].append(nova_cat_padrao_stripped) # Exemplo se fosse mutável
                    # salvar_categorias_padrao() # Exemplo se fosse salvo em arquivo
                    # st.rerun()
               elif nova_cat_padrao_stripped in CATEGORIAS_PADRAO_RECEITA:
                    st.info(f"A categoria '{nova_cat_padrao_stripped}' já existe nas categorias padrão.")


     st.markdown("---")

     st.subheader("Gerenciar Categorias por Usuário")
     st.info("Cada usuário pode ter categorias de receita personalizadas.")

     # Seleciona o usuário para gerenciar categorias
     user_emails = [u.get('Email') for u in st.session_state.get('usuarios', [])]
     selected_user_email = st.selectbox("Selecione o usuário para gerenciar categorias:", user_emails, key="select_user_for_categories")

     if selected_user_email:
          # Encontra o usuário selecionado
          user_index_for_cat = next((i for i, u in enumerate(st.session_state.get('usuarios', [])) if u.get('Email') == selected_user_email), None)

          if user_index_for_cat is not None:
               user = st.session_state['usuarios'][user_index_for_cat]
               st.write(f"Categorias de Receita para {user.get('Nome', 'Usuário Desconhecido')}:")

               categorias_atuais = user.get('categorias_receita', [])
               # Combina as categorias do usuário com as padrão para mostrar todas as opções relevantes
               todas_opcoes_cat = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + categorias_atuais))


               with st.form(key=f"edit_user_categories_form_{user_index_for_cat}"):
                    # Permite multi-selecionar as categorias
                    edited_categorias = st.multiselect(
                        "Selecione as categorias de Receita:",
                        todas_opcoes_cat, # Opções incluem padrão + atuais do usuário
                        default=categorias_atuais, # Pré-seleciona as que o usuário já tem
                        key=f"multiselect_user_cats_{user_index_for_cat}"
                    )

                    # Opção para adicionar uma nova categoria específica para este usuário
                    nova_categoria_usuario_input = st.text_input("Adicionar nova categoria para este usuário:", key=f"new_cat_user_input_{user_index_for_cat}")
                    add_cat_usuario_button = st.form_submit_button("Adicionar Categoria (apenas para este usuário)")

                    if add_cat_usuario_button and nova_categoria_usuario_input:
                         nova_categoria_usuario_stripped = nova_categoria_usuario_input.strip()
                         if nova_categoria_usuario_stripped and nova_categoria_usuario_stripped not in edited_categorias:
                              # Adiciona a nova categoria à lista de seleção e à lista do usuário (temporariamente no formulário)
                              edited_categorias.append(nova_categoria_usuario_stripped)
                              st.success(f"Categoria '{nova_categoria_usuario_stripped}' adicionada à seleção. Salve para confirmar.")
                              # Force re-render para atualizar o multiselect? Streamlit forms são tricky.
                              # Uma rerender fora do form pode ser necessária.
                              # st.session_state[f"multiselect_user_cats_{user_index_for_cat}"] = edited_categorias # Tenta atualizar o state key
                              # st.rerun() # Rerender para refletir a nova opção


                    # Botão para Salvar as categorias selecionadas para este usuário
                    save_user_categories_button = st.form_submit_button("Salvar Categorias para este Usuário")

                    if save_user_categories_button:
                         # Atualiza a lista de categorias de receita para o usuário selecionado
                         st.session_state['usuarios'][user_index_for_cat]['categorias_receita'] = edited_categorias
                         salvar_usuarios()
                         st.success(f"Categorias de receita para '{user.get('Nome')}' salvas com sucesso!")
                         # Se o usuário logado for o que teve as categorias editadas, atualiza suas categorias no session state
                         if user_index_for_cat == st.session_state.get('usuario_atual_index'):
                              usuario_categorias_receita = st.session_state['usuarios'][user_index_for_cat].get('categorias_receita', [])
                              todas_unicas_receita = list(dict.fromkeys(CATEGORIAS_PADRAO_RECEITA + usuario_categorias_receita))
                              st.session_state['todas_categorias_receita'] = todas_unicas_receita
                         st.rerun() # Recarrega para refletir as mudanças



# --- Layout Principal ---
def main():
    st.sidebar.title("Navegação")

    if not st.session_state.get('autenticado'):
        pagina_login()
    else:
        # Adiciona o nome do usuário logado na sidebar
        st.sidebar.write(f"Bem-vindo(a), **{st.session_state.get('usuario_atual_nome', 'Usuário')}**!")
        # Adiciona o tipo de usuário logado na sidebar
        st.sidebar.write(f"Tipo: **{st.session_state.get('tipo_usuario_atual', 'Cliente')}**")


        if st.sidebar.button("Dashboard", key="nav_dashboard"):
            st.session_state['pagina_atual'] = 'dashboard'
            st.session_state['show_add_modal'] = False
            st.session_state['show_edit_modal'] = False
            st.session_state['show_edit_user_modal'] = False
            st.session_state['show_confirm_delete_user_modal'] = False
            st.session_state['show_confirm_delete_modal'] = False
            st.rerun()
        if st.sidebar.button("Lançamentos", key="nav_lancamentos"):
            st.session_state['pagina_atual'] = 'lancamentos'
            st.session_state['show_add_modal'] = False
            st.session_state['show_edit_modal'] = False
            st.session_state['show_edit_user_modal'] = False
            st.session_state['show_confirm_delete_user_modal'] = False
            st.session_state['show_confirm_delete_modal'] = False
            st.rerun()

        # Apenas administradores veem a página de usuários e categorias
        if st.session_state.get('tipo_usuario_atual') == 'Administrador':
            if st.sidebar.button("Gerenciar Usuários", key="nav_usuarios"):
                st.session_state['pagina_atual'] = 'usuarios'
                st.session_state['show_add_modal'] = False
                st.session_state['show_edit_modal'] = False
                st.session_state['show_edit_user_modal'] = False # Garante que o modal de edição de usuário é fechado ao navegar
                st.session_state['show_confirm_delete_user_modal'] = False
                st.session_state['show_confirm_delete_modal'] = False
                st.rerun()
            if st.sidebar.button("Gerenciar Categorias", key="nav_categorias"):
                st.session_state['pagina_atual'] = 'categorias'
                st.session_state['show_add_modal'] = False
                st.session_state['show_edit_modal'] = False
                st.session_state['show_edit_user_modal'] = False
                st.session_state['show_confirm_delete_user_modal'] = False
                st.session_state['show_confirm_delete_modal'] = False
                st.rerun()

        # Botão de Logout
        if st.sidebar.button("Sair", key="nav_logout"):
            st.session_state['autenticado'] = False
            st.session_state['usuario_atual_email'] = None
            st.session_state['usuario_atual_nome'] = None
            st.session_state['tipo_usuario_atual'] = None
            st.session_state['usuario_atual_index'] = None
            st.session_state['pagina_atual'] = 'dashboard' # Volta para o dashboard (que exigirá login)
            st.session_state['show_add_modal'] = False
            st.session_state['show_edit_modal'] = False
            st.session_state['show_edit_user_modal'] = False
            st.session_state['show_confirm_delete_user_modal'] = False
            st.session_state['show_confirm_delete_modal'] = False
            st.session_state['todas_categorias_receita'] = CATEGORIAS_PADRAO_RECEITA.copy() # Reseta categorias visíveis
            st.rerun() # Força re-renderização para mostrar a página de login

        st.sidebar.markdown("---")


        # --- Renderização da Página Principal ---
        if st.session_state.get('pagina_atual') == 'dashboard':
            st.title("Dashboard Financeiro")
            exibir_resumo_central()

            # Adiciona o formulário de adicionar lançamento no dashboard, visível por padrão
            render_add_lancamento_form()

            # Exibe o formulário de edição SE o show_edit_modal for True
            if st.session_state.get('show_edit_modal', False):
                render_edit_lancamento_form()

            # Exibe a lista de lançamentos abaixo dos formulários
            exibir_lancamentos()


        elif st.session_state.get('pagina_atual') == 'lancamentos':
            st.title("Gerenciar Lançamentos")
            # Re-adiciona o formulário de adicionar/editar aqui também se você quiser que esta seja uma página de gerenciamento
            render_add_lancamento_form()
            if st.session_state.get('show_edit_modal', False):
                 render_edit_lancamento_form()

            # Exibe a lista de lançamentos
            exibir_lancamentos()


        elif st.session_state.get('pagina_atual') == 'usuarios':
            st.title("Administração de Usuários")
            exibir_usuarios()

        elif st.session_state.get('pagina_atual') == 'categorias':
             st.title("Administração de Categorias")
             gerenciar_categorias()



if __name__ == "__main__":
    main()
