from entity.drawableEntity import DrawableEntity


# @author Daniel McCoy Stephenson
# @since August 5th, 2022
class LivingEntity(DrawableEntity):
    # Excrement spawning cooldown: 5 minutes at 30 ticks per second
    EXCREMENT_COOLDOWN_TICKS = 30 * 60 * 5  # 9000 ticks
    
    def __init__(self, name, color, energy, edibleEntityTypes, tickCreated):
        DrawableEntity.__init__(self, name, color)
        self.energy = energy
        self.edibleEntityTypes = edibleEntityTypes
        self.targetEnergy = energy
        self.tickCreated = tickCreated
        self.tickLastReproduced = None
        self.tickLastExcrement = None

    def getEnergy(self):
        return self.energy

    def setEnergy(self, energy):
        if energy < 0:
            self.energy = 0
        elif energy > 100:
            self.energy = 100
        else:
            self.energy = energy

    def addEnergy(self, amount):
        if self.energy + amount > 100:
            self.energy = 100
        else:
            self.energy += amount

    def removeEnergy(self, amount):
        if self.energy - amount < 0:
            self.energy = 0
        else:
            self.energy -= amount

    def needsEnergy(self):
        return self.energy < self.targetEnergy * 0.50

    def getTargetEnergy(self):
        return self.targetEnergy

    def setTargetEnergy(self, targetEnergy):
        self.targetEnergy = targetEnergy

    def canEat(self, entity):
        for entityType in self.edibleEntityTypes:
            if type(entity) is entityType:
                return True
        return False

    def kill(self):
        self.energy = 0

    def getTickCreated(self):
        return self.tickCreated

    def setTickCreated(self, tick):
        self.tickCreated = tick

    def getAge(self, tick):
        return tick - self.tickCreated

    def getTickLastReproduced(self):
        return self.tickLastReproduced

    def setTickLastReproduced(self, tick):
        self.tickLastReproduced = tick

    def getTickLastExcrement(self):
        return self.tickLastExcrement

    def setTickLastExcrement(self, tick):
        self.tickLastExcrement = tick

    def shouldSpawnExcrement(self, currentTick):
        # Spawn excrement every 5 minutes (at 30 ticks per second)
        if self.tickLastExcrement is None:
            return True
        return (currentTick - self.tickLastExcrement) >= self.EXCREMENT_COOLDOWN_TICKS
