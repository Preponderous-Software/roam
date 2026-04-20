from src.entity.matureCrop import MatureCrop


def test_initialization():
    crop = MatureCrop(100)

    assert crop.name == "Mature Crop"
    assert crop.getImagePath() == "assets/images/matureCrop.png"
    assert crop.isSolid() == False


def test_tick_planted():
    crop = MatureCrop(200)

    assert crop.getTickPlanted() == 200


def test_set_tick_planted():
    crop = MatureCrop(100)
    crop.setTickPlanted(500)

    assert crop.getTickPlanted() == 500
