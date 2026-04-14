from src.entity.chickenMeat import ChickenMeat


def test_initialization():
    chickenMeat = ChickenMeat()

    assert chickenMeat.name == "Chicken Meat"
    assert chickenMeat.getImagePath() == "assets/images/chickenMeat.png"
    assert chickenMeat.isSolid() == False


def test_energy_range():
    for _ in range(50):
        chickenMeat = ChickenMeat()
        assert 15 <= chickenMeat.getEnergy() <= 25
