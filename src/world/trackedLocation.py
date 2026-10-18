from lib.pyenvlib.location import Location


# @author Claude
# @since October 18th, 2026
#
# A Location that tells its Room whenever its entity stack changes, so the
# room's in-memory revision counter (RFC 0017 Open Question 3) covers every
# mutation path: Room/Environment/Grid methods, direct Location.addEntity /
# removeEntity calls from worldScreen and the NPC behaviours, and
# setEntities. WorldViewBuilder re-walks a room only when that counter moved.
#
# The vendored pyenvlib Grid builds plain Location objects, and must not be
# modified, so Room converts its locations in place with trackLocation()
# (a class swap to this subclass, which adds no state of its own beyond the
# back-reference). Nothing here is persisted: RoomJsonReaderWriter writes an
# explicit field list, pinned by tests/world/test_roomJsonReaderWriterFieldPin.py.
class TrackedLocation(Location):
    def addEntity(self, entity):
        Location.addEntity(self, entity)
        self._changed()

    def removeEntity(self, entity):
        Location.removeEntity(self, entity)
        self._changed()

    def setEntities(self, entities):
        Location.setEntities(self, entities)
        self._changed()

    def getLocationRevision(self):
        """The room revision of this location's latest change, so a reader
        can tell which locations of a changed room actually changed."""
        return self._locationRevision

    def _changed(self):
        self._locationRevision = self._revisionRoom.noteLocationChanged(self)


def trackLocation(location, room):
    """Make location report its changes to room (in place)."""
    if not isinstance(location, TrackedLocation):
        location.__class__ = TrackedLocation
    location._revisionRoom = room
    location._locationRevision = room.getRevision()
