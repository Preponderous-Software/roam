from src.entity.wheat import Wheat


def test_initialization():
    wheat = Wheat()

    assert wheat.name == "Wheat"
    assert wheat.getImagePath() == "assets/images/wheat.png"
    assert wheat.isSolid() == False


def test_energy_range():
    for _ in range(50):
        wheat = Wheat()
        assert 10 <= wheat.getEnergy() <= 20
