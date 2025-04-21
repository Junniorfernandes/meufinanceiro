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

    /* Adicionado estilo para ajustar o alinhamento vertical do conteúdo nas colunas */
    /* Isso pode ajudar a alinhar texto e botões se estiverem em colunas na mesma linha */
    div.st எழுது > div {
        vertical-align: middle;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

DATA_FILE = "lancamentos.json"
# USUARIOS_FILE e CATEGORIAS_FILE removidos

# --- Funções de Carregamento e Salvamento ---

def salvar_lancamentos():
    """Salva a lista de lançamentos no arquivo JSON."""
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.get("lancamentos", []), f, indent=4)

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
            salvar_lancamentos()
    else:
        st.session_state["lancamentos"] = []
        salvar_lancamentos()

# --- Inicialização de Estado ---
if 'show_add_modal' not in st.session_state:
    st.session_state['show_add_modal'] = False
if 'show_edit_modal' not in st.session_state:
    st.session_state['show_edit_modal'] = False
if 'editar_indice' not in st.session_state:
     st.session_state['editar_indice'] = None
if 'editar_lancamento' not in st.session_state:
     st.session_state['editar_lancamento'] = None

carregar_lancamentos()
if "lancamentos" not in st.session_state:
    st.session_state["lancamentos"] = []

CATEGORIAS_FIXAS_RECEITA = ["Serviços","Vendas"]

# --- Funções para Renderizar os Formulários ---

