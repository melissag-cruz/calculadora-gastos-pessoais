"""Regras e armazenamento da calculadora de gastos, sem nenhuma interação com o usuário.

Este módulo é usado tanto pela versão de terminal (main.py) quanto pela interface gráfica
(interface.py), para que as duas sigam exatamente as mesmas regras.
"""

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

PASTA = Path(__file__).parent
ARQUIVO_DESPESAS = PASTA / "despesas.csv"
ARQUIVO_CONFIG = PASTA / "configuracoes.json"
COLUNAS = ["data", "descricao", "categoria", "valor"]
ZERO = Decimal("0.00")

Despesa = dict[str, str]


# --- Conversão e formatação ---------------------------------------------------------------


def converter_valor(texto: str) -> Decimal | None:
    """Converte '25,90' ou '25.90' em Decimal; devolve None se não for um valor positivo."""
    try:
        valor = Decimal(texto.strip().replace(",", "."))
    except InvalidOperation:
        return None
    return valor if valor.is_finite() and valor > 0 else None


def converter_data(texto: str) -> str | None:
    """Converte uma data AAAA-MM-DD para o formato padrão; devolve None se for inválida."""
    try:
        return datetime.strptime(texto.strip(), "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def converter_mes(texto: str) -> str | None:
    """Converte um mês AAAA-MM (aceita '2026-3') para '2026-03'; devolve None se for inválido."""
    try:
        return datetime.strptime(texto.strip(), "%Y-%m").strftime("%Y-%m")
    except ValueError:
        return None


def deslocar_mes(mes: str, passo: int) -> str:
    """Avança (ou volta, com passo negativo) um mês no formato AAAA-MM."""
    ano, numero = map(int, mes.split("-"))
    meses = ano * 12 + (numero - 1) + passo
    return f"{meses // 12:04d}-{meses % 12 + 1:02d}"


def normalizar_categoria(categoria: str) -> str:
    """Padroniza a categoria para que 'ALIMENTAÇÃO' e ' alimentação' sejam agrupadas juntas."""
    return " ".join(categoria.split()).capitalize()


def formatar_reais(valor: Decimal) -> str:
    """Formata um Decimal como moeda no padrão brasileiro."""
    valor_formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor_formatado}"


# --- Despesas (CSV) -----------------------------------------------------------------------


def carregar_despesas() -> list[Despesa]:
    """Lê as despesas salvas. Retorna uma lista vazia se o CSV ainda não existir."""
    if not ARQUIVO_DESPESAS.exists():
        return []

    with ARQUIVO_DESPESAS.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def criar_despesa(data_despesa: str, descricao: str, categoria: str, valor: Decimal) -> Despesa:
    return {
        "data": data_despesa,
        "descricao": descricao,
        "categoria": categoria,
        "valor": f"{valor:.2f}",
    }


