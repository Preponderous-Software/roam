from src.entity.excrement import Excrement


def test_initialization():
    excrement = Excrement(100)

    assert excrement.name == "Excrement"
    assert excrement.getImagePath() == "assets/images/excrement.png"
    assert excrement.isSolid() == False


def test_tick_created():
    excrement = Excrement(200)

    assert excrement.getTickCreated() == 200


def test_set_tick_created():
    excrement = Excrement(100)
    excrement.setTickCreated(500)

    assert excrement.getTickCreated() == 500
