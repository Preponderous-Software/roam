from src.entity.living.livingEntity import LivingEntity
from src.entity.grass import Grass


def createLivingEntity():
    return LivingEntity("test", "myimagepath.png", 50, [], 0)


def test_initialization():
    livingEntity = createLivingEntity()

    assert livingEntity.name == "test"
    assert livingEntity.getEnergy() == 50
    assert livingEntity.getTargetEnergy() == 50
    assert livingEntity.getTickCreated() == 0
    assert livingEntity.getTickLastExcrement() is None


def test_set_energy():
    livingEntity = createLivingEntity()
    livingEntity.setEnergy(100)

    assert livingEntity.getEnergy() == 100


def test_set_energy_negative():
    livingEntity = createLivingEntity()
    livingEntity.setEnergy(-10)
    
    assert livingEntity.getEnergy() == 0  # Should clamp to 0


def test_set_energy_over_max():
    livingEntity = createLivingEntity()
    livingEntity.setEnergy(150)
    
    assert livingEntity.getEnergy() == 100  # Should clamp to 100


def test_set_target_energy():
    livingEntity = createLivingEntity()
    livingEntity.setTargetEnergy(100)

    assert livingEntity.getTargetEnergy() == 100


def test_add_energy():
    livingEntity = createLivingEntity()
    livingEntity.addEnergy(50)

    assert livingEntity.getEnergy() == 100


def test_add_energy_over_max():
    livingEntity = createLivingEntity()
    livingEntity.setEnergy(90)
    livingEntity.addEnergy(50)  # Should clamp to 100
    
    assert livingEntity.getEnergy() == 100


def test_remove_energy():
    livingEntity = createLivingEntity()
    livingEntity.removeEnergy(50)

    assert livingEntity.getEnergy() == 0


def test_remove_energy_below_zero():
    livingEntity = createLivingEntity()
    livingEntity.setEnergy(10)
    livingEntity.removeEnergy(50)  # Should clamp to 0
    
    assert livingEntity.getEnergy() == 0


def test_needs_energy():
    livingEntity = createLivingEntity()
    assert livingEntity.needsEnergy() == False

    livingEntity.setEnergy(livingEntity.getTargetEnergy() / 2 - 1)
    assert livingEntity.needsEnergy() == True


def test_get_age():
    livingEntity = createLivingEntity()
    assert livingEntity.getAge(100) == 100


def test_kill():
    livingEntity = createLivingEntity()
    livingEntity.kill()

    assert livingEntity.getEnergy() == 0


def test_can_eat():
    livingEntity = createLivingEntity()
    assert livingEntity.canEat("test") == False


def test_can_eat_with_edible_types():
    livingEntity = LivingEntity("test", "path.png", 50, [Grass], 0)
    grass = Grass()
    
    assert livingEntity.canEat(grass) == True
    assert livingEntity.canEat("not grass") == False


def test_excrement_tick_tracking():
    livingEntity = createLivingEntity()
    
    assert livingEntity.getTickLastExcrement() is None
    
    livingEntity.setTickLastExcrement(1000)
    assert livingEntity.getTickLastExcrement() == 1000


def test_should_spawn_excrement():
    livingEntity = createLivingEntity()
    
    # Should spawn excrement initially when never spawned
    assert livingEntity.shouldSpawnExcrement(1000) == True
    
    # Set last excrement tick
    livingEntity.setTickLastExcrement(1000)
    
    # Should not spawn excrement if not enough time has passed
    assert livingEntity.shouldSpawnExcrement(1000) == False
    assert livingEntity.shouldSpawnExcrement(1000 + 5000) == False  # Only 5000 ticks passed
    
    # Should spawn excrement after cooldown (9000 ticks = 5 minutes at 30 tps)
    assert livingEntity.shouldSpawnExcrement(1000 + 9000) == True
    assert livingEntity.shouldSpawnExcrement(1000 + 10000) == True


def test_tick_last_reproduced():
    livingEntity = createLivingEntity()
    
    assert livingEntity.getTickLastReproduced() is None
    
    livingEntity.setTickLastReproduced(5000)
    assert livingEntity.getTickLastReproduced() == 5000