def salvar_despesa(data_despesa: str, descricao: str, categoria: str, valor: Decimal) -> None:
    """Acrescenta uma despesa ao CSV, criando o cabeçalho se o arquivo for novo."""
    arquivo_novo = not ARQUIVO_DESPESAS.exists() or ARQUIVO_DESPESAS.stat().st_size == 0

    with ARQUIVO_DESPESAS.open("a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        if arquivo_novo:
            escritor.writeheader()
        escritor.writerow(criar_despesa(data_despesa, descricao, categoria, valor))


def salvar_todas(despesas: list[Despesa]) -> None:
    """Regrava o CSV inteiro."""
    # Grava num arquivo temporário e troca no fim, para não perder dados se algo falhar no meio.
    temporario = ARQUIVO_DESPESAS.with_suffix(".tmp")
    with temporario.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(despesas)
    temporario.replace(ARQUIVO_DESPESAS)


def filtrar_por_mes(despesas: list[Despesa], mes: str) -> list[Despesa]:
    """Mantém só as despesas do mês informado no formato AAAA-MM."""
    return [despesa for despesa in despesas if despesa["data"].startswith(f"{mes}-")]


def calcular_resumo(despesas: list[Despesa]) -> tuple[dict[str, Decimal], Decimal]:
    """Retorna (totais por categoria, total geral) de uma lista de despesas."""
    totais_por_categoria: dict[str, Decimal] = {}
    total_geral = ZERO
    for despesa in despesas:
        valor = Decimal(despesa["valor"])
        categoria = despesa["categoria"]
        totais_por_categoria[categoria] = totais_por_categoria.get(categoria, ZERO) + valor
        total_geral += valor
    return totais_por_categoria, total_geral


# --- Renda e orçamentos (JSON) ------------------------------------------------------------


def _ler_config() -> dict:
    if not ARQUIVO_CONFIG.exists():
        return {}
    with ARQUIVO_CONFIG.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def _gravar_config(config: dict) -> None:
    temporario = ARQUIVO_CONFIG.with_suffix(".tmp")
    temporario.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(ARQUIVO_CONFIG)


def obter_renda() -> Decimal | None:
    renda = _ler_config().get("renda_mensal")
    return Decimal(renda) if renda else None


def definir_renda(valor: Decimal) -> None:
    config = _ler_config()
    config["renda_mensal"] = f"{valor:.2f}"
    _gravar_config(config)


def obter_orcamentos() -> dict[str, Decimal]:
    orcamentos = _ler_config().get("orcamentos", {})
    return {categoria: Decimal(valor) for categoria, valor in orcamentos.items()}


def definir_orcamento(categoria: str, valor: Decimal) -> None:
    """Define o limite mensal de gastos de uma categoria."""
    config = _ler_config()
    config.setdefault("orcamentos", {})[categoria] = f"{valor:.2f}"
    _gravar_config(config)


def listar_categorias() -> list[str]:
    """Categorias já usadas em despesas ou orçamentos, em ordem alfabética."""
    categorias = {despesa["categoria"] for despesa in carregar_despesas()}
    return sorted(categorias | obter_orcamentos().keys())


# --- Resumo do mês ------------------------------------------------------------------------


@dataclass
class ResumoMensal:
    mes: str
    despesas: list[Despesa]
    totais_por_categoria: dict[str, Decimal]
    total: Decimal
    renda: Decimal | None
    orcamentos: dict[str, Decimal]

    @property
    def saldo(self) -> Decimal | None:
        return None if self.renda is None else self.renda - self.total

    def excesso(self, categoria: str) -> Decimal:
        """Quanto a categoria passou do orçamento no mês (zero se não passou ou não tem limite)."""
        limite = self.orcamentos.get(categoria)
        if limite is None:
            return ZERO
        return max(self.totais_por_categoria.get(categoria, ZERO) - limite, ZERO)

    def linhas_resumo(self) -> list[str]:
        """Texto do resumo, uma linha por item, usado no terminal e na interface gráfica."""
        linhas = []
        for categoria, total in sorted(self.totais_por_categoria.items()):
            linha = f"{categoria}: {formatar_reais(total)}"
            limite = self.orcamentos.get(categoria)
            if limite is not None:
                linha += f" de {formatar_reais(limite)}"
                excesso = self.excesso(categoria)
                if excesso:
                    linha += f" (passou {formatar_reais(excesso)})"
            linhas.append(linha)
        linhas.append(f"Total: {formatar_reais(self.total)}")
        if self.renda is not None:
            linhas.append(f"Renda: {formatar_reais(self.renda)}")
            linhas.append(f"Saldo: {formatar_reais(self.renda - self.total)}")
        return linhas


def resumo_do_mes(mes: str) -> ResumoMensal:
    """Junta despesas, totais, renda e orçamentos de um mês (AAAA-MM)."""
    despesas = sorted(filtrar_por_mes(carregar_despesas(), mes), key=lambda d: d["data"])
    totais, total = calcular_resumo(despesas)
    return ResumoMensal(mes, despesas, totais, total, obter_renda(), obter_orcamentos())
