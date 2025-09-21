from src.entity.drawableEntity import DrawableEntity


def test_initialization():
    drawableEntity = DrawableEntity("test", "myimagepath.png")

    assert drawableEntity.getName() == "test"
    assert drawableEntity.getImagePath() == "myimagepath.png"


def test_isPushable_default():
    drawableEntity = DrawableEntity("test", "myimagepath.png")
    
    assert drawableEntity.isPushable() == False
