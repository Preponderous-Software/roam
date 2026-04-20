from src.entity.wheatSeed import WheatSeed


def test_initialization():
    seed = WheatSeed()

    assert seed.name == "Wheat Seed"
    assert seed.getImagePath() == "assets/images/wheatSeed.png"
    assert seed.isSolid() == False
