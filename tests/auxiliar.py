import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gastos


class TesteComArquivos(unittest.TestCase):
    """Faz cada teste usar arquivos de dados numa pasta temporária, sem tocar nos seus dados."""

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        for atributo, nome in [
            ("ARQUIVO_DESPESAS", "despesas.csv"),
            ("ARQUIVO_CONFIG", "configuracoes.json"),
        ]:
            patcher = patch.object(gastos, atributo, self.pasta / nome)
            patcher.start()
            self.addCleanup(patcher.stop)
