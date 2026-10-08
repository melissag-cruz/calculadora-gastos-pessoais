import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import main


class TestFormatarReais(unittest.TestCase):
    def test_valor_simples(self):
        self.assertEqual(main.formatar_reais(Decimal("25.9")), "R$ 25,90")

    def test_valor_com_milhar(self):
        self.assertEqual(main.formatar_reais(Decimal("1234567.89")), "R$ 1.234.567,89")


class TestNormalizarCategoria(unittest.TestCase):
    def test_agrupa_variacoes_de_maiusculas_e_espacos(self):
        for entrada in ["alimentação", "ALIMENTAÇÃO", "  Alimentação "]:
            self.assertEqual(main.normalizar_categoria(entrada), "Alimentação")

    def test_remove_espacos_repetidos(self):
        self.assertEqual(main.normalizar_categoria("pet   shop"), "Pet shop")


class TestPedirTexto(unittest.TestCase):
    def test_repete_ate_receber_texto(self):
        with patch("builtins.input", side_effect=["", "   ", " Mercado "]), patch("builtins.print"):
            self.assertEqual(main.pedir_texto("Descrição"), "Mercado")

    def test_enter_mantem_padrao(self):
        with patch("builtins.input", return_value=""):
            self.assertEqual(main.pedir_texto("Descrição", "Mercado"), "Mercado")


class TestPedirValor(unittest.TestCase):
    def test_aceita_virgula_e_rejeita_invalidos(self):
        with patch("builtins.input", side_effect=["abc", "0", "-5", "nan", "25,90"]), patch("builtins.print"):
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
        with patch("builtins.input", side_effect=["08/10/2026", "2026-02-30", "2026-10-08"]), patch("builtins.print"):
            self.assertEqual(main.pedir_data(), "2026-10-08")


class TestFiltrarPorMes(unittest.TestCase):
    def test_mantem_apenas_o_mes_pedido(self):
        despesas = [
            {"data": "2026-09-30", "valor": "1.00"},
            {"data": "2026-10-01", "valor": "2.00"},
            {"data": "2026-10-31", "valor": "3.00"},
            {"data": "2025-10-15", "valor": "4.00"},
        ]
        resultado = main.filtrar_por_mes(despesas, "2026-10")
        self.assertEqual([d["data"] for d in resultado], ["2026-10-01", "2026-10-31"])


class TestPedirMes(unittest.TestCase):
    def test_enter_usa_mes_atual(self):
        with patch("builtins.input", return_value=""):
            self.assertEqual(main.pedir_mes(), date.today().strftime("%Y-%m"))

    def test_rejeita_mes_invalido_e_completa_zero(self):
        with patch("builtins.input", side_effect=["10/2026", "2026-13", "2026-3"]), patch("builtins.print"):
            self.assertEqual(main.pedir_mes(), "2026-03")


class TestPedirIndice(unittest.TestCase):
    def test_converte_para_indice_e_rejeita_invalidos(self):
        with patch("builtins.input", side_effect=["0", "4", "abc", "²", "2"]), patch("builtins.print"):
            self.assertEqual(main.pedir_indice(3), 1)

    def test_enter_cancela(self):
        with patch("builtins.input", return_value=""):
            self.assertIsNone(main.pedir_indice(3))


class TestCalcularResumo(unittest.TestCase):
    def test_soma_por_categoria_e_total(self):
        despesas = [
            {"categoria": "Alimentação", "valor": "10.50"},
            {"categoria": "Transporte", "valor": "5.00"},
            {"categoria": "Alimentação", "valor": "4.50"},
        ]
        totais, total_geral = main.calcular_resumo(despesas)
        self.assertEqual(totais, {"Alimentação": Decimal("15.00"), "Transporte": Decimal("5.00")})
        self.assertEqual(total_geral, Decimal("20.00"))

    def test_lista_vazia(self):
        self.assertEqual(main.calcular_resumo([]), ({}, Decimal("0.00")))


class TestArquivoCsv(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        caminho = Path(self.pasta.name) / "despesas.csv"
        self.patcher = patch.object(main, "ARQUIVO_DESPESAS", caminho)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.pasta.cleanup()

    def test_carregar_sem_arquivo_retorna_lista_vazia(self):
        self.assertEqual(main.carregar_despesas(), [])

    def test_salvar_e_carregar(self):
        main.salvar_despesa("2026-10-08", "Mercado", "Alimentação", Decimal("85.5"))
        main.salvar_despesa("2026-10-09", "Ônibus", "Transporte", Decimal("4.4"))

        despesas = main.carregar_despesas()
        self.assertEqual(len(despesas), 2)
        self.assertEqual(
            despesas[0],
            {"data": "2026-10-08", "descricao": "Mercado", "categoria": "Alimentação", "valor": "85.50"},
        )
        self.assertEqual(despesas[1]["valor"], "4.40")


class TestEditarOuRemover(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        caminho = Path(self.pasta.name) / "despesas.csv"
        self.patcher = patch.object(main, "ARQUIVO_DESPESAS", caminho)
        self.patcher.start()
        main.salvar_despesa("2026-10-09", "Ônibus", "Transporte", Decimal("4.40"))
        main.salvar_despesa("2026-10-08", "Mercado", "Alimentação", Decimal("85.50"))

    def tearDown(self):
        self.patcher.stop()
        self.pasta.cleanup()

    def executar(self, *respostas):
        with patch("builtins.input", side_effect=list(respostas)), patch("builtins.print"):
            main.editar_ou_remover_despesa()
        return main.carregar_despesas()

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
            {"data": "2026-10-09", "descricao": "Ônibus", "categoria": "Transporte", "valor": "5.00"},
        )
        self.assertEqual(despesas[0]["descricao"], "Mercado")

    def test_cancelar_nao_altera(self):
        despesas = self.executar("")
        self.assertEqual(len(despesas), 2)


if __name__ == "__main__":
    unittest.main()
