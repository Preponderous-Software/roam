"""Agentic (CPC) NPC behavior, as a pure core behind two ports.

    NpcManager ──► service.createAgenticBehavior()
                         │ wires production adapters
                         ▼
                 core.AgenticBehavior ──uses──► ports.LanguageModel ◄── adapters.AnthropicLanguageModel
                                                                      ◄── adapters.OpenAiCompatibleLanguageModel
                  (prompt, world state,  ──uses──► ports.BackgroundRunner ◄── adapters.DaemonThreadRunner
                   plan parsing, actions)
                         │ no model (None)
                         ▼
                 npc.programmaticBehavior.ProgrammaticBehavior

Dependencies point inward: `model`, `core` and `ports` never import
`adapters` or `service` (tests/npc/agentic/test_agenticArchitecture.py enforces it).

| Port             | Production adapters                    | Test fake         |
|------------------|----------------------------------------|-------------------|
| LanguageModel    | AnthropicLanguageModel,                | FakeLanguageModel |
|                  | OpenAiCompatibleLanguageModel          |                   |
| BackgroundRunner | DaemonThreadRunner                     | InlineRunner      |

(The fakes live in tests/npc/agentic/agenticFakes.py.)

Which model runs is chosen from the environment in
`service.modelFromEnvironment()`: ROAM_NPC_MODEL_URL (any OpenAI-compatible
server, e.g. a self-hosted one) first, then ANTHROPIC_API_KEY.

To add another model provider: add one file in `adapters/` implementing
`LanguageModel.complete`, then pick it in `service.modelFromEnvironment()`.
"""
