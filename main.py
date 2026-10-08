"""Calculadora simples de gastos pessoais com armazenamento em CSV."""

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ARQUIVO_DESPESAS = Path(__file__).with_name("despesas.csv")
COLUNAS = ["data", "descricao", "categoria", "valor"]


Despesa = dict[str, str]


def carregar_despesas() -> list[Despesa]:
    """Lê as despesas salvas. Retorna uma lista vazia se o CSV ainda não existir."""
    if not ARQUIVO_DESPESAS.exists():
        return []

    with ARQUIVO_DESPESAS.open("r", newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


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
        texto = input(f"Valor ({dica}): R$ ").strip().replace(",", ".")
        if not texto and padrao is not None:
            return padrao
        try:
            valor = Decimal(texto)
            if valor.is_finite() and valor > 0:
                return valor
        except InvalidOperation:
            pass
        print("Digite um valor válido maior que zero.")


def pedir_data(padrao: str | None = None) -> str:
    """Pede uma data no formato AAAA-MM-DD; Enter usa `padrao` ou a data de hoje."""
    padrao = padrao or date.today().isoformat()
    while True:
        texto = input(f"Data (AAAA-MM-DD; Enter para {padrao}): ").strip()
        if not texto:
            return padrao
        try:
            return date.fromisoformat(texto).isoformat()
        except ValueError:
            print("Data inválida. Use o formato AAAA-MM-DD, por exemplo 2026-10-08.")


def pedir_mes() -> str:
    """Pede um mês no formato AAAA-MM; Enter usa o mês atual."""
    mes_atual = date.today().strftime("%Y-%m")
    while True:
        texto = input(f"Mês (AAAA-MM; Enter para {mes_atual}): ").strip()
        if not texto:
            return mes_atual
        try:
            return datetime.strptime(texto, "%Y-%m").strftime("%Y-%m")
        except ValueError:
            print("Mês inválido. Use o formato AAAA-MM, por exemplo 2026-10.")


def normalizar_categoria(categoria: str) -> str:
    """Padroniza a categoria para que 'ALIMENTAÇÃO' e ' alimentação' sejam agrupadas juntas."""
    return " ".join(categoria.split()).capitalize()


def adicionar_despesa() -> None:
    descricao = pedir_texto("Descrição")
    categoria = normalizar_categoria(pedir_texto("Categoria (ex.: alimentação)"))
    valor = pedir_valor()
    data_despesa = pedir_data()
    salvar_despesa(data_despesa, descricao, categoria, valor)
    print("Despesa salva com sucesso!\n")


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


def formatar_reais(valor: Decimal) -> str:
    """Formata um Decimal como moeda no padrão brasileiro."""
    valor_formatado = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor_formatado}"


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


def calcular_resumo(despesas: list[Despesa]) -> tuple[dict[str, Decimal], Decimal]:
    """Retorna (totais por categoria, total geral) de uma lista de despesas."""
    totais_por_categoria: dict[str, Decimal] = {}
    total_geral = Decimal("0.00")
    for despesa in despesas:
        valor = Decimal(despesa["valor"])
        categoria = despesa["categoria"]
        totais_por_categoria[categoria] = totais_por_categoria.get(categoria, Decimal("0.00")) + valor
        total_geral += valor
    return totais_por_categoria, total_geral


def filtrar_por_mes(despesas: list[Despesa], mes: str) -> list[Despesa]:
    """Mantém só as despesas do mês informado no formato AAAA-MM."""
    return [despesa for despesa in despesas if despesa["data"].startswith(f"{mes}-")]


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
    mes = pedir_mes()
    despesas = filtrar_por_mes(carregar_despesas(), mes)
    if not despesas:
        print(f"Nenhuma despesa encontrada em {mes}.\n")
        return
    imprimir_despesas(despesas, f"Despesas de {mes}")
    imprimir_resumo(despesas, f"Resumo de {mes}")


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


def main() -> None:
    while True:
        print("=== Calculadora de Gastos Pessoais ===")
        print("1. Adicionar despesa")
        print("2. Listar despesas")
        print("3. Ver resumo dos gastos")
        print("4. Ver gastos de um mês")
        print("5. Editar ou remover despesa")
        print("0. Sair")
        opcao = input("Escolha uma opção: ").strip()
        print()

        if opcao == "1":
            adicionar_despesa()
        elif opcao == "2":
            listar_despesas()
        elif opcao == "3":
            mostrar_resumo()
        elif opcao == "4":
            mostrar_mes()
        elif opcao == "5":
            editar_ou_remover_despesa()
        elif opcao == "0":
            print("Até mais!")
            break
        else:
            print("Opção inválida. Tente novamente.\n")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nAté mais!")
