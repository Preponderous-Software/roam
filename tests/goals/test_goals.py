# @author Daniel McCoy Stephenson
from codex.codex import ALL_LIVING_ENTITY_TYPES
from goals.goal import Goal
from goals.goalContext import GoalContext
from goals.goalRegistry import GoalRegistry
from goals.goals import Goals
from goals.goalsJsonReaderWriter import GoalsJsonReaderWriter


class FakeStats:
    def __init__(self, rooms=0, food=0, score=0):
        self._rooms = rooms
        self._food = food
        self._score = score

    def getRoomsExplored(self):
        return self._rooms

    def getFoodEaten(self):
        return self._food

    def getScore(self):
        return self._score


class FakeCodex:
    def __init__(self, discovered=None):
        self._discovered = discovered or []

    def getDiscoveredEntities(self):
        return self._discovered


class FakeDayNightCycle:
    def __init__(self, phase="day"):
        self._phase = phase

    def getPhase(self, tick):
        return self._phase


class FakeTickCounter:
    def __init__(self, tick=0):
        self._tick = tick

    def getTick(self):
        return self._tick


class FakeConfig:
    def __init__(self, path):
        self.pathToSaveDirectory = path


def makeContext(rooms=0, food=0, score=0, discovered=None, phase="day"):
    return GoalContext(
        FakeStats(rooms, food, score),
        FakeCodex(discovered),
        FakeDayNightCycle(phase),
        FakeTickCounter(),
    )


def makeGoals(rooms=0, food=0, score=0, discovered=None, phase="day"):
    return Goals(
        FakeStats(rooms, food, score),
        FakeCodex(discovered),
        FakeDayNightCycle(phase),
        FakeTickCounter(),
    )


def test_goal_completes_when_target_reached():
    goal = Goal("g", "desc", 3, lambda c: c.stats.getRoomsExplored())
    assert goal.evaluate(makeContext(rooms=3)) is True
    assert goal.isCompleted() is True


def test_goal_not_completed_below_target():
    goal = Goal("g", "desc", 5, lambda c: c.stats.getRoomsExplored())
    assert goal.evaluate(makeContext(rooms=2)) is False
    assert goal.isCompleted() is False


def test_goal_evaluate_only_reports_fresh_completion():
    goal = Goal("g", "desc", 1, lambda c: 1)
    assert goal.evaluate(makeContext()) is True
    assert goal.evaluate(makeContext()) is False


def test_progress_is_clamped_to_target():
    goal = Goal("g", "desc", 5, lambda c: c.stats.getRoomsExplored())
    assert goal.getProgress(makeContext(rooms=99)) == 5


def test_registry_provides_default_goals():
    ids = [g.getIdentifier() for g in GoalRegistry().getGoals()]
    assert "explore_5_rooms" in ids
    assert "explore_100_rooms" in ids
    assert "eat_50_food" in ids
    assert "discover_bear" in ids
    assert "discover_all_creatures" in ids
    assert "experience_nightfall" in ids
    assert "witness_dawn" in ids
    assert "reach_score_25" in ids


def test_registry_goal_ids_are_unique():
    ids = [g.getIdentifier() for g in GoalRegistry().getGoals()]
    assert len(ids) == len(set(ids))


def test_evaluate_reports_newly_completed_once():
    goals = makeGoals(rooms=5)
    newly = [g.getDescription() for g in goals.evaluate()]
    assert "Explore 5 rooms" in newly
    assert goals.evaluate() == []


def test_nightfall_goal_completes_at_night():
    goals = makeGoals(phase="night")
    ids = [g.getIdentifier() for g in goals.evaluate()]
    assert "experience_nightfall" in ids


def test_specific_creature_discovery_goal_completes():
    goals = makeGoals(discovered=["Chicken"])
    ids = [g.getIdentifier() for g in goals.evaluate()]
    assert "discover_chicken" in ids
    assert "discover_bear" not in ids
    assert "discover_all_creatures" not in ids


def test_discover_all_creatures_completes_when_all_found():
    goals = makeGoals(discovered=list(ALL_LIVING_ENTITY_TYPES))
    ids = [g.getIdentifier() for g in goals.evaluate()]
    assert "discover_all_creatures" in ids


def test_discover_all_creatures_incomplete_when_some_missing():
    # Discovering only a subset must not complete the "every creature" goal.
    partial = list(ALL_LIVING_ENTITY_TYPES)[:-1]
    goals = makeGoals(discovered=partial)
    ids = [g.getIdentifier() for g in goals.evaluate()]
    assert "discover_all_creatures" not in ids


def test_score_and_dawn_goals_complete():
    goals = makeGoals(score=100, phase="dawn")
    ids = [g.getIdentifier() for g in goals.evaluate()]
    assert "reach_score_25" in ids
    assert "reach_score_100" in ids
    assert "witness_dawn" in ids


def test_completed_count_and_total():
    goals = makeGoals(rooms=5)
    goals.evaluate()
    assert goals.getCompletedCount() == 1
    assert goals.getTotalCount() == len(GoalRegistry().getGoals())


def test_completed_identifiers_roundtrip():
    goals = makeGoals(rooms=5)
    goals.evaluate()
    completed = goals.getCompletedIdentifiers()
    assert "explore_5_rooms" in completed

    restored = makeGoals()
    restored.setCompletedIdentifiers(completed)
    explore = next(
        g for g in restored.getGoals() if g.getIdentifier() == "explore_5_rooms"
    )
    assert explore.isCompleted() is True


def test_reader_writer_roundtrip(tmp_path):
    config = FakeConfig(str(tmp_path / "save"))
    readerWriter = GoalsJsonReaderWriter(config)
    readerWriter.save(["explore_5_rooms", "eat_10_food"])
    assert sorted(readerWriter.load()) == ["eat_10_food", "explore_5_rooms"]


def test_reader_returns_empty_when_missing(tmp_path):
    config = FakeConfig(str(tmp_path / "nonexistent"))
    assert GoalsJsonReaderWriter(config).load() == []
