"""Testes das regras e do armazenamento (módulo gastos)."""

import unittest
from decimal import Decimal

import gastos
from tests.auxiliar import TesteComArquivos


class TestFormatarReais(unittest.TestCase):
    def test_valor_simples(self):
        self.assertEqual(gastos.formatar_reais(Decimal("25.9")), "R$ 25,90")

    def test_valor_com_milhar(self):
        self.assertEqual(gastos.formatar_reais(Decimal("1234567.89")), "R$ 1.234.567,89")

    def test_valor_negativo(self):
        self.assertEqual(gastos.formatar_reais(Decimal("-150")), "R$ -150,00")


class TestNormalizarCategoria(unittest.TestCase):
    def test_agrupa_variacoes_de_maiusculas_e_espacos(self):
        for entrada in ["alimentação", "ALIMENTAÇÃO", "  Alimentação "]:
            self.assertEqual(gastos.normalizar_categoria(entrada), "Alimentação")

    def test_remove_espacos_repetidos(self):
        self.assertEqual(gastos.normalizar_categoria("pet   shop"), "Pet shop")


class TestConversoes(unittest.TestCase):
    def test_converter_valor(self):
        self.assertEqual(gastos.converter_valor("25,90"), Decimal("25.90"))
        self.assertEqual(gastos.converter_valor(" 25.90 "), Decimal("25.90"))
        for invalido in ["", "abc", "0", "-5", "nan", "inf"]:
            self.assertIsNone(gastos.converter_valor(invalido), invalido)

    def test_converter_data(self):
        self.assertEqual(gastos.converter_data("2026-10-08"), "2026-10-08")
        self.assertEqual(gastos.converter_data("2026-1-5"), "2026-01-05")
        for invalida in ["", "08/10/2026", "2026-02-30", "20261008"]:
            self.assertIsNone(gastos.converter_data(invalida), invalida)

    def test_converter_mes(self):
        self.assertEqual(gastos.converter_mes("2026-3"), "2026-03")
        for invalido in ["", "10/2026", "2026-13"]:
            self.assertIsNone(gastos.converter_mes(invalido), invalido)

    def test_deslocar_mes(self):
        self.assertEqual(gastos.deslocar_mes("2026-12", 1), "2027-01")
        self.assertEqual(gastos.deslocar_mes("2026-01", -1), "2025-12")
        self.assertEqual(gastos.deslocar_mes("2026-05", 0), "2026-05")


class TestFiltrarPorMes(unittest.TestCase):
    def test_mantem_apenas_o_mes_pedido(self):
        despesas = [
            {"data": "2026-09-30", "valor": "1.00"},
            {"data": "2026-10-01", "valor": "2.00"},
            {"data": "2026-10-31", "valor": "3.00"},
            {"data": "2025-10-15", "valor": "4.00"},
        ]
        resultado = gastos.filtrar_por_mes(despesas, "2026-10")
        self.assertEqual([d["data"] for d in resultado], ["2026-10-01", "2026-10-31"])


class TestCalcularResumo(unittest.TestCase):
    def test_soma_por_categoria_e_total(self):
        despesas = [
            {"categoria": "Alimentação", "valor": "10.50"},
            {"categoria": "Transporte", "valor": "5.00"},
            {"categoria": "Alimentação", "valor": "4.50"},
        ]
        totais, total_geral = gastos.calcular_resumo(despesas)
        self.assertEqual(totais, {"Alimentação": Decimal("15.00"), "Transporte": Decimal("5.00")})
        self.assertEqual(total_geral, Decimal("20.00"))

    def test_lista_vazia(self):
        self.assertEqual(gastos.calcular_resumo([]), ({}, Decimal("0.00")))


