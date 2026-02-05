import pytest
from src.pyvm.cli import cli

def test_doctor(mocker):
    mocker.patch('src.pyvm.cli.check_pyenv', return_value=True)
    mocker.patch('src.pyvm.cli.check_mise', return_value=True)
    mocker.patch('src.pyvm.cli.check_network', return_value=True)
    mocker.patch('src.pyvm.cli.check_permissions', return_value=True)

    result = cli.invoke(cli.doctor)
    assert result.exit_code == 0
    assert "All systems go!" in result.output