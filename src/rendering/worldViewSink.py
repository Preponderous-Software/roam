# @author Claude
# @since October 18th, 2026
#
# Where game logic publishes the per-tick WorldView (RFC 0017 stage 2). A
# frontend that draws the world from a WorldView registers its own sink; the
# default is NullWorldViewSink. worldScreen asks wantsWorldView() once per tick
# and only builds a view when some sink says yes, so 2D frontends (pygame,
# text, web, null), which never ask for one, pay one boolean check per tick.
class WorldViewSink:
    def wantsWorldView(self):
        return False

    def getWantedRadiusRooms(self):
        """How many rooms around the player's room the view should cover."""
        return 1

    def publish(self, worldView):
        pass


class NullWorldViewSink(WorldViewSink):
    pass
