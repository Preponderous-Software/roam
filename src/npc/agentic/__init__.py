"""Agentic (CPC) NPC behavior, as a pure core behind two ports.

    NpcManager ──► service.createAgenticBehavior()
                         │ wires production adapters
                         ▼
                 core.AgenticBehavior ──uses──► ports.LanguageModel ◄── adapters.AnthropicLanguageModel
                  (prompt, world state,  ──uses──► ports.BackgroundRunner ◄── adapters.DaemonThreadRunner
                   plan parsing, actions)
                         │ no model (None)
                         ▼
                 npc.programmaticBehavior.ProgrammaticBehavior

Dependencies point inward: `model`, `core` and `ports` never import
`adapters` or `service` (tests/npc/agentic/test_architecture.py enforces it).

| Port             | Production adapter       | Test fake                         |
|------------------|--------------------------|-----------------------------------|
| LanguageModel    | AnthropicLanguageModel   | FakeLanguageModel (tests/npc)     |
| BackgroundRunner | DaemonThreadRunner       | InlineRunner (tests/npc)          |

To add another model provider (e.g. a self-hosted one): add one file in
`adapters/` implementing `LanguageModel.complete`, then pass it to
`createAgenticBehavior(model=...)` or make it the default in `service.py`.
"""
