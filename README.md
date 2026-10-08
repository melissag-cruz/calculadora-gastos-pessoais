# 💰 Calculadora de Gastos Pessoais

![Testes](https://github.com/melissag-cruz/calculadora-gastos-pessoais/actions/workflows/testes.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

Programa de terminal em Python para registrar despesas do dia a dia, organizá-las por categoria e acompanhar quanto foi gasto em cada mês. Os dados ficam salvos em um arquivo CSV, então nada se perde ao fechar o programa.

## 🚀 Funcionalidades

- **Cadastrar despesas** com descrição, categoria, valor e data (Enter usa a data de hoje).
- **Listar** todas as despesas em ordem de data.
- **Resumo por categoria**, com o total de cada uma e o total geral.
- **Filtrar por mês**, vendo as despesas e o resumo só daquele período.
- **Editar ou remover** um lançamento, com confirmação antes de apagar.
- **Salvar automaticamente** em `despesas.csv`, que também abre no Excel.
- **Validar o que é digitado**: aceita `25,90` ou `25.90`, recusa valores negativos e datas inválidas, e agrupa `alimentação` e `ALIMENTAÇÃO` na mesma categoria.

## 🛠️ Tecnologias

- Python 3
- Módulos nativos: `csv`, `datetime`, `decimal`, `pathlib` e `unittest`
- Git e GitHub Actions

## ▶️ Como executar

Pré-requisito: **Python 3.10 ou superior**. Não é preciso instalar nenhuma biblioteca.

```bash
git clone https://github.com/melissag-cruz/calculadora-gastos-pessoais.git
cd calculadora-gastos-pessoais
python main.py
```

> No Windows, se `python` não funcionar, use `py main.py`.

## 📋 Exemplo de uso

```text
=== Calculadora de Gastos Pessoais ===
1. Adicionar despesa
2. Listar despesas
3. Ver resumo dos gastos
4. Ver gastos de um mês
5. Editar ou remover despesa
0. Sair
Escolha uma opção: 4

Mês (AAAA-MM; Enter para 2026-10):

--- Despesas de 2026-10 ---
2026-10-05 | Moradia | Aluguel | R$ 1.000,00
2026-10-08 | Alimentação | Mercado | R$ 485,50
2026-10-10 | Transporte | Ônibus | R$ 4,40
2026-10-12 | Alimentação | Restaurante | R$ 62,90

--- Resumo de 2026-10 ---
Alimentação: R$ 548,40
Moradia: R$ 1.000,00
Transporte: R$ 4,40
Total: R$ 1.552,80
```

## 🧪 Testes

O projeto tem testes automatizados com o módulo nativo `unittest`:

```bash
python -m unittest discover -s tests -t . -v
```

Os testes também rodam automaticamente no **GitHub Actions** a cada push, em mais de uma versão do Python.

## 📁 Estrutura do projeto

```text
├── main.py                  # Programa principal
├── tests/
│   └── test_main.py         # Testes automatizados
└── .github/workflows/
    └── testes.yml           # Integração contínua (CI)
```

> 🔒 O `despesas.csv` está no `.gitignore`, então seus gastos reais nunca são enviados ao GitHub.

##  Aprendizados

Durante o desenvolvimento deste projeto pratiquei:

- Organizar o código em funções pequenas e reutilizáveis
- Ler e gravar arquivos CSV
- Validar dados digitados pelo usuário
- Usar `Decimal` para trabalhar com dinheiro sem erros de arredondamento
- Escrever testes automatizados
- Versionar com Git e configurar integração contínua no GitHub

## 🎯 Próximas melhorias

- Informar a renda mensal e ver o saldo restante do mês
- Gráficos de gastos por categoria
- Exportar relatório mensal para Excel
- Interface gráfica

## 👩‍💻 Autora

Feito por **Melissa Gomes Silva Cruz**.

[GitHub](https://github.com/melissag-cruz)
