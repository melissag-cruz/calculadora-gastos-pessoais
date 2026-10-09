"""Testes da versão de terminal: perguntas ao usuário e opções do menu."""

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import gastos
import main
from tests.auxiliar import TesteComArquivos


def responder(*respostas):
    """Simula o usuário digitando as respostas, na ordem."""
    return patch("builtins.input", side_effect=list(respostas))


class TestPedirTexto(unittest.TestCase):
    def test_repete_ate_receber_texto(self):
        with patch("builtins.input", side_effect=["", "   ", " Mercado "]), patch("builtins.print"):
            self.assertEqual(main.pedir_texto("Descrição"), "Mercado")

    def test_enter_mantem_padrao(self):
        with patch("builtins.input", return_value=""):
            self.assertEqual(main.pedir_texto("Descrição", "Mercado"), "Mercado")


class TestPedirValor(unittest.TestCase):
    def test_aceita_virgula_e_rejeita_invalidos(self):
        with (
            patch("builtins.input", side_effect=["abc", "0", "-5", "nan", "25,90"]),
            patch("builtins.print"),
        ):
            self.assertEqual(main.pedir_valor(), Decimal("25.90"))

    def test_enter_mantem_padrao(self):
        with patch("builtins.input", return_value=""):
            self.assertEqual(main.pedir_valor(Decimal("10.00")), Decimal("10.00"))


class TestPedirData(unittest.TestCase):
    def test_enter_usa_data_de_hoje(self):
        with patch("builtins.input", return_value=""):
            self.assertEqual(main.pedir_data(), date.today().isoformat())

    def test_enter_mantem_padrao(self):
        with patch("builtins.input", return_value=""):
            self.assertEqual(main.pedir_data("2025-01-15"), "2025-01-15")

    def test_rejeita_data_invalida(self):
        with (
            patch("builtins.input", side_effect=["08/10/2026", "2026-02-30", "2026-10-08"]),
            patch("builtins.print"),
        ):
            self.assertEqual(main.pedir_data(), "2026-10-08")


class TestPedirMes(unittest.TestCase):
    def test_enter_usa_mes_atual(self):
        with patch("builtins.input", return_value=""):
            self.assertEqual(main.pedir_mes(), date.today().strftime("%Y-%m"))

    def test_rejeita_mes_invalido_e_completa_zero(self):
        with (
            patch("builtins.input", side_effect=["10/2026", "2026-13", "2026-3"]),
            patch("builtins.print"),
        ):
            self.assertEqual(main.pedir_mes(), "2026-03")


class TestPedirIndice(unittest.TestCase):
    def test_converte_para_indice_e_rejeita_invalidos(self):
        with (
            patch("builtins.input", side_effect=["0", "4", "abc", "²", "2"]),
            patch("builtins.print"),
        ):
            self.assertEqual(main.pedir_indice(3), 1)

    def test_enter_cancela(self):
        with patch("builtins.input", return_value=""):
            self.assertIsNone(main.pedir_indice(3))


class TestEditarOuRemover(TesteComArquivos):
    def setUp(self):
        super().setUp()
        gastos.salvar_despesa("2026-10-09", "Ônibus", "Transporte", Decimal("4.40"))
        gastos.salvar_despesa("2026-10-08", "Mercado", "Alimentação", Decimal("85.50"))

    def executar(self, *respostas):
        with responder(*respostas), patch("builtins.print"):
            main.editar_ou_remover_despesa()
        return gastos.carregar_despesas()

    def test_remove_despesa_escolhida(self):
        # A lista aparece ordenada por data, então o número 1 é o Mercado.
        despesas = self.executar("1", "2", "s")
        self.assertEqual([d["descricao"] for d in despesas], ["Ônibus"])

    def test_remocao_sem_confirmar_nao_altera(self):
        despesas = self.executar("1", "2", "n")
        self.assertEqual(len(despesas), 2)

    def test_edita_so_o_valor(self):
        despesas = self.executar("2", "1", "", "", "5,00", "")
        self.assertEqual(
            despesas[1],
            {
                "data": "2026-10-09",
                "descricao": "Ônibus",
                "categoria": "Transporte",
                "valor": "5.00",
            },
        )
        self.assertEqual(despesas[0]["descricao"], "Mercado")

    def test_cancelar_nao_altera(self):
        despesas = self.executar("")
        self.assertEqual(len(despesas), 2)


class TestAdicionarDespesa(TesteComArquivos):
    def test_salva_com_categoria_padronizada(self):
        with responder("Mercado", "  ALIMENTAÇÃO ", "85,50", "2026-10-08"), patch("builtins.print"):
            main.adicionar_despesa()
        self.assertEqual(
            gastos.carregar_despesas(),
            [
                {
                    "data": "2026-10-08",
                    "descricao": "Mercado",
                    "categoria": "Alimentação",
                    "valor": "85.50",
                }
            ],
        )

    def test_avisa_quando_passa_do_orcamento(self):
        gastos.definir_orcamento("Lazer", Decimal("100"))
        gastos.salvar_despesa("2026-10-01", "Cinema", "Lazer", Decimal("80"))
        with responder("Show", "lazer", "50", "2026-10-20"), patch("builtins.print") as impresso:
            main.adicionar_despesa()
        texto = " ".join(
            str(chamada.args[0]) for chamada in impresso.call_args_list if chamada.args
        )
        self.assertIn("passou R$ 30,00 do orçamento de Lazer", texto)


class TestRendaEOrcamento(TesteComArquivos):
    def test_define_renda(self):
        with responder("3000"), patch("builtins.print"):
            main.definir_renda_mensal()
        self.assertEqual(gastos.obter_renda(), Decimal("3000.00"))

    def test_define_orcamento_com_categoria_padronizada(self):
        with responder("transporte", "200"), patch("builtins.print"):
            main.definir_orcamento_categoria()
        self.assertEqual(gastos.obter_orcamentos(), {"Transporte": Decimal("200.00")})


class TestMostrarMes(TesteComArquivos):
    def test_mostra_saldo_quando_ha_renda(self):
        gastos.definir_renda(Decimal("1000"))
        gastos.salvar_despesa("2026-10-08", "Mercado", "Alimentação", Decimal("250"))
        with responder("2026-10"), patch("builtins.print") as impresso:
            main.mostrar_mes()
        texto = "\n".join(
            str(chamada.args[0]) for chamada in impresso.call_args_list if chamada.args
        )
        self.assertIn("Saldo: R$ 750,00", texto)


if __name__ == "__main__":
    unittest.main()
