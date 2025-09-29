from src.entity.living.livingEntity import LivingEntity


def createLivingEntity():
    return LivingEntity("test", "myimagepath.png", 50, [], 0)


def test_initialization():
    livingEntity = createLivingEntity()

    assert livingEntity.name == "test"
    assert livingEntity.getEnergy() == 50
    assert livingEntity.getTargetEnergy() == 50
    assert livingEntity.getTickCreated() == 0


def test_set_energy():
    livingEntity = createLivingEntity()
    livingEntity.setEnergy(100)

    assert livingEntity.getEnergy() == 100


def test_set_target_energy():
    livingEntity = createLivingEntity()
    livingEntity.setTargetEnergy(100)

    assert livingEntity.getTargetEnergy() == 100


def test_add_energy():
    livingEntity = createLivingEntity()
    livingEntity.addEnergy(50)

    assert livingEntity.getEnergy() == 100


def test_remove_energy():
    livingEntity = createLivingEntity()
    livingEntity.removeEnergy(50)

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


def test_excrement_tick_tracking():
    livingEntity = createLivingEntity()
    
    assert livingEntity.getTickLastExcrement() == None
    
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
