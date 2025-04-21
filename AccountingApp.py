import streamlit as st
from datetime import datetime
import json
import os
import pandas as pd
import io
from fpdf import FPDF # Certifique-se de ter a biblioteca fpdf2 instalada (pip install fpdf2)

# --- Estilo CSS para os botões ---
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
    /* Estilo para os botões de exclusão (secondary button) */
    div.stButton > button[kind="secondary"] {
        background-color: #e0f2f7; /* Fundo azul claro (ajustado para Streamlit secondary default) */
        color: #003548; /* Texto azul escuro */
        border-color: #b2e2f2; /* Borda azul */
    }
     div.stButton > button[kind="secondary"]:hover {
        background-color: #b2e2f2; /* Fundo azul ao passar o mouse */
        color: #003548;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_FILE = "lancamentos.json"
# USUARIOS_FILE e CATEGORIAS_FILE removidos

# --- Funções de Carregamento e Salvamento ---

# Funções de usuário e categorias removidas

def salvar_lancamentos():
    """Salva a lista de lançamentos no arquivo JSON."""
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.get("lancamentos", []), f, indent=4) # Adicionado indent para legibilidade

def carregar_lancamentos():
    """Carrega a lista de lançamentos do arquivo JSON."""
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
            salvar_lancamentos() # Salva o arquivo vazio após erro
    else:
        st.session_state["lancamentos"] = []
        salvar_lancamentos() # Cria o arquivo vazio se não existir

# --- Inicialização de Estado ---
# Removidos estados de usuário, autenticação e categorias do usuário

# Variáveis de estado para controlar a exibição dos "popups"/form
if 'show_add_modal' not in st.session_state:
    st.session_state['show_add_modal'] = False
if 'show_edit_modal' not in st.session_state:
    st.session_state['show_edit_modal'] = False
if 'editar_indice' not in st.session_state:
     st.session_state['editar_indice'] = None
if 'editar_lancamento' not in st.session_state:
     st.session_state['editar_lancamento'] = None

# Carrega os lançamentos ao iniciar o app
carregar_lancamentos()
if "lancamentos" not in st.session_state:
    st.session_state["lancamentos"] = []

# Define as categorias fixas de Receita
CATEGORIAS_FIXAS_RECEITA = ["Serviços","Vendas"]
# Não há gestão de categorias de Despesa na UI modificada.

# Funções de usuário e login removidas

# --- Funções para Renderizar os Formulários (agora na área principal) ---

def render_add_lancamento_form():
    """Renderiza o formulário para adicionar um novo lançamento."""
    with st.expander("Adicionar Novo Lançamento", expanded=True):
        st.subheader("Adicionar Lançamento") # Título genérico

        with st.form(key="add_lancamento_form"):
            data_str = st.text_input("Data (DD/MM/AAAA)", key="add_lanc_data_form")
            descricao = st.text_input("Descrição", key="add_lanc_descricao_form")
            tipo = st.selectbox("Tipo de Lançamento", ["Receita", "Despesa"], key="add_lanc_tipo_form")

            categoria_placeholder = st.empty()
            categoria = "" # Inicializa a variável de categoria

            if tipo == "Receita":
                categoria = categoria_placeholder.selectbox(
                    "Categoria",
                    CATEGORIAS_FIXAS_RECEITA, # Usa as categorias fixas
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
                            "Categorias": categoria, # Salva a categoria (será vazia se não for Receita)
                            "Tipo de Lançamento": tipo,
                            "Valor": valor,
                            # Campo 'user_email' removido
                        }
                        st.session_state["lancamentos"].append(novo_lancamento)
                        salvar_lancamentos()
                        st.success("Lançamento adicionado com sucesso!")
                        st.session_state['show_add_modal'] = False
                        st.rerun()
                    except ValueError:
                        st.error("Formato de data inválido. Use DD/MM/AAAA.")

        if st.button("Cancelar", key="cancel_add_form_button"):
             st.session_state['show_add_modal'] = False
             st.rerun()


