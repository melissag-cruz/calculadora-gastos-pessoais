"""Interface gráfica (tkinter) da calculadora de gastos.

Execute com: python interface.py
"""

import tkinter as tk
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, simpledialog, ttk

import gastos
import relatorios
from gastos import ResumoMensal


class Aplicativo(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Calculadora de Gastos Pessoais")
        self.minsize(820, 480)
        self.mes = tk.StringVar(value=date.today().strftime("%Y-%m"))
        self.texto_resumo = tk.StringVar()
        self.resumo = gastos.resumo_do_mes(self.mes.get())

        self._montar_cabecalho()
        corpo = ttk.Frame(self, padding=(10, 0, 10, 10))
        corpo.pack(fill="both", expand=True)
        corpo.columnconfigure(1, weight=1)
        corpo.rowconfigure(0, weight=1)
        self._montar_formulario(corpo)
        self._montar_tabela(corpo)
        self._montar_resumo(corpo)
        self.atualizar()

    # --- Montagem da tela -----------------------------------------------------------------

    def _montar_cabecalho(self) -> None:
        cabecalho = ttk.Frame(self, padding=10)
        cabecalho.pack(fill="x")
        ttk.Button(cabecalho, text="◀", width=3, command=lambda: self.mudar_mes(-1)).pack(
            side="left"
        )
        ttk.Label(cabecalho, textvariable=self.mes, font=("Segoe UI", 14, "bold")).pack(
            side="left", padx=10
        )
        ttk.Button(cabecalho, text="▶", width=3, command=lambda: self.mudar_mes(1)).pack(
            side="left"
        )

    def _montar_formulario(self, pai: ttk.Frame) -> None:
        formulario = ttk.LabelFrame(pai, text="Nova despesa", padding=10)
        formulario.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.campo_descricao = ttk.Entry(formulario, width=24)
        self.campo_categoria = ttk.Combobox(formulario, width=22)
        self.campo_valor = ttk.Entry(formulario, width=24)
        self.campo_data = ttk.Entry(formulario, width=24)
        self.campo_data.insert(0, date.today().isoformat())

        campos = [
            ("Descrição", self.campo_descricao),
            ("Categoria", self.campo_categoria),
            ("Valor (R$)", self.campo_valor),
            ("Data (AAAA-MM-DD)", self.campo_data),
        ]
        for linha, (rotulo, campo) in enumerate(campos):
            ttk.Label(formulario, text=rotulo).grid(row=linha * 2, column=0, sticky="w")
            campo.grid(row=linha * 2 + 1, column=0, sticky="ew", pady=(0, 8))
            campo.bind("<Return>", lambda _evento: self.adicionar())
        ttk.Button(formulario, text="Adicionar", command=self.adicionar).grid(
            row=len(campos) * 2, column=0, sticky="ew"
        )

    def _montar_tabela(self, pai: ttk.Frame) -> None:
        quadro = ttk.Frame(pai)
        quadro.grid(row=0, column=1, sticky="nsew")
        quadro.columnconfigure(0, weight=1)
        quadro.rowconfigure(0, weight=1)

        # Larguras em número de caracteres, convertidas para pixels conforme a fonte da tela.
        fonte = tkfont.nametofont("TkDefaultFont")
        ttk.Style(self).configure("Treeview", rowheight=fonte.metrics("linespace") + 6)
        colunas = {"data": 11, "descricao": 26, "categoria": 14, "valor": 14}
        self.tabela = ttk.Treeview(quadro, columns=list(colunas), show="headings")
        for coluna, caracteres in colunas.items():
            titulo = "Descrição" if coluna == "descricao" else coluna.capitalize()
            self.tabela.heading(coluna, text=titulo)
            alinhamento = "e" if coluna == "valor" else "w"
            largura = fonte.measure("0") * caracteres
            self.tabela.column(coluna, width=largura, minwidth=largura, anchor=alinhamento)
        self.tabela.grid(row=0, column=0, sticky="nsew")

        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.tabela.yview)
        barra.grid(row=0, column=1, sticky="ns")
        self.tabela.configure(yscrollcommand=barra.set)

        ttk.Button(quadro, text="Remover selecionada", command=self.remover).grid(
            row=1, column=0, sticky="e", pady=(8, 0)
        )

    def _montar_resumo(self, pai: ttk.Frame) -> None:
        quadro = ttk.LabelFrame(pai, text="Resumo do mês", padding=10)
        quadro.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        ttk.Label(quadro, textvariable=self.texto_resumo, justify="left").pack(anchor="w")

        botoes = [
            ("Definir renda mensal", self.pedir_renda),
            ("Definir orçamento", self.pedir_orcamento),
            ("Exportar para Excel", self.exportar_excel),
            ("Ver gráfico", self.mostrar_grafico),
        ]
        for texto, comando in botoes:
            ttk.Button(quadro, text=texto, command=comando).pack(fill="x", pady=(8, 0))

    # --- Ações ----------------------------------------------------------------------------

    def atualizar(self) -> None:
        self.resumo = gastos.resumo_do_mes(self.mes.get())
        self.tabela.delete(*self.tabela.get_children())
        for indice, despesa in enumerate(self.resumo.despesas):
            valor = gastos.formatar_reais(Decimal(despesa["valor"]))
            self.tabela.insert(
                "",
                "end",
                iid=str(indice),
                values=(despesa["data"], despesa["descricao"], despesa["categoria"], valor),
            )

        linhas = self.resumo.linhas_resumo()
        if not self.resumo.despesas:
            linhas.insert(0, "Nenhuma despesa neste mês.\n")
        if self.resumo.renda is None:
            linhas.append("\nInforme sua renda para ver\nquanto sobra no mês.")
        self.texto_resumo.set("\n".join(linhas))
        self.campo_categoria["values"] = gastos.listar_categorias()

    def mudar_mes(self, passo: int) -> None:
        self.mes.set(gastos.deslocar_mes(self.mes.get(), passo))
        self.atualizar()

    def adicionar(self) -> None:
        descricao = self.campo_descricao.get().strip()
        categoria = gastos.normalizar_categoria(self.campo_categoria.get())
        valor = gastos.converter_valor(self.campo_valor.get())
        data_despesa = gastos.converter_data(self.campo_data.get())

        if not descricao or not categoria:
            messagebox.showwarning("Campos vazios", "Preencha a descrição e a categoria.")
            return
        if valor is None:
            messagebox.showwarning("Valor inválido", "Digite um valor maior que zero, ex.: 25,90.")
            return
        if data_despesa is None:
            messagebox.showwarning("Data inválida", "Use o formato AAAA-MM-DD, ex.: 2026-10-08.")
            return

        gastos.salvar_despesa(data_despesa, descricao, categoria, valor)
        self.campo_descricao.delete(0, "end")
        self.campo_valor.delete(0, "end")
        self.campo_descricao.focus()
        self.mes.set(data_despesa[:7])
        self.atualizar()

        excesso = self.resumo.excesso(categoria)
        if excesso:
            messagebox.showwarning(
                "Orçamento ultrapassado",
                f"Você passou {gastos.formatar_reais(excesso)} do orçamento de {categoria}.",
            )

    def remover(self) -> None:
        selecionadas = self.tabela.selection()
        if not selecionadas:
            messagebox.showinfo("Remover", "Selecione uma despesa na tabela.")
            return
        despesa = self.resumo.despesas[int(selecionadas[0])]
        if not messagebox.askyesno("Remover", f"Remover '{despesa['descricao']}'?"):
            return
        todas = gastos.carregar_despesas()
        todas.remove(despesa)
        gastos.salvar_todas(todas)
        self.atualizar()

    def _pedir_valor(self, titulo: str, pergunta: str) -> Decimal | None:
        texto = simpledialog.askstring(titulo, pergunta, parent=self)
        if texto is None:
            return None
        valor = gastos.converter_valor(texto)
        if valor is None:
            messagebox.showwarning(
                "Valor inválido", "Digite um valor maior que zero, ex.: 3000,00."
            )
        return valor

    def pedir_renda(self) -> None:
        valor = self._pedir_valor("Renda mensal", "Quanto você recebe por mês? (ex.: 3000,00)")
        if valor is not None:
            gastos.definir_renda(valor)
            self.atualizar()

    def pedir_orcamento(self) -> None:
        texto = simpledialog.askstring("Orçamento", "Para qual categoria?", parent=self)
        if not texto or not texto.strip():
            return
        categoria = gastos.normalizar_categoria(texto)
        valor = self._pedir_valor("Orçamento", f"Limite mensal para {categoria}: (ex.: 500,00)")
        if valor is not None:
            gastos.definir_orcamento(categoria, valor)
            self.atualizar()

    def _gerar_arquivo(self, gerar: Callable[[ResumoMensal], Path]) -> Path | None:
        if not self.resumo.despesas:
            messagebox.showinfo("Sem despesas", "Não há despesas neste mês.")
            return None
        try:
            return gerar(self.resumo)
        except ModuleNotFoundError:
            messagebox.showerror(
                "Bibliotecas faltando", "Instale com: pip install -r requirements.txt"
            )
            return None

    def exportar_excel(self) -> None:
        caminho = self._gerar_arquivo(relatorios.exportar_excel)
        if caminho:
            messagebox.showinfo("Relatório salvo", f"Relatório salvo em:\n{caminho}")

    def mostrar_grafico(self) -> None:
        caminho = self._gerar_arquivo(relatorios.gerar_grafico)
        if not caminho:
            return
        janela = tk.Toplevel(self)
        janela.title(f"Gastos de {self.resumo.mes}")
        imagem = tk.PhotoImage(file=caminho)
        rotulo = ttk.Label(janela, image=imagem)
        rotulo.image = imagem  # mantém a referência, senão a imagem some da tela
        rotulo.pack()


if __name__ == "__main__":
    try:
        from ctypes import windll

        # Deixa o texto nítido no Windows quando a tela usa escala (125%, 150%...).
        windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        pass
    Aplicativo().mainloop()
