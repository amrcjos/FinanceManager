
import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from collections import defaultdict

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database import (
    criar_tabelas,
    criar_conta,
    listar_contas,
    listar_contas_com_saldo,
    atualizar_conta,
    excluir_conta,
    listar_categorias,
    criar_categoria,
    atualizar_categoria,
    excluir_categoria,
    adicionar_transacao,
    listar_transacoes,
    obter_resumo,
    excluir_transacao,
    atualizar_transacao,
)


# =========================================================
# IDENTIDADE VISUAL
# =========================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#191919"
SIDEBAR = "#202020"
SURFACE = "#242424"
SURFACE_HOVER = "#2C2C2C"
BORDER = "#333333"
TEXT = "#EEEEEE"
MUTED = "#999999"
GREEN = "#63B889"
RED = "#E47777"
BLUE = "#78A9D4"

PERIODOS = ["Mês atual", "Mês anterior", "Últimos 3 meses", "Mês específico"]

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


# =========================================================
# INICIALIZACAO
# =========================================================

criar_tabelas()

if not listar_contas():
    criar_conta("Conta principal")


# =========================================================
# FUNCOES AUXILIARES
# =========================================================

def formatar_moeda(centavos):
    valor = Decimal(centavos) / 100
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def converter_para_centavos(valor):
    valor = valor.strip().replace("R$", "").replace(" ", "")

    if not valor:
        raise ValueError("Informe um valor.")

    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")

    try:
        numero = Decimal(valor)
    except InvalidOperation:
        raise ValueError("Digite um valor válido.")

    if not numero.is_finite() or numero <= 0:
        raise ValueError("O valor precisa ser maior que zero.")

    return int(numero * 100)


