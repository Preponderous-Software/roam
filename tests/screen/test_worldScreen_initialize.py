from unittest.mock import MagicMock


def _makeWorldScreen(test_config):
    from screen.worldScreen import WorldScreen
    from rendering.renderer import Renderer

    ws = WorldScreen.__new__(WorldScreen)
    ws.config = test_config
    ws.container = MagicMock()
    ws.status = MagicMock()
    ws.roomPreloader = MagicMock()
    ws.hudDragManager = MagicMock()
    ws.startingHomeGenerator = MagicMock()
    ws.player = MagicMock()
    ws.stats = MagicMock()
    ws.restApiServer = MagicMock()
    ws.renderer = MagicMock(spec=Renderer)
    ws.renderer.getGameAreaRect.return_value = MagicMock(width=720, height=720)
    ws.renderer.getDisplaySize.return_value = (720, 720)
    ws.currentZ = 0
    ws.initializeLocationWidthAndHeight = MagicMock()
    ws.discoverEntitiesInRoom = MagicMock()
    ws.save = MagicMock()
    return ws


def test_initialize_saves_brand_new_world(test_config):
    from screen.worldScreen import Map, EnergyBar

    ws = _makeWorldScreen(test_config)
    ws.startingHomeGenerator.generate.return_value = -1

    room = MagicMock()
    room.getX.return_value = 0
    room.getY.return_value = 0
    gameMap = MagicMock()
    gameMap.getRoom.return_value = -1
    gameMap.generateNewRoom.return_value = room
    gameMap.consumeIsNewRoom.return_value = True

    energyBar = MagicMock()

    def resolve(dependencyType):
        if dependencyType is Map:
            return gameMap
        if dependencyType is EnergyBar:
            return energyBar
        raise AssertionError(f"unexpected dependency: {dependencyType}")

    ws.container.resolve.side_effect = resolve

    ws.initialize()

    ws.save.assert_called_once_with()


def test_initialize_does_not_save_existing_world(test_config):
    from screen.worldScreen import Map, EnergyBar

    ws = _makeWorldScreen(test_config)

    room = MagicMock()
    room.getX.return_value = 0
    room.getY.return_value = 0
    gameMap = MagicMock()
    gameMap.getRoom.return_value = room
    gameMap.consumeIsNewRoom.return_value = False

    energyBar = MagicMock()

    def resolve(dependencyType):
        if dependencyType is Map:
            return gameMap
        if dependencyType is EnergyBar:
            return energyBar
        raise AssertionError(f"unexpected dependency: {dependencyType}")

    ws.container.resolve.side_effect = resolve

    ws.initialize()

    ws.save.assert_not_called()


def test_initialize_registers_and_loads_hud_layout(test_config):
    from screen.worldScreen import Map, EnergyBar

    ws = _makeWorldScreen(test_config)

    room = MagicMock()
    room.getX.return_value = 0
    room.getY.return_value = 0
    gameMap = MagicMock()
    gameMap.getRoom.return_value = room
    gameMap.consumeIsNewRoom.return_value = False

    energyBar = MagicMock()

    def resolve(dependencyType):
        if dependencyType is Map:
            return gameMap
        if dependencyType is EnergyBar:
            return energyBar
        raise AssertionError(f"unexpected dependency: {dependencyType}")

    ws.container.resolve.side_effect = resolve

    ws.initialize()

    registeredNames = [
        call.args[0] for call in ws.hudDragManager.register.call_args_list
    ]
    assert registeredNames == ["hotbar", "status", "energyBar", "minimap"]
    ws.hudDragManager.load.assert_called_once()
    loadArgs = ws.hudDragManager.load.call_args.args
    assert loadArgs[1:] == (720, 720)
