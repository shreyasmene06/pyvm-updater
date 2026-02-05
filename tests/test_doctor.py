import pytest
from src.pyvm.cli import doctor

def test_doctor(mocker):
    mocker.patch('src.pyvm.cli.check_pyenv_installed', return_value=True)
    mocker.patch('src.pyvm.cli.check_mise_installed', return_value=True)
    mocker.patch('src.pyvm.cli.check_network', return_value=True)

    result = doctor()
    assert "All systems operational!" in result.output