def render_edit_lancamento_form():
    """Renderiza o formulário para editar um lançamento existente."""
    if st.session_state.get('editar_indice') is None:
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

    with st.expander("Editar Lançamento", expanded=True):
        st.subheader("Editar Lançamento") # Título genérico

        with st.form(key=f"edit_lancamento_form_{indice}"):
            lancamento = st.session_state["editar_lancamento"]

            data_str = st.text_input(
                "Data (DD/MM/AAAA)",
                datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y"),
                key=f"edit_lanc_data_form_{indice}"
            )
            descricao = st.text_input("Descrição", lancamento.get("Descrição", ""), key=f"edit_lanc_descricao_form_{indice}")
            tipo = st.selectbox(
                "Tipo de Lançamento",
                ["Receita", "Despesa"],
                index=["Receita", "Despesa"].index(lancamento.get("Tipo de Lançamento", "Receita")),
                key=f"edit_lanc_tipo_form_{indice}",
            )

            categoria_placeholder = st.empty()
            categoria = "" # Inicializa a variável de categoria

            if tipo == "Receita":
                 current_category = lancamento.get("Categorias", "")
                 categorias_disponiveis = CATEGORIAS_FIXAS_RECEITA # Usa as categorias fixas

                 try:
                     default_index = categorias_disponiveis.index(current_category)
                 except ValueError:
                     default_index = 0 # Use a primeira opção se a categoria salva não estiver nas fixas

                 categoria = categoria_placeholder.selectbox(
                    "Categoria",
                    categorias_disponiveis,
                    index=default_index,
                    key=f"edit_lanc_categoria_receita_form_{indice}",
                )

            valor = st.number_input(
                "Valor", value=lancamento.get("Valor", 0.0), format="%.2f", min_value=0.0, key=f"edit_lanc_valor_form_{indice}"
            )

            submit_button = st.form_submit_button("Salvar Edição")

            if submit_button:
                if not data_str or not descricao or valor is None or (tipo == "Receita" and not categoria):
                    st.warning("Por favor, preencha todos os campos obrigatórios.")
                else:
                    try:
                        data_obj = datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                        st.session_state["lancamentos"][indice] = {
                            "Data": data_obj,
                            "Descrição": descricao,
                            "Categorias": categoria, # Salva a categoria (será vazia se não for Receita)
                            "Tipo de Lançamento": tipo,
                            "Valor": valor,
                            # Campo 'user_email' removido
                        }
                        salvar_lancamentos()
                        st.success("Lançamento editado com sucesso!")
                        st.session_state['editar_indice'] = None
                        st.session_state['editar_lancamento'] = None
                        st.session_state['show_edit_modal'] = False
                        st.rerun()
                    except ValueError:
                        st.error("Formato de data inválido. Use DD/MM/AAAA.")

        if st.button("Cancelar Edição", key=f"cancel_edit_form_button_{indice}"):
            st.session_state['editar_indice'] = None
            st.session_state['editar_lancamento'] = None
            st.session_state['show_edit_modal'] = False
            st.rerun()


def exibir_resumo_central():
    """Exibe o resumo financeiro (Receitas, Despesas, Total)."""
    st.subheader("Resumo Financeiro")

    # Exibe todos os lançamentos
    lancamentos_filtrados = st.session_state.get("lancamentos", [])
    st.info("Exibindo resumo de todos os lançamentos.") # Mensagem genérica

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

# Função para exportar lançamentos para Excel
def exportar_lancamentos_para_excel(lancamentos_list):
    """Exporta a lista de lançamentos para um arquivo Excel."""
    lancamentos_para_df = []
    for lancamento in lancamentos_list:
        lancamento_copy = lancamento.copy()
        # Remove campo 'user_email' se existir
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

