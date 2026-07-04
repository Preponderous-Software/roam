from entity.living.npc import Npc, randomNpcName


def _npc():
    return Npc("TestNPC", 0)


def test_initialization():
    npc = _npc()
    assert npc.getName() == "TestNPC"
    assert npc.getEnergy() == 100
    assert npc.getTargetEnergy() == 100
    assert npc.getMode() == "npc"
    assert npc.isSolid() is False
    assert npc.getDirection() == -1
    assert npc.getTickLastMoved() == -1
    assert npc.getTickLastGathered() == -1
    assert npc.getTickLastPlaced() == -1


def test_set_direction_tracks_last():
    npc = _npc()
    npc.setDirection(2)
    assert npc.getDirection() == 2
    assert npc.getLastDirection() == -1
    npc.setDirection(3)
    assert npc.getDirection() == 3
    assert npc.getLastDirection() == 2


def test_mode_toggle():
    npc = _npc()
    assert npc.getMode() == "npc"
    npc.setMode("cpc")
    assert npc.getMode() == "cpc"
    npc.setMode("npc")
    assert npc.getMode() == "npc"


def test_is_dead_when_energy_below_one():
    npc = _npc()
    npc.setEnergy(0.5)
    assert npc.isDead() is True


def test_is_dead_at_zero_energy():
    npc = _npc()
    npc.setEnergy(0)
    assert npc.isDead() is True


def test_is_not_dead_at_full_energy():
    npc = _npc()
    assert npc.isDead() is False


def test_is_not_dead_at_one():
    npc = _npc()
    npc.setEnergy(1)
    assert npc.isDead() is False


def test_inventory_accessible():
    npc = _npc()
    assert npc.getInventory() is not None


def test_random_npc_name_is_nonempty_string():
    name = randomNpcName()
    assert isinstance(name, str)
    assert len(name) > 0