class TestArquivoCsv(TesteComArquivos):
    def test_carregar_sem_arquivo_retorna_lista_vazia(self):
        self.assertEqual(gastos.carregar_despesas(), [])

    def test_salvar_e_carregar(self):
        gastos.salvar_despesa("2026-10-08", "Mercado", "Alimentação", Decimal("85.5"))
        gastos.salvar_despesa("2026-10-09", "Ônibus", "Transporte", Decimal("4.4"))

        despesas = gastos.carregar_despesas()
        self.assertEqual(len(despesas), 2)
        self.assertEqual(
            despesas[0],
            {
                "data": "2026-10-08",
                "descricao": "Mercado",
                "categoria": "Alimentação",
                "valor": "85.50",
            },
        )
        self.assertEqual(despesas[1]["valor"], "4.40")

    def test_salvar_todas_substitui_o_conteudo(self):
        gastos.salvar_despesa("2026-10-08", "Mercado", "Alimentação", Decimal("85.5"))
        nova = gastos.criar_despesa("2026-10-10", "Cinema", "Lazer", Decimal("30"))
        gastos.salvar_todas([nova])
        self.assertEqual(gastos.carregar_despesas(), [nova])


class TestConfiguracoes(TesteComArquivos):
    def test_sem_arquivo_nao_ha_renda_nem_orcamentos(self):
        self.assertIsNone(gastos.obter_renda())
        self.assertEqual(gastos.obter_orcamentos(), {})

    def test_renda_e_orcamentos_sao_salvos_juntos(self):
        gastos.definir_orcamento("Lazer", Decimal("200"))
        gastos.definir_renda(Decimal("3500"))
        gastos.definir_orcamento("Alimentação", Decimal("800"))
        gastos.definir_orcamento("Lazer", Decimal("250"))

        self.assertEqual(gastos.obter_renda(), Decimal("3500.00"))
        self.assertEqual(
            gastos.obter_orcamentos(),
            {"Lazer": Decimal("250.00"), "Alimentação": Decimal("800.00")},
        )

    def test_listar_categorias_junta_despesas_e_orcamentos(self):
        gastos.salvar_despesa("2026-10-08", "Mercado", "Alimentação", Decimal("10"))
        gastos.definir_orcamento("Lazer", Decimal("100"))
        self.assertEqual(gastos.listar_categorias(), ["Alimentação", "Lazer"])


class TestResumoDoMes(TesteComArquivos):
    def setUp(self):
        super().setUp()
        gastos.salvar_despesa("2026-10-12", "Restaurante", "Alimentação", Decimal("62.90"))
        gastos.salvar_despesa("2026-10-05", "Mercado", "Alimentação", Decimal("485.50"))
        gastos.salvar_despesa("2026-10-10", "Ônibus", "Transporte", Decimal("4.40"))
        gastos.salvar_despesa("2026-09-30", "Mês passado", "Alimentação", Decimal("999"))
        gastos.definir_orcamento("Alimentação", Decimal("500"))
        gastos.definir_orcamento("Transporte", Decimal("200"))

    def test_junta_despesas_totais_e_orcamentos_do_mes(self):
        resumo = gastos.resumo_do_mes("2026-10")
        self.assertEqual(
            [d["descricao"] for d in resumo.despesas], ["Mercado", "Ônibus", "Restaurante"]
        )
        self.assertEqual(resumo.total, Decimal("552.80"))
        self.assertEqual(resumo.excesso("Alimentação"), Decimal("48.40"))
        self.assertEqual(resumo.excesso("Transporte"), Decimal("0.00"))
        self.assertEqual(resumo.excesso("Sem orçamento"), Decimal("0.00"))

    def test_sem_renda_nao_mostra_saldo(self):
        resumo = gastos.resumo_do_mes("2026-10")
        self.assertIsNone(resumo.saldo)
        self.assertNotIn("Saldo", "\n".join(resumo.linhas_resumo()))

    def test_com_renda_calcula_saldo(self):
        gastos.definir_renda(Decimal("3000"))
        resumo = gastos.resumo_do_mes("2026-10")
        self.assertEqual(resumo.saldo, Decimal("2447.20"))
        self.assertEqual(
            resumo.linhas_resumo(),
            [
                "Alimentação: R$ 548,40 de R$ 500,00 (passou R$ 48,40)",
                "Transporte: R$ 4,40 de R$ 200,00",
                "Total: R$ 552,80",
                "Renda: R$ 3.000,00",
                "Saldo: R$ 2.447,20",
            ],
        )


if __name__ == "__main__":
    unittest.main()