def somar_meses(data, quantidade):
    """Retorna o dia 1 do mês, deslocado em 'quantidade' meses."""
    indice = data.year * 12 + (data.month - 1) + quantidade
    return date(indice // 12, indice % 12 + 1, 1)


def fim_do_mes(data):
    return somar_meses(data, 1) - timedelta(days=1)


def nome_mes(data):
    return f"{MESES_PT[data.month - 1]}/{data.year}"


def criar_botao(
    pai,
    texto,
    comando,
    cor=SURFACE,
    hover=SURFACE_HOVER,
    largura=None
):
    return ctk.CTkButton(
        pai,
        text=texto,
        command=comando,
        fg_color=cor,
        hover_color=hover,
        text_color=TEXT,
        corner_radius=8,
        height=36,
        width=largura if largura else 0,
        font=("Segoe UI", 12)
    )


def criar_titulo(pai, titulo, descricao=None):
    ctk.CTkLabel(
        pai,
        text=titulo,
        font=("Segoe UI", 27, "bold"),
        text_color=TEXT
    ).pack(anchor="w")

    if descricao:
        ctk.CTkLabel(
            pai,
            text=descricao,
            font=("Segoe UI", 12),
            text_color=MUTED
        ).pack(anchor="w", pady=(5, 22))


# =========================================================
# APLICACAO
# =========================================================

class FinanceManager(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Finance")
        self.geometry("1350x820")
        self.minsize(1100, 700)
        self.configure(fg_color=BG)

        self.pagina_atual = "Visão geral"
        self.categorias = {}
        self.contas = {}
        self.periodo_visao = "Mês atual"
        self.mes_especifico = date.today().replace(day=1)

        self.criar_interface()
        self.mostrar_pagina("Visão geral")

    # =====================================================
    # ESTRUTURA PRINCIPAL
    # =====================================================

    def criar_interface(self):

        self.sidebar = ctk.CTkFrame(
            self,
            width=235,
            corner_radius=0,
            fg_color=SIDEBAR
        )

        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # MARCA

        marca = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )
        marca.pack(fill="x", padx=22, pady=(28, 35))

        ctk.CTkLabel(
            marca,
            text="◈",
            font=("Segoe UI", 28, "bold"),
            text_color=GREEN
        ).pack(side="left")

        ctk.CTkLabel(
            marca,
            text="finance",
            font=("Segoe UI", 23, "bold"),
            text_color=TEXT
        ).pack(side="left", padx=8)

        # NAVEGACAO

        ctk.CTkLabel(
            self.sidebar,
            text="WORKSPACE",
            font=("Segoe UI", 10, "bold"),
            text_color="#777777"
        ).pack(anchor="w", padx=24, pady=(0, 10))

        self.botoes_navegacao = {}

        paginas = [
            ("Visão geral", "⌂"),
            ("Transações", "⇄"),
            ("Contas", "▣"),
            ("Categorias", "◇"),
            ("Relatórios", "▥"),
        ]

        for nome, simbolo in paginas:
            botao = ctk.CTkButton(
                self.sidebar,
                text=f"   {simbolo}     {nome}",
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                hover_color=SURFACE_HOVER,
                text_color="#B8B8B8",
                font=("Segoe UI", 13),
                command=lambda p=nome: self.mostrar_pagina(p)
            )

            botao.pack(fill="x", padx=12, pady=3)
            self.botoes_navegacao[nome] = botao

        # RODAPE SIDEBAR

        rodape = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )
        rodape.pack(side="bottom", fill="x", padx=15, pady=20)

        ctk.CTkFrame(
            rodape,
            height=1,
            fg_color=BORDER
        ).pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            rodape,
            text="FINANCE MANAGER",
            font=("Segoe UI", 10, "bold"),
            text_color="#777777"
        ).pack(anchor="w", padx=8)

        ctk.CTkLabel(
            rodape,
            text="Controle financeiro pessoal",
            font=("Segoe UI", 10),
            text_color="#666666"
        ).pack(anchor="w", padx=8, pady=(4, 0))

        # AREA PRINCIPAL

        self.main = ctk.CTkFrame(
            self,
            fg_color=BG,
            corner_radius=0
        )

        self.main.pack(
            side="right",
            fill="both",
            expand=True
        )

        self.topbar = ctk.CTkFrame(
            self.main,
            fg_color=BG,
            height=58
        )
        self.topbar.pack(fill="x", padx=35, pady=(12, 0))
        self.topbar.pack_propagate(False)

        self.topbar_label = ctk.CTkLabel(
            self.topbar,
            text="Finance / Visão geral",
            font=("Segoe UI", 11),
            text_color=MUTED
        )
        self.topbar_label.pack(side="left", pady=15)

        ctk.CTkLabel(
            self.topbar,
            text=date.today().strftime("%d/%m/%Y"),
            font=("Segoe UI", 11),
            text_color=MUTED
        ).pack(side="right", pady=15)

        self.content = ctk.CTkScrollableFrame(
            self.main,
            fg_color=BG,
            corner_radius=0
        )

        self.content.pack(
            fill="both",
            expand=True,
            padx=35,
            pady=(5, 25)
        )

    # =====================================================
    # NAVEGACAO
    # =====================================================

    def mostrar_pagina(self, pagina):
        self.pagina_atual = pagina

        for nome, botao in self.botoes_navegacao.items():
            if nome == pagina:
                botao.configure(
                    fg_color="#303A35",
                    text_color="#9AD6B4"
                )
            else:
                botao.configure(
                    fg_color="transparent",
                    text_color="#B8B8B8"
                )

        self.topbar_label.configure(
            text=f"Finance / {pagina}"
        )

        for widget in self.content.winfo_children():
            widget.destroy()

        if pagina == "Visão geral":
            self.pagina_inicio()

        elif pagina == "Transações":
            self.pagina_transacoes()

        elif pagina == "Contas":
            self.pagina_contas()

        elif pagina == "Categorias":
            self.pagina_categorias()

        elif pagina == "Relatórios":
            self.pagina_relatorios()

    def atualizar_pagina(self):
        self.mostrar_pagina(self.pagina_atual)

    # =====================================================
    # COMPONENTES VISUAIS
    # =====================================================

    def criar_card(self, pai, titulo, valor, detalhe, cor):
        card = ctk.CTkFrame(
            pai,
            fg_color=SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )

        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 12)
        )

        ctk.CTkLabel(
            card,
            text=titulo,
            font=("Segoe UI", 11, "bold"),
            text_color=MUTED
        ).pack(anchor="w", padx=20, pady=(18, 10))

        ctk.CTkLabel(
            card,
            text=valor,
            font=("Segoe UI", 23, "bold"),
            text_color=cor
        ).pack(anchor="w", padx=20)

        ctk.CTkLabel(
            card,
            text=detalhe,
            font=("Segoe UI", 10),
            text_color=MUTED
        ).pack(anchor="w", padx=20, pady=(6, 18))

        return card

    def criar_painel(self, pai, titulo):
        painel = ctk.CTkFrame(
            pai,
            fg_color=SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )

        ctk.CTkLabel(
            painel,
            text=titulo,
            font=("Segoe UI", 15, "bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=18, pady=(17, 8))

        return painel

    # =====================================================
    # PERIODO DE ANALISE
    # =====================================================

    def obter_datas_periodo(self):
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        periodo = self.periodo_visao

        if periodo == "Mês anterior":
            inicio = somar_meses(inicio_mes, -1)
            fim = fim_do_mes(inicio)

        elif periodo == "Últimos 3 meses":
            inicio = somar_meses(inicio_mes, -2)
            fim = fim_do_mes(inicio_mes)

        elif periodo == "Mês específico":
            inicio = self.mes_especifico
            fim = fim_do_mes(inicio)

        else:  # Mês atual (padrão)
            inicio = inicio_mes
            fim = fim_do_mes(inicio_mes)

        return inicio, fim

    def rotulo_periodo(self):
        inicio, fim = self.obter_datas_periodo()

        if inicio.year == fim.year and inicio.month == fim.month:
            return nome_mes(inicio)

        return f"{nome_mes(inicio)} a {nome_mes(fim)}"

    def transacoes_do_periodo(self):
        inicio, fim = self.obter_datas_periodo()
        inicio_txt = inicio.isoformat()
        fim_txt = fim.isoformat()

        return [
            t for t in listar_transacoes()
            if inicio_txt <= str(t[4])[:10] <= fim_txt
        ]

    def alterar_periodo(self, valor):
        self.periodo_visao = valor
        self.after(10, self.atualizar_pagina)

    def alterar_mes_especifico(self, valor):
        self.mes_especifico = self.mapa_meses[valor]
        self.after(10, self.atualizar_pagina)

    def criar_seletor_periodo(self, pai):
        barra = ctk.CTkFrame(pai, fg_color="transparent")
        barra.pack(fill="x", pady=(0, 18))

        ctk.CTkLabel(
            barra,
            text="PERÍODO",
            font=("Segoe UI", 10, "bold"),
            text_color=MUTED
        ).pack(side="left", padx=(0, 10))

        menu = ctk.CTkOptionMenu(
            barra,
            values=PERIODOS,
            command=self.alterar_periodo,
            fg_color=SURFACE,
            button_color="#343434",
            button_hover_color="#454545",
            height=36,
            width=170
        )
        menu.set(self.periodo_visao)
        menu.pack(side="left")

        if self.periodo_visao == "Mês específico":
            hoje = date.today().replace(day=1)
            meses = [somar_meses(hoje, -i) for i in range(36)]
            self.mapa_meses = {nome_mes(m): m for m in meses}

            menu_mes = ctk.CTkOptionMenu(
                barra,
                values=list(self.mapa_meses.keys()),
                command=self.alterar_mes_especifico,
                fg_color=SURFACE,
                button_color="#343434",
                button_hover_color="#454545",
                height=36,
                width=170
            )
            menu_mes.set(nome_mes(self.mes_especifico))
            menu_mes.pack(side="left", padx=(8, 0))

        inicio, fim = self.obter_datas_periodo()

        ctk.CTkLabel(
            barra,
            text=f"{inicio.strftime('%d/%m/%Y')}  →  {fim.strftime('%d/%m/%Y')}",
            font=("Segoe UI", 11),
            text_color=MUTED
        ).pack(side="right")

    # =====================================================
    # VISAO GERAL
    # =====================================================

    def pagina_inicio(self):

        criar_titulo(
            self.content,
            "Visão geral",
            "Acompanhe sua vida financeira em um só lugar."
        )

        self.criar_seletor_periodo(self.content)

        resumo = obter_resumo()
        transacoes = self.transacoes_do_periodo()
        rotulo = self.rotulo_periodo()

        receitas = sum(t[2] for t in transacoes if t[3] == "income")
        despesas = sum(t[2] for t in transacoes if t[3] == "expense")

        cards = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        cards.pack(fill="x", pady=(0, 20))

        self.criar_card(
            cards,
            "SALDO TOTAL",
            formatar_moeda(resumo["saldo"]),
            "Saldo acumulado das contas",
            TEXT
        )

        self.criar_card(
            cards,
            "RECEITAS",
            formatar_moeda(receitas),
            f"Receitas em {rotulo}",
            GREEN
        )

        self.criar_card(
            cards,
            "DESPESAS",
            formatar_moeda(despesas),
            f"Despesas em {rotulo}",
            RED
        )

        # GRAFICOS

        area_graficos = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )

        area_graficos.pack(
            fill="both",
            expand=True,
            pady=(0, 20)
        )

        painel_mensal = self.criar_painel(
            area_graficos,
            "Receitas e despesas"
        )

        painel_mensal.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 8)
        )

        self.grafico_mensal(painel_mensal, transacoes)

        painel_categoria = self.criar_painel(
            area_graficos,
            "Despesas por categoria"
        )

        painel_categoria.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(8, 0)
        )

        self.grafico_categorias(painel_categoria, transacoes)

        # TRANSACOES RECENTES

        painel = self.criar_painel(
            self.content,
            "Movimentações do período"
        )
        painel.pack(fill="x", pady=(0, 15))

        recentes = transacoes[:5]

        if not recentes:
            ctk.CTkLabel(
                painel,
                text="Nenhuma movimentação neste período.",
                text_color=MUTED
            ).pack(anchor="w", padx=18, pady=20)

        else:
            for transacao in recentes:
                self.criar_linha_transacao(
                    painel,
                    transacao,
                    mostrar_acoes=False
                )

        criar_botao(
            self.content,
            "+ Nova transação",
            lambda: self.abrir_modal_transacao(),
            cor="#315C46",
            hover="#3C7558"
        ).pack(anchor="w", pady=(0, 15))

    # =====================================================
    # AGREGACOES DO PERIODO
    # =====================================================

    def despesas_por_categoria(self, transacoes):
        totais = defaultdict(int)
        nomes = {}

        for t in transacoes:
            if t[3] == "expense":
                totais[t[7]] += t[2]
                nomes[t[7]] = t[5]

        dados = [(cid, nomes[cid], valor) for cid, valor in totais.items()]
        dados.sort(key=lambda item: item[2], reverse=True)

        return dados

    def historico_do_periodo(self, transacoes):
        """Um mês só -> agrupa por dia. Vários meses -> agrupa por mês."""
        inicio, fim = self.obter_datas_periodo()
        um_mes = (inicio.year, inicio.month) == (fim.year, fim.month)

        rotulos = []
        chaves = []

        if um_mes:
            for dia in range(1, fim.day + 1):
                chaves.append(inicio.replace(day=dia).isoformat())
                rotulos.append(f"{dia:02d}")
            tamanho_chave = 10
        else:
            mes = inicio
            while mes <= fim:
                chaves.append(mes.strftime("%Y-%m"))
                rotulos.append(mes.strftime("%m/%y"))
                mes = somar_meses(mes, 1)
            tamanho_chave = 7

        receitas = {c: 0 for c in chaves}
        despesas = {c: 0 for c in chaves}

        for t in transacoes:
            chave = str(t[4])[:tamanho_chave]

            if chave not in receitas:
                continue

            if t[3] == "income":
                receitas[chave] += t[2]
            else:
                despesas[chave] += t[2]

        return (
            rotulos,
            [receitas[c] / 100 for c in chaves],
            [despesas[c] / 100 for c in chaves],
        )

    # =====================================================
    # GRAFICO MENSAL
    # =====================================================

    def grafico_mensal(self, pai, transacoes):
        meses, receitas, despesas = self.historico_do_periodo(transacoes)

        figura = Figure(
            figsize=(5, 3),
            dpi=100,
            facecolor=SURFACE
        )

        eixo = figura.add_subplot(111)
        eixo.set_facecolor(SURFACE)

        posicoes = list(range(len(meses)))
        largura = 0.34

        eixo.bar(
            [p - largura / 2 for p in posicoes],
            receitas,
            width=largura,
            color=GREEN,
            label="Receitas"
        )

        eixo.bar(
            [p + largura / 2 for p in posicoes],
            despesas,
            width=largura,
            color=RED,
            label="Despesas"
        )

        passo = 1 if len(meses) <= 12 else 2

        eixo.set_xticks(posicoes[::passo])
        eixo.set_xticklabels(meses[::passo], fontsize=8)

        eixo.tick_params(colors=MUTED, labelsize=8)
        eixo.grid(axis="y", alpha=0.12)
        eixo.set_axisbelow(True)

        eixo.legend(
            facecolor=SURFACE,
            labelcolor=TEXT,
            frameon=False,
            fontsize=8
        )

        for borda in eixo.spines.values():
            borda.set_visible(False)

        figura.tight_layout(pad=1.5)

        canvas = FigureCanvasTkAgg(
            figura,
            master=pai
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 12)
        )

    # =====================================================
    # GRAFICO DE CATEGORIAS
    # =====================================================

    def grafico_categorias(self, pai, transacoes):
        dados = self.despesas_por_categoria(transacoes)

        figura = Figure(
            figsize=(5, 3),
            dpi=100,
            facecolor=SURFACE
        )

        eixo = figura.add_subplot(111)
        eixo.set_facecolor(SURFACE)

        if dados:
            nomes = [item[1] for item in dados]
            valores = [item[2] / 100 for item in dados]

            fatias, _ = eixo.pie(
                valores,
                startangle=90,
                wedgeprops={
                    "width": 0.42,
                    "edgecolor": SURFACE
                }
            )

            legenda = [
                f"{nome} · {formatar_moeda(item[2])}"
                for nome, item in zip(nomes, dados)
            ]

            eixo.legend(
                fatias,
                legenda,
                loc="center left",
                bbox_to_anchor=(0.78, 0.5),
                fontsize=8,
                labelcolor=TEXT,
                frameon=False
            )

            eixo.set_aspect("equal")

        else:
            eixo.text(
                0.5,
                0.5,
                "Sem despesas neste período",
                color=MUTED,
                ha="center",
                va="center",
                transform=eixo.transAxes
            )
            eixo.set_axis_off()

        figura.tight_layout(pad=1)

        canvas = FigureCanvasTkAgg(
            figura,
            master=pai
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 12)
        )

    # =====================================================
    # TRANSACOES
    # =====================================================

    def pagina_transacoes(self):

        criar_titulo(
            self.content,
            "Transações",
            "Gerencie suas receitas e despesas."
        )

        barra = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        barra.pack(fill="x", pady=(0, 18))

        self.busca_transacao = ctk.CTkEntry(
            barra,
            placeholder_text="Pesquisar movimentações...",
            height=38,
            fg_color=SURFACE,
            border_color=BORDER,
            text_color=TEXT
        )
        self.busca_transacao.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8)
        )

        self.filtro_tipo = ctk.CTkOptionMenu(
            barra,
            values=["Todas", "Receitas", "Despesas"],
            fg_color=SURFACE,
            button_color="#343434",
            button_hover_color="#454545",
            height=38
        )
        self.filtro_tipo.pack(side="left", padx=5)

        criar_botao(
            barra,
            "Pesquisar",
            self.aplicar_filtros,
            largura=100
        ).pack(side="left", padx=5)

        criar_botao(
            barra,
            "+ Nova",
            self.abrir_modal_transacao,
            cor="#315C46",
            hover="#3C7558",
            largura=105
        ).pack(side="right", padx=(8, 0))

        self.lista_transacoes_frame = ctk.CTkFrame(
            self.content,
            fg_color=SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )

        self.lista_transacoes_frame.pack(
            fill="both",
            expand=True
        )

        self.aplicar_filtros()

    def aplicar_filtros(self):

        busca = self.busca_transacao.get().strip()

        tipo_texto = self.filtro_tipo.get()

        tipo = None

        if tipo_texto == "Receitas":
            tipo = "income"
        elif tipo_texto == "Despesas":
            tipo = "expense"

        transacoes = listar_transacoes(
            busca=busca or None,
            tipo=tipo
        )

        for widget in self.lista_transacoes_frame.winfo_children():
            widget.destroy()

        cabecalho = ctk.CTkFrame(
            self.lista_transacoes_frame,
            fg_color="#292929",
            corner_radius=8
        )
        cabecalho.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            cabecalho,
            text=f"{len(transacoes)} movimentações encontradas",
            font=("Segoe UI", 11, "bold"),
            text_color=MUTED
        ).pack(anchor="w", padx=15, pady=12)

        if not transacoes:
            ctk.CTkLabel(
                self.lista_transacoes_frame,
                text="Nenhuma transação encontrada.",
                text_color=MUTED
            ).pack(pady=30)
            return

        for transacao in transacoes:
            self.criar_linha_transacao(
                self.lista_transacoes_frame,
                transacao,
                mostrar_acoes=True
            )

    def criar_linha_transacao(
        self,
        pai,
        transacao,
        mostrar_acoes=True
    ):
        (
            transacao_id,
            descricao,
            valor,
            tipo,
            data_transacao,
            categoria,
            conta,
            categoria_id,
            conta_id,
            observacoes
        ) = transacao

        cor = GREEN if tipo == "income" else RED
        sinal = "+" if tipo == "income" else "−"

        linha = ctk.CTkFrame(
            pai,
            fg_color="#292929",
            corner_radius=8
        )

        linha.pack(
            fill="x",
            padx=10,
            pady=4
        )

        esquerda = ctk.CTkFrame(
            linha,
            fg_color="transparent"
        )
        esquerda.pack(
            side="left",
            fill="x",
            expand=True,
            padx=15,
            pady=10
        )

        ctk.CTkLabel(
            esquerda,
            text=descricao,
            font=("Segoe UI", 13, "bold"),
            text_color=TEXT
        ).pack(anchor="w")

        ctk.CTkLabel(
            esquerda,
            text=f"{categoria}   ·   {conta}   ·   {data_transacao}",
            font=("Segoe UI", 10),
            text_color=MUTED
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkLabel(
            linha,
            text=f"{sinal} {formatar_moeda(valor)}",
            font=("Segoe UI", 13, "bold"),
            text_color=cor
        ).pack(side="right", padx=15)

        if mostrar_acoes:

            criar_botao(
                linha,
                "Editar",
                lambda t=transacao: self.abrir_modal_transacao(t),
                largura=65
            ).pack(side="right", padx=4, pady=8)

            criar_botao(
                linha,
                "Excluir",
                lambda tid=transacao_id: self.excluir_movimentacao(tid),
                cor="#512C2C",
                hover="#743A3A",
                largura=65
            ).pack(side="right", padx=4, pady=8)

    # =====================================================
    # MODAL DE TRANSACAO
    # =====================================================

    
    def abrir_modal_transacao(self, transacao=None):

        editando = transacao is not None

        janela = ctk.CTkToplevel(self)
        janela.title(
            "Editar transação" if editando else "Nova transação"
        )
        janela.geometry("550x700")
        janela.resizable(False, False)
        janela.configure(fg_color=BG)
        janela.transient(self)
        janela.grab_set()

        # CABEÇALHO
        ctk.CTkLabel(
            janela,
            text="Editar transação" if editando else "Nova transação",
            font=("Segoe UI", 23, "bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=28, pady=(16, 2))

        ctk.CTkLabel(
            janela,
            text="Preencha as informações da movimentação.",
            font=("Segoe UI", 11),
            text_color=MUTED
        ).pack(anchor="w", padx=28, pady=(0, 8))

        # CAMPOS
        campos = ctk.CTkFrame(
            janela,
            fg_color="transparent"
        )
        campos.pack(fill="both", expand=True, padx=28)

        def criar_label(texto):
            ctk.CTkLabel(
                campos,
                text=texto,
                font=("Segoe UI", 10, "bold"),
                text_color=MUTED
            ).pack(anchor="w", pady=(5, 2))

        def criar_entry(placeholder):
            campo = ctk.CTkEntry(
                campos,
                height=34,
                fg_color=SURFACE,
                border_color=BORDER,
                placeholder_text=placeholder
            )
            campo.pack(fill="x")
            return campo

        criar_label("DESCRIÇÃO")
        descricao_entry = criar_entry("Ex.: Compra no mercado")

        criar_label("VALOR")
        valor_entry = criar_entry("Ex.: 150,00")

        criar_label("TIPO")
        tipo_menu = ctk.CTkOptionMenu(
            campos,
            values=["Despesa", "Receita"],
            height=34,
            fg_color=SURFACE,
            button_color="#343434",
            button_hover_color="#454545"
        )
        tipo_menu.pack(fill="x")

        criar_label("CATEGORIA")
        categorias_menu = ctk.CTkOptionMenu(
            campos,
            values=["Selecione"],
            height=34,
            fg_color=SURFACE,
            button_color="#343434",
            button_hover_color="#454545"
        )
        categorias_menu.pack(fill="x")

        criar_label("CONTA")
        contas = listar_contas()
        mapa_contas = {
            nome: conta_id
            for conta_id, nome, tipo, saldo in contas
        }

        conta_menu = ctk.CTkOptionMenu(
            campos,
            values=list(mapa_contas.keys()) or ["Nenhuma conta"],
            height=34,
            fg_color=SURFACE,
            button_color="#343434",
            button_hover_color="#454545"
        )
        conta_menu.pack(fill="x")

        criar_label("DATA")
        data_entry = criar_entry("AAAA-MM-DD")
        data_entry.insert(0, date.today().isoformat())

        criar_label("OBSERVAÇÕES")
        observacoes_entry = criar_entry("Detalhes adicionais")

        # CATEGORIAS
        mapa_categorias = {}

        def atualizar_menu_categorias(tipo_texto):
            tipo = "income" if tipo_texto == "Receita" else "expense"
            categorias = listar_categorias(tipo)

            mapa_categorias.clear()
            mapa_categorias.update({
                nome: categoria_id
                for categoria_id, nome, categoria_tipo in categorias
            })

            nomes = list(mapa_categorias.keys())

            if nomes:
                categorias_menu.configure(values=nomes)
                categorias_menu.set(nomes[0])
            else:
                categorias_menu.configure(values=["Nenhuma categoria"])
                categorias_menu.set("Nenhuma categoria")

        tipo_menu.configure(command=atualizar_menu_categorias)
        tipo_menu.set("Despesa")
        atualizar_menu_categorias("Despesa")

        # PREENCHER NA EDIÇÃO
        if editando:
            (
                transacao_id,
                descricao,
                valor,
                tipo,
                data_transacao,
                categoria,
                conta,
                categoria_id,
                conta_id,
                observacoes
            ) = transacao

            descricao_entry.insert(0, descricao)
            valor_entry.insert(0, f"{valor // 100},{valor % 100:02d}")

            tipo_texto = "Receita" if tipo == "income" else "Despesa"
            tipo_menu.set(tipo_texto)
            atualizar_menu_categorias(tipo_texto)

            if categoria in mapa_categorias:
                categorias_menu.set(categoria)

            if conta in mapa_contas:
                conta_menu.set(conta)

            data_entry.delete(0, "end")
            data_entry.insert(0, data_transacao)

            if observacoes:
                observacoes_entry.insert(0, observacoes)

        # SALVAR
        def salvar():
            try:
                descricao = descricao_entry.get().strip()
                valor_centavos = converter_para_centavos(valor_entry.get())

                tipo_texto = tipo_menu.get()
                tipo = "income" if tipo_texto == "Receita" else "expense"

                categoria_nome = categorias_menu.get()
                conta_nome = conta_menu.get()

                if categoria_nome not in mapa_categorias:
                    raise ValueError("Selecione uma categoria válida.")

                if conta_nome not in mapa_contas:
                    raise ValueError("Selecione uma conta válida.")

                data_transacao = data_entry.get().strip()
                observacoes = observacoes_entry.get().strip() or None

                if editando:
                    atualizar_transacao(
                        transacao[0],
                        descricao,
                        valor_centavos,
                        tipo,
                        data_transacao,
                        mapa_categorias[categoria_nome],
                        mapa_contas[conta_nome],
                        observacoes
                    )
                else:
                    adicionar_transacao(
                        descricao,
                        valor_centavos,
                        tipo,
                        data_transacao,
                        mapa_categorias[categoria_nome],
                        mapa_contas[conta_nome],
                        observacoes
                    )

                janela.destroy()
                self.atualizar_pagina()

                messagebox.showinfo(
                    "Sucesso",
                    "Transação salva com sucesso!"
                )

            except Exception as erro:
                messagebox.showerror(
                    "Erro",
                    str(erro),
                    parent=janela
                )

        criar_botao(
            janela,
            "Salvar transação",
            salvar,
            cor="#315C46",
            hover="#3C7558"
        ).pack(fill="x", padx=28, pady=25)

    def excluir_movimentacao(self, transacao_id):
        confirmar = messagebox.askyesno(
            "Excluir transação",
            "Deseja realmente excluir esta movimentação?"
        )

        if not confirmar:
            return

        try:
            excluir_transacao(transacao_id)
            self.atualizar_pagina()

        except Exception as erro:
            messagebox.showerror("Erro", str(erro))

    # =====================================================
    # CONTAS
    # =====================================================

    def pagina_contas(self):

        criar_titulo(
            self.content,
            "Contas",
            "Organize suas contas e acompanhe os saldos."
        )

        painel = self.criar_painel(
            self.content,
            "Adicionar conta"
        )
        painel.pack(fill="x", pady=(0, 20))

        formulario = ctk.CTkFrame(
            painel,
            fg_color="transparent"
        )
        formulario.pack(fill="x", padx=18, pady=(0, 18))

        nome_entry = ctk.CTkEntry(
            formulario,
            placeholder_text="Nome da conta",
            height=38,
            fg_color="#303030",
            border_color=BORDER
        )
        nome_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tipo_menu = ctk.CTkOptionMenu(
            formulario,
            values=["Conta corrente", "Poupança", "Dinheiro", "Carteira digital"],
            height=38,
            fg_color="#303030",
            button_color="#414141"
        )
        tipo_menu.pack(side="left", padx=5)

        saldo_entry = ctk.CTkEntry(
            formulario,
            placeholder_text="Saldo inicial",
            width=125,
            height=38,
            fg_color="#303030",
            border_color=BORDER
        )
        saldo_entry.pack(side="left", padx=5)

        def salvar_conta():
            try:
                nome = nome_entry.get().strip()
                saldo = saldo_entry.get().strip()

                saldo_centavos = (
                    converter_para_centavos(saldo)
                    if saldo else 0
                )

                tipos = {
                    "Conta corrente": "checking",
                    "Poupança": "savings",
                    "Dinheiro": "cash",
                    "Carteira digital": "digital"
                }

                criar_conta(
                    nome,
                    tipos[tipo_menu.get()],
                    saldo_centavos
                )

                self.pagina_contas()

            except Exception as erro:
                messagebox.showerror("Erro", str(erro))

        criar_botao(
            formulario,
            "Adicionar",
            salvar_conta,
            cor="#315C46",
            hover="#3C7558",
            largura=100
        ).pack(side="left", padx=(8, 0))

        contas = listar_contas_com_saldo()

        for conta in contas:
            (
                conta_id,
                nome,
                tipo,
                saldo_inicial,
                saldo_atual
            ) = conta

            linha = ctk.CTkFrame(
                self.content,
                fg_color=SURFACE,
                corner_radius=10,
                border_width=1,
                border_color=BORDER
            )
            linha.pack(fill="x", pady=5)

            esquerda = ctk.CTkFrame(
                linha,
                fg_color="transparent"
            )
            esquerda.pack(
                side="left",
                fill="x",
                expand=True,
                padx=18,
                pady=15
            )

            ctk.CTkLabel(
                esquerda,
                text=nome,
                font=("Segoe UI", 14, "bold")
            ).pack(anchor="w")

            ctk.CTkLabel(
                esquerda,
                text=f"{tipo}  ·  Saldo inicial: {formatar_moeda(saldo_inicial)}",
                font=("Segoe UI", 10),
                text_color=MUTED
            ).pack(anchor="w", pady=(4, 0))

            ctk.CTkLabel(
                linha,
                text=formatar_moeda(saldo_atual),
                font=("Segoe UI", 15, "bold"),
                text_color=GREEN if saldo_atual >= 0 else RED
            ).pack(side="right", padx=15)

            criar_botao(
                linha,
                "Editar",
                lambda c=conta: self.editar_conta(c),
                largura=65
            ).pack(side="right", padx=5)

            criar_botao(
                linha,
                "Excluir",
                lambda cid=conta_id: self.remover_conta(cid),
                cor="#512C2C",
                hover="#743A3A",
                largura=65
            ).pack(side="right", padx=5)

    def editar_conta(self, conta):
        conta_id, nome, tipo, saldo_inicial, saldo_atual = conta

        novo_nome = ctk.CTkInputDialog(
            text="Nome da conta:",
            title="Editar conta"
        ).get_input()

        if novo_nome is None:
            return

        novo_saldo = ctk.CTkInputDialog(
            text="Novo saldo inicial em reais:",
            title="Editar saldo inicial"
        ).get_input()

        if novo_saldo is None:
            return

        try:
            saldo_centavos = converter_para_centavos(novo_saldo)

            atualizar_conta(
                conta_id,
                novo_nome,
                tipo,
                saldo_centavos
            )

            self.pagina_contas()

        except Exception as erro:
            messagebox.showerror("Erro", str(erro))

    def remover_conta(self, conta_id):
        confirmar = messagebox.askyesno(
            "Excluir conta",
            "Deseja realmente excluir esta conta?"
        )

        if not confirmar:
            return

        try:
            excluir_conta(conta_id)
            self.pagina_contas()

        except Exception as erro:
            messagebox.showerror("Não foi possível excluir", str(erro))

    # =====================================================
    # CATEGORIAS
    # =====================================================

    def pagina_categorias(self):

        criar_titulo(
            self.content,
            "Categorias",
            "Organize suas receitas e despesas."
        )

        painel = self.criar_painel(
            self.content,
            "Nova categoria"
        )
        painel.pack(fill="x", pady=(0, 20))

        formulario = ctk.CTkFrame(
            painel,
            fg_color="transparent"
        )
        formulario.pack(fill="x", padx=18, pady=(0, 18))

        nome_entry = ctk.CTkEntry(
            formulario,
            placeholder_text="Nome da categoria",
            height=38,
            fg_color="#303030",
            border_color=BORDER
        )
        nome_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tipo_menu = ctk.CTkOptionMenu(
            formulario,
            values=["Despesa", "Receita"],
            height=38,
            fg_color="#303030",
            button_color="#414141"
        )
        tipo_menu.pack(side="left", padx=5)

        def salvar_categoria():
            try:
                tipo = (
                    "income"
                    if tipo_menu.get() == "Receita"
                    else "expense"
                )

                criar_categoria(
                    nome_entry.get(),
                    tipo
                )

                self.pagina_categorias()

            except Exception as erro:
                messagebox.showerror("Erro", str(erro))

        criar_botao(
            formulario,
            "Adicionar",
            salvar_categoria,
            cor="#315C46",
            hover="#3C7558",
            largura=100
        ).pack(side="left", padx=(8, 0))

        categorias = listar_categorias()

        for categoria_id, nome, tipo in categorias:

            cor = GREEN if tipo == "income" else RED
            tipo_texto = "Receita" if tipo == "income" else "Despesa"

            linha = ctk.CTkFrame(
                self.content,
                fg_color=SURFACE,
                corner_radius=9,
                border_width=1,
                border_color=BORDER
            )
            linha.pack(fill="x", pady=4)

            ctk.CTkLabel(
                linha,
                text="●",
                text_color=cor,
                font=("Segoe UI", 15)
            ).pack(side="left", padx=(16, 10), pady=12)

            ctk.CTkLabel(
                linha,
                text=nome,
                font=("Segoe UI", 13, "bold")
            ).pack(side="left", pady=12)

            ctk.CTkLabel(
                linha,
                text=tipo_texto,
                text_color=MUTED,
                font=("Segoe UI", 10)
            ).pack(side="right", padx=15)

            criar_botao(
                linha,
                "Editar",
                lambda c=(categoria_id, nome, tipo): self.editar_categoria(c),
                largura=65
            ).pack(side="right", padx=5)

            criar_botao(
                linha,
                "Excluir",
                lambda cid=categoria_id: self.remover_categoria(cid),
                cor="#512C2C",
                hover="#743A3A",
                largura=65
            ).pack(side="right", padx=5)

    def editar_categoria(self, categoria):
        categoria_id, nome, tipo = categoria

        novo_nome = ctk.CTkInputDialog(
            text="Novo nome da categoria:",
            title="Editar categoria"
        ).get_input()

        if novo_nome is None:
            return

        try:
            atualizar_categoria(
                categoria_id,
                novo_nome,
                tipo
            )

            self.pagina_categorias()

        except Exception as erro:
            messagebox.showerror("Erro", str(erro))

    def remover_categoria(self, categoria_id):
        confirmar = messagebox.askyesno(
            "Excluir categoria",
            "Deseja realmente excluir esta categoria?"
        )

        if not confirmar:
            return

        try:
            excluir_categoria(categoria_id)
            self.pagina_categorias()

        except Exception as erro:
            messagebox.showerror(
                "Não foi possível excluir",
                str(erro)
            )

    # =====================================================
    # RELATORIOS
    # =====================================================

    def pagina_relatorios(self):

        criar_titulo(
            self.content,
            "Relatórios",
            "Entenda seus hábitos financeiros e acompanhe seus resultados."
        )

        self.criar_seletor_periodo(self.content)

        transacoes = self.transacoes_do_periodo()

        area = ctk.CTkFrame(
            self.content,
            fg_color="transparent"
        )
        area.pack(fill="both", expand=True)

        painel_mensal = self.criar_painel(
            area,
            "Receitas e despesas do período"
        )
        painel_mensal.pack(
            fill="both",
            expand=True,
            pady=(0, 15)
        )

        self.grafico_mensal(painel_mensal, transacoes)

        painel_categorias = self.criar_painel(
            area,
            "Despesas detalhadas por categoria"
        )
        painel_categorias.pack(
            fill="x",
            pady=(0, 15)
        )

        dados = self.despesas_por_categoria(transacoes)

        if not dados:
            ctk.CTkLabel(
                painel_categorias,
                text="Nenhuma despesa neste período.",
                text_color=MUTED
            ).pack(anchor="w", padx=18, pady=15)

        else:
            total = sum(item[2] for item in dados)

            for categoria_id, nome, valor in dados:
                linha = ctk.CTkFrame(
                    painel_categorias,
                    fg_color="transparent"
                )
                linha.pack(fill="x", padx=18, pady=7)

                percentual = (
                    valor / total * 100
                    if total else 0
                )

                ctk.CTkLabel(
                    linha,
                    text=nome,
                    font=("Segoe UI", 12)
                ).pack(side="left")

                ctk.CTkLabel(
                    linha,
                    text=(
                        f"{formatar_moeda(valor)}"
                        f"   ·   {percentual:.1f}%"
                    ),
                    font=("Segoe UI", 12, "bold"),
                    text_color=RED
                ).pack(side="right")

                barra = ctk.CTkProgressBar(
                    painel_categorias,
                    height=7,
                    progress_color=RED,
                    fg_color="#3A3A3A"
                )
                barra.pack(fill="x", padx=18, pady=(0, 5))
                barra.set(percentual / 100)

    # =====================================================
    # INICIAR
    # =====================================================


if __name__ == "__main__":
    app = FinanceManager()
    app.mainloop()
