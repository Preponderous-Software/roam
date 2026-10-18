# Roam 3D spectator

A read-only 3D view of a running game (RFC 0017, stage 1). It renders Roam's
own sprites as an HD-2D diorama: tiles become textured terrain, rooms are
raised by biome (mountains highest), rocks and trees become blocks, and
creatures, items and the player are upright cards. Light sources (torches,
campfires, golden lanterns) are real point lights at night, and the time of
day follows the game's own day/night curve.

It never sends input to the game and cannot change it or its saves.

## Turning it on

1. In `config.yml`, set `restEnabled: true` (the port is `restPort`, 8090 by
   default).
2. Start Roam (desktop or `--text`) and open a world.
3. Open <http://127.0.0.1:8090/spectator/> in a browser on the same machine.

The page is served by Roam's embedded REST server, which binds to
`127.0.0.1` only, so it is not reachable from other machines. It polls
`GET /api/v1/snapshot` twice a second.

The game builds the snapshot on its own thread (a `WorldView`, RFC 0017
stage 2) only while something is polling: with `restEnabled: true` and no
spectator open, it does no extra work per tick. While the page is open, the
game builds at most four views a second, covering only the radius asked for. three.js 0.147.0 is loaded from
jsDelivr, so the browser needs an internet connection the first time.

## What it shows

- The rooms the game has **already loaded** within 0 to 3 rooms of the
  player (the "Rooms around player" setting). The spectator never makes the
  game load or generate a room.
- The level the player is on: entering a cave switches the view to that cave
  level.
- Each room's biome is the generator's room type when the game still knows
  it, otherwise it is inferred from the room's contents (room types are not
  saved). On a heavily changed world the inferred biome, and so the terrain
  height, can change; this is cosmetic only.
- Hover (or tap) a tile to see its room, biome, tile and entity stack.

The scene itself is `web/roam3d.js`, which the spectator shares with the browser game's opt-in 3D view (`/play?view=3d`), so the two cannot drift apart.

Cave lighting in the spectator is a viewing convenience: Roam itself has no
ambient light underground.
