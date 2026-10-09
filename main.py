"""Calculadora de gastos pessoais no terminal."""

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path

import relatorios
from gastos import (
    Despesa,
    ResumoMensal,
    calcular_resumo,
    carregar_despesas,
    converter_data,
    converter_mes,
    converter_valor,
    criar_despesa,
    definir_orcamento,
    definir_renda,
    formatar_reais,
    normalizar_categoria,
    obter_orcamentos,
    obter_renda,
    resumo_do_mes,
    salvar_despesa,
    salvar_todas,
)

MENSAGEM_DEPENDENCIAS = (
    "Essa opção precisa de bibliotecas extras. Instale com: pip install -r requirements.txt\n"
)


def pedir_texto(rotulo: str, padrao: str | None = None) -> str:
    """Pede um texto não vazio; se houver `padrao`, Enter mantém esse valor."""
    sufixo = f" (Enter mantém '{padrao}')" if padrao else ""
    while True:
        texto = input(f"{rotulo}{sufixo}: ").strip()
        if texto:
            return texto
        if padrao:
            return padrao
        print("Este campo não pode ficar vazio.")


def pedir_valor(padrao: Decimal | None = None) -> Decimal:
    """Pede um valor positivo e aceita vírgula ou ponto como separador decimal."""
    dica = "ex.: 25,90" if padrao is None else f"Enter mantém {formatar_reais(padrao)}"
    while True:
        texto = input(f"Valor ({dica}): R$ ").strip()
        if not texto and padrao is not None:
            return padrao
        valor = converter_valor(texto)
        if valor is not None:
            return valor
        print("Digite um valor válido maior que zero.")


def pedir_data(padrao: str | None = None) -> str:
    """Pede uma data no formato AAAA-MM-DD; Enter usa `padrao` ou a data de hoje."""
    padrao = padrao or date.today().isoformat()
    while True:
        texto = input(f"Data (AAAA-MM-DD; Enter para {padrao}): ").strip()
        if not texto:
            return padrao
        data_convertida = converter_data(texto)
        if data_convertida:
            return data_convertida
        print("Data inválida. Use o formato AAAA-MM-DD, por exemplo 2026-10-08.")


def pedir_mes() -> str:
    """Pede um mês no formato AAAA-MM; Enter usa o mês atual."""
    mes_atual = date.today().strftime("%Y-%m")
    while True:
        texto = input(f"Mês (AAAA-MM; Enter para {mes_atual}): ").strip()
        if not texto:
            return mes_atual
        mes = converter_mes(texto)
        if mes:
            return mes
        print("Mês inválido. Use o formato AAAA-MM, por exemplo 2026-10.")


def avisar_orcamento(categoria: str, data_despesa: str) -> None:
    resumo = resumo_do_mes(data_despesa[:7])
    excesso = resumo.excesso(categoria)
    if excesso:
        print(
            f"Atenção: em {resumo.mes} você passou {formatar_reais(excesso)} "
            f"do orçamento de {categoria}."
        )


def adicionar_despesa() -> None:
    descricao = pedir_texto("Descrição")
    categoria = normalizar_categoria(pedir_texto("Categoria (ex.: alimentação)"))
    valor = pedir_valor()
    data_despesa = pedir_data()
    salvar_despesa(data_despesa, descricao, categoria, valor)
    print("Despesa salva com sucesso!")
    avisar_orcamento(categoria, data_despesa)
    print()


def formatar_linha(despesa: Despesa) -> str:
    valor = formatar_reais(Decimal(despesa["valor"]))
    return f"{despesa['data']} | {despesa['categoria']} | {despesa['descricao']} | {valor}"


def imprimir_despesas(despesas: list[Despesa], titulo: str) -> None:
    print(f"\n--- {titulo} ---")
    for despesa in sorted(despesas, key=lambda d: d["data"]):
        print(formatar_linha(despesa))
    print()


def listar_despesas() -> None:
    despesas = carregar_despesas()
    if not despesas:
        print("Ainda não há despesas cadastradas.\n")
        return
    imprimir_despesas(despesas, "Suas despesas")


def imprimir_resumo(despesas: list[Despesa], titulo: str) -> None:
    totais_por_categoria, total_geral = calcular_resumo(despesas)
    print(f"--- {titulo} ---")
    for categoria, total in sorted(totais_por_categoria.items()):
        print(f"{categoria}: {formatar_reais(total)}")
    print(f"Total: {formatar_reais(total_geral)}\n")


def mostrar_resumo() -> None:
    despesas = carregar_despesas()
    if not despesas:
        print("Ainda não há despesas para resumir.\n")
        return
    print()
    imprimir_resumo(despesas, "Resumo dos gastos")