def render_add_lancamento_form():
    """Renderiza o formulário para adicionar um novo lançamento."""
    with st.expander("Adicionar Novo Lançamento", expanded=True):
        st.subheader("Adicionar Lançamento")

        with st.form(key="add_lancamento_form"):
            data_str = st.text_input("Data (DD/MM/AAAA)", key="add_lanc_data_form")
            descricao = st.text_input("Descrição", key="add_lanc_descricao_form")
            tipo = st.selectbox("Tipo de Lançamento", ["Receita", "Despesa"], key="add_lanc_tipo_form")

            categoria_placeholder = st.empty()
            categoria = ""

            if tipo == "Receita":
                categoria = categoria_placeholder.selectbox(
                    "Categoria",
                    CATEGORIAS_FIXAS_RECEITA,
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
        st.subheader("Editar Lançamento")

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
            categoria = ""

            if tipo == "Receita":
                 current_category = lancamento.get("Categorias", "")
                 categorias_disponiveis = CATEGORIAS_FIXAS_RECEITA

                 try:
                     default_index = categorias_disponiveis.index(current_category)
                 except ValueError:
                     default_index = 0

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
                            "Categorias": categoria,
                            "Tipo de Lançamento": tipo,
                            "Valor": valor,
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

    lancamentos_filtrados = st.session_state.get("lancamentos", [])
    st.info("Exibindo resumo de todos os lançamentos.")

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

# Função para exportar lançamentos para PDF (lista detalhada) - Corrigida a passagem de strings
def exportar_lancamentos_para_pdf(lancamentos_list):
    """Exporta a lista detalhada de lançamentos para um arquivo PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    try:
        pdf.add_font('Arial_Unicode', '', 'Arial_Unicode.ttf')
        pdf.set_font('Arial_Unicode', '', 12)
        font_for_table = 'Arial_Unicode'
    except Exception as e:
         pdf.set_font("Arial", '', 12)
         font_for_table = 'Arial'

    pdf.set_font("Arial", 'B', 12)
    report_title = "Relatório Detalhado de Lançamentos"
    # Passa a string diretamente para cell
    pdf.cell(0, 10, report_title, 0, 1, 'C')
    pdf.ln(10)

    pdf.set_font(font_for_table, 'B', 10)
    col_widths = [20, 50, 30, 20, 20]
    headers = ["Data", "Descrição", "Categoria", "Tipo", "Valor"]

    for i, header in enumerate(headers):
        # Passa a string diretamente para cell
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C', fill=False)
    pdf.ln()

    pdf.set_font(font_for_table, '', 10)
    for lancamento in lancamentos_list:
        try:
            data_formatada = datetime.strptime(lancamento.get("Data", '1900-01-01'), "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            data_formatada = lancamento.get("Data", "Data Inválida")

        descricao = lancamento.get("Descrição", "")
        categoria = lancamento.get("Categorias", "")
        tipo = lancamento.get("Tipo de Lançamento", "")
        valor_formatado = f"R$ {lancamento.get('Valor', 0.0):.2f}".replace('.', ',')

        # Passa as strings diretamente para cell
        pdf.cell(col_widths[0], 10, data_formatada, 1, 0, 'C')
        pdf.cell(col_widths[1], 10, descricao, 1, 0, 'L')
        pdf.cell(col_widths[2], 10, categoria if categoria else "", 1, 0, 'C')
        pdf.cell(col_widths[3], 10, tipo, 1, 0, 'C')
        pdf.cell(col_widths[4], 10, valor_formatado, 1, 0, 'R')

        pdf.ln()

    pdf_output = pdf.output(dest='S')

    if isinstance(pdf_output, str):
        pdf_output_bytes = pdf_output.encode('latin-1')
    else:
        pdf_output_bytes = pdf_output

    return io.BytesIO(pdf_output_bytes)


# --- FUNÇÃO para gerar a Demonstração de Resultados em PDF --- Corrigida a passagem de strings
def gerar_demonstracao_resultados_pdf(lancamentos_list):
    """Gera um PDF da Demonstração de Resultados (DRE)."""
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
    report_title = "Demonstração de Resultados"
    # Passa a string diretamente para cell
    pdf.cell(0, 10, report_title, 0, 1, 'C')
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
    # Passa a string diretamente para cell
    pdf.cell(0, 10, "Receitas", 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10)
    for categoria in sorted(receitas_por_categoria.keys()):
        valor = receitas_por_categoria[categoria]
        # Passa as strings diretamente para cell
        pdf.cell(100, 7, f"- {categoria}", 0, 0, 'L')
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ','), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10)
    # Passa a string diretamente para cell
    pdf.cell(100, 7, "Total Receitas", 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_receitas:.2f}".replace('.', ','), 0, 1, 'R')
    pdf.ln(10)

    # --- Adicionar Despesas ao PDF ---
    pdf.set_font(font_for_text, 'B', 12)
    # Passa a string diretamente para cell
    pdf.cell(0, 10, "Despesas", 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font(font_for_text, '', 10)
    for categoria in sorted(despesas_por_categoria.keys()):
        valor = despesas_por_categoria[categoria]
        # Passa as strings diretamente para cell
        pdf.cell(100, 7, f"- {categoria}", 0, 0, 'L')
        pdf.cell(0, 7, f"R$ {valor:.2f}".replace('.', ','), 0, 1, 'R')

    pdf.set_font(font_for_text, 'B', 10)
    # Passa a string diretamente para cell
    pdf.cell(100, 7, "Total Despesas", 0, 0, 'L')
    pdf.cell(0, 7, f"R$ {total_despesas:.2f}".replace('.', ','), 0, 1, 'R')
    pdf.ln(10)

    # --- Adicionar Resultado Líquido ---
    resultado_liquido = total_receitas - total_despesas
    pdf.set_font(font_for_text, 'B', 12)

    if resultado_liquido >= 0:
        pdf.set_text_color(0, 0, 255)
    else:
        pdf.set_text_color(255, 0, 0)

    # Passa a string diretamente para cell
    pdf.cell(100, 10, "Resultado Líquido", 0, 0, 'L')
    pdf.cell(0, 10, f"R$ {resultado_liquido:.2f}".replace('.', ','), 0, 1, 'R')

    pdf.set_text_color(0, 0, 0)

    pdf_output = pdf.output(dest='S')

    if isinstance(pdf_output, str):
        pdf_output_bytes = pdf_output.encode('latin-1')
    else:
        pdf_output_bytes = pdf_output

    return io.BytesIO(pdf_output_bytes)


def exibir_lancamentos():
    """Exibe os lançamentos em um formato tabular com botões de ação por linha."""
    st.subheader("Lançamentos Registrados")

    lancamentos_para_exibir = st.session_state.get("lancamentos", [])
    st.info("Exibindo todos os lançamentos registrados.")

    if not lancamentos_para_exibir:
        st.info("Nenhum lançamento encontrado.")
        # --- Botões de Exportação para lista vazia ---
        col_excel, col_pdf_lista, col_pdf_dr = st.columns([1, 1, 1])
        with col_excel:
             excel_buffer = exportar_lancamentos_para_excel([])
             if excel_buffer:
                st.download_button(
                    label="📥 Exportar para Excel (Vazio)",
                    data=excel_buffer,
                    file_name=f'lancamentos_{datetime.now().strftime("%Y%m%d")}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
        with col_pdf_lista:
             pdf_lista_buffer = exportar_lancamentos_para_pdf([])
             st.download_button(
                label="📄 Exportar Lista PDF (Vazia)",
                data=pdf_lista_buffer,
                file_name=f'lista_lancamentos_{datetime.now().strftime("%Y%m%d")}.pdf',
                mime='application/pdf'
             )
        with col_pdf_dr:
             pdf_dr_buffer = gerar_demonstracao_resultados_pdf([])
             st.download_button(
                label="📊 Exportar DR PDF (Vazia)",
                data=pdf_dr_buffer,
                file_name=f'demonstracao_resultados_{datetime.now().strftime("%Y%m%d")}.pdf',
                mime='application/pdf'
             )
        st.markdown("---")
        return

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


    # --- Exibir Lançamentos em Formato de Colunas (simulando tabela) ---

    # Define as colunas para cabeçalho e linhas de dados
    # Ajuste os valores na lista para controlar a largura relativa das colunas
    # Total da soma das larguras não importa, apenas as proporções relativas entre elas
    col_widths = [2, 4, 3, 2, 2, 1, 1] # Exemplo: Data, Descrição, Categoria, Tipo, Valor, Editar, Excluir

    # Exibir Cabeçalho
    cols_header = st.columns(col_widths)
    headers = ["Data", "Descrição", "Categoria", "Tipo", "Valor", "", ""] # Headers, vazios para colunas de botão

    for col, header in zip(cols_header, headers):
        with col:
            # Use markdown para negrito no cabeçalho
            st.markdown(f"**{header}**")

    st.markdown("---") # Linha horizontal após o cabeçalho

    # Exibir Linhas de Dados com Botões
    # Precisamos do índice original do lançamento na lista session_state['lancamentos']
    # para que as ações de edição/exclusão modifiquem o item correto,
    # mesmo que a lista 'lancamentos_para_exibir' esteja ordenada.

    for i, lancamento_ordenado in enumerate(lancamentos_para_exibir):
        # Cria as colunas para a linha atual de dados e botões
        cols_data = st.columns(col_widths)

        # Encontra o índice original deste lançamento na lista não ordenada do session state
        try:
            indice_original = st.session_state['lancamentos'].index(lancamento_ordenado)
        except ValueError:
             # Isso só aconteceria se o item não fosse encontrado na lista original,
             # o que é improvável se 'lancamentos_para_exibir' veio de lá.
             continue # Pula para o próximo item se não encontrar (segurança)


        # Prepara os dados para exibição formatada
        data_formatada = lancamento_ordenado.get("Data", '1900-01-01')
        try:
            data_formatada = datetime.strptime(data_formatada, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            pass # Mantém o valor original se o formato for inválido

        descricao = lancamento_ordenado.get("Descrição", "")
        categoria = lancamento_ordenado.get("Categorias", "")
        tipo = lancamento_ordenado.get("Tipo de Lançamento", "")
        valor_formatado = f"R$ {lancamento_ordenado.get('Valor', 0.0):.2f}".replace('.', ',')


        # Coloca os dados formatados nas colunas correspondentes
        with cols_data[0]:
            st.write(data_formatada)
        with cols_data[1]:
            st.write(descricao)
        with cols_data[2]:
            st.write(categoria)
        with cols_data[3]:
            st.write(tipo)
        with cols_data[4]:
            st.write(valor_formatado)

        # Coloca os botões de ação nas colunas correspondentes
        with cols_data[5]:
             # Usa o índice original do lançamento na session state como key para o botão
            if st.button("Editar", key=f"editar_{indice_original}", help=f"Editar: {descricao}"):
                st.session_state['editar_indice'] = indice_original
                # Copia os dados do lançamento original para o estado de edição
                st.session_state['editar_lancamento'] = st.session_state['lancamentos'][indice_original].copy()
                st.session_state['show_edit_modal'] = True # Abre o formulário de edição
                st.session_state['show_add_modal'] = False # Fecha o formulário de adicionar, se estiver aberto
                st.rerun() # Roda o aplicativo novamente para exibir o formulário de edição

        with cols_data[6]:
            # Usa o índice original do lançamento na session state como key para o botão
            if st.button("Excluir", key=f"excluir_{indice_original}", help=f"Excluir: {descricao}", type="secondary"):
                del st.session_state['lancamentos'][indice_original] # Remove da lista original
                salvar_lancamentos() # Salva as alterações
                st.success("Lançamento excluído com sucesso!")
                # Limpa o estado de edição se o item excluído era o que estava sendo editado
                if st.session_state.get('editar_indice') == indice_original:
                    st.session_state['editar_indice'] = None
                    st.session_state['editar_lancamento'] = None
                    st.session_state['show_edit_modal'] = False
                st.rerun() # Roda o aplicativo novamente para atualizar a lista exibida

        st.markdown("---") # Linha separadora para cada lançamento (simulando borda de linha)


# --- Layout da Aplicação Principal (Dashboard) ---
def main():
    """Função principal que renderiza o dashboard."""
    st.title("Sistema de Lançamentos Financeiros")

    # Controla a exibição dos formulários de Adicionar ou Editar
    if st.session_state.get('show_add_modal', False):
         render_add_lancamento_form()
    elif st.session_state.get('show_edit_modal', False):
         render_edit_lancamento_form()
    else:
        # Se nenhum formulário estiver aberto, exibe o botão para adicionar e as outras seções
        if st.button("Adicionar Novo Lançamento"):
             st.session_state['show_add_modal'] = True
             st.session_state['show_edit_modal'] = False
             st.rerun()

        exibir_resumo_central()
        exibir_lancamentos()


# --- Execução da Aplicação ---
if __name__ == "__main__":
    main()
