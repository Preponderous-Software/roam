from src.entity.excrement import Excrement


def test_initialization():
    excrement = Excrement(100)

    assert excrement.name == "Excrement"
    assert excrement.getImagePath() == "assets/images/excrement.png"
    assert excrement.isSolid() == False
    assert excrement.getTickCreated() == 100


def test_age_calculation():
    excrement = Excrement(100)
    
    assert excrement.getAge(100) == 0
    assert excrement.getAge(150) == 50
    assert excrement.getAge(200) == 100