from src.entity.berry import Berry


def test_initialization():
    berry = Berry()

    assert berry.name == "Berry"
    assert berry.getImagePath() == "assets/images/banana.png"
    assert berry.isSolid() == False
