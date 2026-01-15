from src.entity.wood import Wood


def test_initialization():
    wood = Wood()

    assert wood.name == "Wood"
    assert wood.getImagePath() == "assets/images/oakWood.png"
    assert wood.isSolid() == True
