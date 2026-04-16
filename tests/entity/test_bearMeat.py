from src.entity.bearMeat import BearMeat


def test_initialization():
    bearMeat = BearMeat()

    assert bearMeat.name == "Bear Meat"
    assert bearMeat.getImagePath() == "assets/images/bearMeat.png"
    assert bearMeat.isSolid() == False


def test_energy_range():
    for _ in range(50):
        bearMeat = BearMeat()
        assert 25 <= bearMeat.getEnergy() <= 35
