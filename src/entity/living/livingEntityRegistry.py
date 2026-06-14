from entity.living.bear import Bear
from entity.living.chicken import Chicken
from entity.living.deer import Deer
from entity.living.rabbit import Rabbit
from entity.living.snake import Snake
from entity.living.wolf import Wolf

# Single source of truth mapping a living-entity class name to its constructor.
# Every constructor here takes exactly `tickCreated`, which lets the room and
# stored-inventory readers reconstruct any creature generically instead of
# special-casing each one. Add a new creature here and the save/load round-trip
# picks it up automatically.
LIVING_ENTITY_TYPES = {
    "Bear": Bear,
    "Chicken": Chicken,
    "Deer": Deer,
    "Rabbit": Rabbit,
    "Snake": Snake,
    "Wolf": Wolf,
}
