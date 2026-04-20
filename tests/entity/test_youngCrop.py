from src.entity.youngCrop import YoungCrop


def test_initialization():
    crop = YoungCrop(100)

    assert crop.name == "Young Crop"
    assert crop.getImagePath() == "assets/images/youngCrop.png"
    assert crop.isSolid() == False


def test_tick_planted():
    crop = YoungCrop(200)

    assert crop.getTickPlanted() == 200


def test_set_tick_planted():
    crop = YoungCrop(100)
    crop.setTickPlanted(500)

    assert crop.getTickPlanted() == 500