def mostrar_mes() -> None:
    resumo = resumo_do_mes(pedir_mes())
    if not resumo.despesas:
        print(f"Nenhuma despesa encontrada em {resumo.mes}.\n")
        return
    imprimir_despesas(resumo.despesas, f"Despesas de {resumo.mes}")
    print(f"--- Resumo de {resumo.mes} ---")
    print("\n".join(resumo.linhas_resumo()))
    if resumo.renda is None:
        print("Dica: use a opção 6 para informar sua renda e ver quanto sobra no mês.")
    print()


def pedir_indice(total: int) -> int | None:
    """Pede o número de um item da lista (1 a `total`) e devolve o índice; Enter cancela."""
    while True:
        texto = input(f"Número da despesa (1-{total}; Enter cancela): ").strip()
        if not texto:
            return None
        try:
            numero = int(texto)
        except ValueError:
            numero = 0
        if 1 <= numero <= total:
            return numero - 1
        print("Número inválido.")


def editar_ou_remover_despesa() -> None:
    despesas = sorted(carregar_despesas(), key=lambda d: d["data"])
    if not despesas:
        print("Ainda não há despesas cadastradas.\n")
        return

    print("--- Escolha a despesa ---")
    for numero, despesa in enumerate(despesas, start=1):
        print(f"{numero}. {formatar_linha(despesa)}")
    indice = pedir_indice(len(despesas))
    if indice is None:
        print("Operação cancelada.\n")
        return

    despesa = despesas[indice]
    acao = input("1. Editar  2. Remover  (Enter cancela): ").strip()
    if acao == "1":
        descricao = pedir_texto("Descrição", despesa["descricao"])
        categoria = normalizar_categoria(pedir_texto("Categoria", despesa["categoria"]))
        valor = pedir_valor(Decimal(despesa["valor"]))
        data_despesa = pedir_data(despesa["data"])
        despesas[indice] = criar_despesa(data_despesa, descricao, categoria, valor)
        mensagem = "Despesa atualizada!"
    elif acao == "2":
        confirmacao = input(f"Remover '{despesa['descricao']}'? (s/N): ").strip().lower()
        if confirmacao != "s":
            print("Operação cancelada.\n")
            return
        despesas.pop(indice)
        mensagem = "Despesa removida!"
    else:
        print("Operação cancelada.\n")
        return

    salvar_todas(despesas)
    print(f"{mensagem}\n")


def definir_renda_mensal() -> None:
    atual = obter_renda()
    if atual is not None:
        print(f"Renda atual: {formatar_reais(atual)}")
    definir_renda(pedir_valor(atual))
    print("Renda mensal salva!\n")


def definir_orcamento_categoria() -> None:
    orcamentos = obter_orcamentos()
    if orcamentos:
        print("--- Orçamentos atuais ---")
        for categoria, limite in sorted(orcamentos.items()):
            print(f"{categoria}: {formatar_reais(limite)}")
    categoria = normalizar_categoria(pedir_texto("Categoria"))
    valor = pedir_valor(orcamentos.get(categoria))
    definir_orcamento(categoria, valor)
    print(f"Orçamento de {categoria} salvo: {formatar_reais(valor)} por mês.\n")


def gerar_arquivo_do_mes(gerar: Callable[[ResumoMensal], Path], descricao: str) -> None:
    resumo = resumo_do_mes(pedir_mes())
    if not resumo.despesas:
        print(f"Nenhuma despesa encontrada em {resumo.mes}.\n")
        return
    try:
        caminho = gerar(resumo)
    except ModuleNotFoundError:
        print(MENSAGEM_DEPENDENCIAS)
        return
    print(f"{descricao} salvo em: {caminho}\n")


def exportar_excel() -> None:
    gerar_arquivo_do_mes(relatorios.exportar_excel, "Relatório")


def gerar_grafico() -> None:
    gerar_arquivo_do_mes(relatorios.gerar_grafico, "Gráfico")


OPCOES: dict[str, tuple[str, Callable[[], None]]] = {
    "1": ("Adicionar despesa", adicionar_despesa),
    "2": ("Listar despesas", listar_despesas),
    "3": ("Ver resumo dos gastos", mostrar_resumo),
    "4": ("Ver gastos de um mês", mostrar_mes),
    "5": ("Editar ou remover despesa", editar_ou_remover_despesa),
    "6": ("Definir renda mensal", definir_renda_mensal),
    "7": ("Definir orçamento de uma categoria", definir_orcamento_categoria),
    "8": ("Exportar relatório do mês para Excel", exportar_excel),
    "9": ("Gerar gráfico do mês", gerar_grafico),
}


def main() -> None:
    while True:
        print("=== Calculadora de Gastos Pessoais ===")
        for numero, (descricao, _) in OPCOES.items():
            print(f"{numero}. {descricao}")
        print("0. Sair")
        opcao = input("Escolha uma opção: ").strip()
        print()

        if opcao == "0":
            print("Até mais!")
            break
        if opcao in OPCOES:
            OPCOES[opcao][1]()
        else:
            print("Opção inválida. Tente novamente.\n")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nAté mais!")