# Função para exportar lançamentos para PDF (lista detalhada)
def exportar_lancamentos_para_pdf(lancamentos_list):
    """Exporta a lista detalhada de lançamentos para um arquivo PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos.
    try:
        # Verifique se o arquivo da fonte existe ou remova esta seção.
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_table = 'Arial_Unicode'
    except Exception as e:
         pdf.set_font("Arial", '', 12)
         font_for_table = 'Arial'

    pdf.set_font("Arial", 'B', 12)
    report_title = "Relatório Detalhado de Lançamentos" # Título genérico
    pdf.cell(0, 10, report_title.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')
    pdf.ln(10)

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
        pdf.cell(col_widths[2], 10, categoria.encode('latin1', 'replace').decode('latin1') if categoria else "", 1, 0, 'C')
        pdf.cell(col_widths[3], 10, tipo.encode('latin1', 'replace').decode('latin1'), 1, 0, 'C')
        pdf.cell(col_widths[4], 10, valor_formatado.encode('latin1', 'replace').decode('latin1'), 1, 0, 'R')

        pdf.ln()

    pdf_output = pdf.output(dest='S') # Deve retornar bytes

    # --- CORREÇÃO START ---
    # Garante que a saída é bytes antes de criar BytesIO
    if isinstance(pdf_output, str):
        # Codifica a string para bytes usando 'latin-1', que geralmente funciona bem com PDF
        pdf_output_bytes = pdf_output.encode('latin-1')
    else:
        # Se já for bytes, usa diretamente
        pdf_output_bytes = pdf_output

    return io.BytesIO(pdf_output_bytes)
    # --- CORREÇÃO END ---


# --- FUNÇÃO para gerar a Demonstração de Resultados em PDF ---
def gerar_demonstracao_resultados_pdf(lancamentos_list):
    """Gera um PDF da Demonstração de Resultados (DRE)."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta adicionar uma fonte que suporte acentos.
    try:
        # Verifique se o arquivo da fonte existe ou remova esta seção.
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_text = 'Arial_Unicode'
    except Exception as e:
         pdf.set_font("Arial", '', 12)
         font_for_text = 'Arial'


    pdf.set_font(font_for_text, 'B', 14) # Título principal com fonte negrito
    report_title = "Demonstração de Resultados" # Título genérico
    pdf.cell(0, 10, report_title.encode('latin1', 'replace').decode('latin1'), 0, 1, 'C')
    pdf.ln(10)

    # --- Processar dados para a Demonstração de Resultados ---
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

    # --- Adicionar Receitas ao PDF ---
    pdf.set_font(font_for_text, 'B', 12)
    pdf.cell(0, 10, "Receitas".encode('latin1', 'replace').decode('latin1'), 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10)
    for categoria in sorted(receitas_por_categoria.keys()):
        valor = receitas_por_categoria[categoria]
        pdf.cell(100, 7, f"- {categoria}".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10)
    pdf.cell(100, 7, "Total Receitas".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_receitas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')
    pdf.ln(10)

    # --- Adicionar Despesas ao PDF ---
    pdf.set_font(font_for_text, 'B', 12)
    pdf.cell(0, 10, "Despesas".encode('latin1', 'replace').decode('latin1'), 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10)
    for categoria in sorted(despesas_por_categoria.keys()):
        valor = despesas_por_categoria[categoria]
        pdf.cell(100, 7, f"- {categoria}".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10)
    pdf.cell(100, 7, "Total Despesas".encode('latin1', 'replace').replace('.', ',').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_despesas:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')
    pdf.ln(10)

    # --- Adicionar Resultado Líquido ---
    resultado_liquido = total_receitas - total_despesas
    pdf.set_font(font_for_text, 'B', 12)

    if resultado_liquido >= 0:
        pdf.set_text_color(0, 0, 255) # Azul para lucro
    else:
        pdf.set_text_color(255, 0, 0) # Vermelho para prejuízo

    pdf.cell(100, 10, "Resultado Líquido".encode('latin1', 'replace').decode('latin1'), 0, 0, 'L')
    pdf.cell(0, 10, f"R$ {resultado_liquido:.2f}".replace('.', ',').encode('latin1', 'replace').decode('latin1'), 0, 1, 'R')

    pdf.set_text_color(0, 0, 0)

    pdf_output = pdf.output(dest='S') # Deve retornar bytes

    # --- CORREÇÃO START ---
    # Garante que a saída é bytes antes de criar BytesIO
    if isinstance(pdf_output, str):
        # Codifica a string para bytes usando 'latin-1', que geralmente funciona bem com PDF
        pdf_output_bytes = pdf_output.encode('latin-1')
    else:
        # Se já for bytes, usa diretamente
        pdf_output_bytes = pdf_output

    return io.BytesIO(pdf_output_bytes)
    # --- CORREÇÃO END ---


def exibir_lancamentos():
    """Exibe a tabela de lançamentos com opções de edição e exclusão."""
    st.subheader("Lançamentos Registrados") # Título genérico

    # Exibe todos os lançamentos
    lancamentos_para_exibir = st.session_state.get("lancamentos", [])
    st.info("Exibindo todos os lançamentos registrados.") # Mensagem genérica

    if not lancamentos_para_exibir:
        st.info("Nenhum lançamento encontrado.")
        # Exibe os botões de exportação mesmo com lista vazia
        col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1])
        with col_excel:
             excel_buffer = exportar_lancamentos_para_excel([]) # Passa lista vazia
             if excel_buffer:
                st.download_button(
                    label="📥 Exportar para Excel (Vazio)",
                    data=excel_buffer,
                    file_name=f'lancamentos_{datetime.now().strftime("%Y%m%d")}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        with col_pdf_lista:
             pdf_lista_buffer = exportar_lancamentos_para_pdf([]) # Passa lista vazia
             st.download_button(
                label="📄 Exportar Lista PDF (Vazia)",
                data=pdf_lista_buffer,
                file_name=f'lista_lancamentos_{datetime.now().strftime("%Y%m%d")}.pdf',
                mime='application/pdf'
             )
        with col_pdf_dr:
             pdf_dr_buffer = gerar_demonstracao_resultados_pdf([]) # Passa lista vazia
             st.download_button(
                label="📊 Exportar DR PDF (Vazia)",
                data=pdf_dr_buffer,
                file_name=f'demonstracao_resultados_{datetime.now().strftime("%Y%m%d")}.pdf',
                mime='application/pdf'
             )
        st.markdown("---")
        return # Sai da função

    # Ordenar lançamentos por data (do mais recente para o mais antigo)
    try:
        lancamentos_para_exibir.sort(key=lambda x: datetime.strptime(x.get('Data', '1900-01-01'), '%Y-%m-%d'), reverse=True)
    except ValueError:
        st.warning("Não foi possível ordenar os lançamentos por data devido a formato inválido.")

    # --- Botões de Exportação ---
    col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1])

    with col_excel:
        excel_buffer = exportar_lancamentos_para_excel(lancamentos_para_exibir)
        if excel_buffer:
            st.download_button(
                label="📥 Exportar Lançamentos em Excel",
                data=excel_buffer,
                file_name=f'lancamentos_{datetime.now().strftime("%Y%m%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

    with col_pdf_lista:
         pdf_lista_buffer = exportar_lancamentos_para_pdf(lancamentos_para_exibir)
         st.download_button(
            label="📄 Exportar Lista PDF",
            data=pdf_lista_buffer,
            file_name=f'lista_lancamentos_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
         )
    with col_pdf_dr:
         pdf_dr_buffer = gerar_demonstracao_resultados_pdf(lancamentos_para_exibir)
         st.download_button(
            label="📊 Exportar DR PDF",
            data=pdf_dr_buffer,
            file_name=f'demonstracao_resultados_{datetime.now().strftime("%Y%m%d")}.pdf',
            mime='application/pdf'
         )

    st.markdown("---") # Separador

    # --- Exibir Lançamentos em Tabela ---
    dados_para_tabela = []
    for i, lancamento in enumerate(lancamentos_para_exibir):
        lancamento_copy = lancamento.copy()

        try:
            lancamento_copy['Data'] = datetime.strptime(lancamento_copy.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            lancamento_copy['Data'] = lancamento_copy.get("Data", "Data Inválida")

        lancamento_copy['Valor'] = f"R$ {lancamento_copy.get('Valor', 0.0):.2f}".replace('.', ',')

        if 'user_email' in lancamento_copy:
             del lancamento_copy['user_email']

        dados_para_tabela.append(lancamento_copy)

    df_exibicao = pd.DataFrame(dados_para_tabela)

    colunas_exibicao = ["Data", "Descrição", "Categorias", "Tipo de Lançamento", "Valor"]
    colunas_validas = [col for col in colunas_exibicao if col in df_exibicao.columns]
    df_exibicao = df_exibicao[colunas_validas]

    st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Data": st.column_config.TextColumn("Data"),
            "Descrição": st.column_config.TextColumn("Descrição"),
            "Categorias": st.column_config.TextColumn("Categoria"),
            "Tipo de Lançamento": st.column_config.TextColumn("Tipo"),
            "Valor": st.column_config.TextColumn("Valor"),
        }
    )

    # --- Botões de Ação (Editar/Excluir) Abaixo da Tabela ---
    st.subheader("Ações nos Lançamentos")

    num_lancamentos = len(lancamentos_para_exibir)
    if num_lancamentos > 0:
        cols_por_linha = 5 # Ajuste este valor conforme necessário
        num_linhas_botoes = (num_lancamentos + cols_por_linha - 1) // cols_por_linha

        for linha in range(num_linhas_botoes):
             cols_acoes = st.columns(cols_por_linha)
             for i in range(cols_por_linha):
                 idx_global = linha * cols_por_linha + i
                 if idx_global < num_lancamentos:
                     lancamento_original = lancamentos_para_exibir[idx_global]
                     try:
                          indice_original = st.session_state['lancamentos'].index(lancamento_original)
                     except ValueError:
                          continue

                     with cols_acoes[i]:
                        if st.button("Editar", key=f"btn_editar_{indice_original}", help=f"Editar: {lancamento_original.get('Descrição', '')}"):
                            st.session_state['editar_indice'] = indice_original
                            st.session_state['editar_lancamento'] = st.session_state['lancamentos'][indice_original].copy()
                            st.session_state['show_edit_modal'] = True
                            st.session_state['show_add_modal'] = False
                            st.rerun()

                        if st.button("Excluir", key=f"btn_excluir_{indice_original}", help=f"Excluir: {lancamento_original.get('Descrição', '')}", type="secondary"):
                            del st.session_state['lancamentos'][indice_original]
                            salvar_lancamentos()
                            st.success("Lançamento excluído com sucesso!")
                            st.session_state['editar_indice'] = None
                            st.session_state['editar_lancamento'] = None
                            st.rerun()


# --- Layout da Aplicação Principal (Dashboard) ---
def main():
    """Função principal que renderiza o dashboard."""
    st.title("Sistema de Lançamentos Financeiros")

    if st.session_state.get('show_add_modal', False):
         render_add_lancamento_form()
    elif st.session_state.get('show_edit_modal', False):
         render_edit_lancamento_form()
    else:
        if st.button("Adicionar Novo Lançamento"):
             st.session_state['show_add_modal'] = True
             st.session_state['show_edit_modal'] = False
             st.rerun()

        exibir_resumo_central()
        exibir_lancamentos()


# --- Execução da Aplicação ---
if __name__ == "__main__":
    main()
