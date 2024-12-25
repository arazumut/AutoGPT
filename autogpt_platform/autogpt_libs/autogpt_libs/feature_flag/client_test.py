import pytest
from ldclient import LDClient

from autogpt_libs.feature_flag.client import feature_flag, mock_flag_variation


@pytest.fixture
def ld_client(mocker):
    client = mocker.Mock(spec=LDClient)
    mocker.patch("ldclient.get", return_value=client)
    client.is_initialized.return_value = True
    return client


@pytest.mark.asyncio
async def test_ozellik_bayragi_acik(ld_client):
    ld_client.variation.return_value = True


    @feature_flag("test-flag")
    async def test_fonksiyonu(kullanici_id: str):
        return "başarılı"

    sonuc = await test_fonksiyonu(kullanici_id="test-kullanici")
    assert sonuc == "başarılı"
    ld_client.variation.assert_called_once()


@pytest.mark.asyncio
async def test_ozellik_bayragi_yetkisiz_cevap(ld_client):
    ld_client.variation.return_value = False

    @feature_flag("test-flag")
    async def test_fonksiyonu(kullanici_id: str):
        return "başarılı"

    sonuc = await test_fonksiyonu(kullanici_id="test-kullanici")
    assert sonuc == {"hata": "devre dışı"}


def test_sahte_bayrak_degisim(ld_client):
    with mock_flag_variation("test-flag", True):
        assert ld_client.variation("test-flag", None, False)

    with mock_flag_variation("test-flag", False):
        assert not ld_client.variation("test-flag", None, False)
