from src.entity.drawableEntity import DrawableEntity


def test_initialization():
    drawableEntity = DrawableEntity("test", "myimagepath.png")

    assert drawableEntity.getName() == "test"
    assert drawableEntity.getImagePath() == "myimagepath.png"
    assert drawableEntity.isSolid() is False


def test_solid_flag():
    assert DrawableEntity("rock", "rock.png", solid=True).isSolid() is True


def test_set_image_path():
    entity = DrawableEntity("test", "old.png")
    entity.setImagePath("new.png")
    assert entity.getImagePath() == "new.png"


# Image loading / scaling / missing-asset placeholder now belong to the
# renderer (PygameRenderer.loadImage); see tests/rendering for that coverage.
