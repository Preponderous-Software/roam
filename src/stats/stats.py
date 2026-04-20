# @author Daniel McCoy Stephenson
from appContainer import component
from config.config import Config
from gameLogging.logger import getLogger
from repositories.statsRepository import StatsRepository

_logger = getLogger(__name__)


@component
class Stats:
    def __init__(self, config: Config, statsRepository: StatsRepository):
        self.config = config
        self.statsRepository = statsRepository
        self.score = 0
        self.roomsExplored = 0
        self.foodEaten = 0
        self.numberOfDeaths = 0

    def getScore(self):
        return self.score

    def setScore(self, score):
        self.score = score

    def incrementScore(self):
        self.score += 1

    def getRoomsExplored(self):
        return self.roomsExplored

    def setRoomsExplored(self, roomsExplored):
        self.roomsExplored = roomsExplored

    def incrementRoomsExplored(self):
        self.roomsExplored += 1

    def getFoodEaten(self):
        return self.foodEaten

    def setFoodEaten(self, applesEaten):
        self.foodEaten = applesEaten

    def incrementFoodEaten(self):
        self.foodEaten += 1

    def getNumberOfDeaths(self):
        return self.numberOfDeaths

    def setNumberOfDeaths(self, numberOfDeaths):
        self.numberOfDeaths = numberOfDeaths

    def incrementNumberOfDeaths(self):
        self.numberOfDeaths += 1

    def save(self):
        self.statsRepository.save(self)

    def load(self):
        self.statsRepository.load(self)
