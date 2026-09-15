# Codex Sol Orchestrator + Luna Subagents

A configurable Codex setup where GPT-5.6 Sol replaces GPT-6 Astra in the quality-critical orchestrator and reviewer roles, while GPT-5.6 Luna remains the default and pinned model for routine execution subagents.

The installer asks which Codex plan you are on. Pro uses GPT-5.6 Sol at medium reasoning to orchestrate and GPT-5.6 Luna at max reasoning for execution subagents. Plus uses GPT-5.6 Luna at max reasoning to orchestrate and medium reasoning for execution subagents. Both plans use a separate GPT-5.6 Sol reviewer at low reasoning.

## Layout

```text
.
├── profiles/
│   ├── pro/
│   │   ├── codex/           (config.toml and agents/*.toml)
│   │   └── agents/          (skills/sol-orchestrator/SKILL.md)
│   └── plus/
│       ├── codex/           (config.toml and agents/*.toml)
│       └── agents/          (skills/sol-orchestrator/SKILL.md)
├── guides/
│   ├── fast-iteration.md
│   ├── complex-repo-work.md
│   ├── routine-coding.md
│   ├── full-orchestration.md
│   ├── plus-plan.md
│   └── token-usage.md
├── scripts/
│   └── token_usage.py
├── AGENTS.md
├── setup.sh
├── setup.ps1
└── LICENSE
```

## Current Plus and Pro configuration

| Role or setting | Plus | Pro |
|---|---|---|
| Orchestrator | GPT-5.6 Luna — max | GPT-5.6 Sol — medium |
| Explorer, worker, tester, researcher | GPT-5.6 Luna — medium | GPT-5.6 Luna — max |
| Default subagent | GPT-5.6 Luna — medium | GPT-5.6 Luna — max |
| Independent reviewer | GPT-5.6 Sol — low | GPT-5.6 Sol — low |
| Concurrent subagent limit | 4 | 4 |

### Pro — `profiles/pro/codex/config.toml`

```toml
model = "gpt-5.6-sol"
model_reasoning_effort = "medium"

approval_policy = "on-request"
sandbox_mode = "workspace-write"

[agents]
enabled = true
max_concurrent_threads_per_session = 4
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "max"
```

### Plus — `profiles/plus/codex/config.toml`

```toml
model = "gpt-5.6-luna"
model_reasoning_effort = "max"

approval_policy = "on-request"
sandbox_mode = "workspace-write"

[agents]
enabled = true
max_concurrent_threads_per_session = 4
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "medium"
```

The installer copies `profiles/<plan>/codex` to `.codex` and
`profiles/<plan>/agents` to `.agents` in the target repository. Each profile
is ready to copy, with no configuration rewriting during setup.

Each role file is explicitly pinned to its intended model: Luna for explorer, worker, tester, and researcher; Sol for reviewer. This means changing only `default_subagent_model` will affect generic spawned agents, but not the named roles.

The four Luna role files explicitly set `model_reasoning_effort = "max"` in the Pro profile and `"medium"` in the Plus profile. The reviewer keeps its explicit `low` effort in both.

When updating an existing installation, copy the role files along with `config.toml` from the selected profile. Replace `<plan>` below with `pro` or `plus`.

If you previously installed the Astra version, remove the old
`.agents/skills/astra-orchestrator/` directory after checking it for local
changes, and replace any `$astra-orchestrator` or `astra-orchestrator`
references in your existing `AGENTS.md`. The Sol skill has a new directory
name, so copying `.agents` does not overwrite the legacy skill automatically.

If you want all named roles, including the reviewer, to follow the `[agents]` defaults, remove both the `model` and `model_reasoning_effort` overrides from their role files.

## Project setup

Clone this repository:

```bash
git clone https://github.com/itsolver/codex-sol-luna-orchestrator.git
cd codex-sol-luna-orchestrator
```

The target project must already exist and must be different from this setup
repository.

### macOS and Linux

Run the shell installer:

```bash
./setup.sh
```

### Windows

Run the PowerShell installer from Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

With PowerShell 7, you can use:

```powershell
pwsh -File .\setup.ps1
```

### Installer prompts

When asked for the target repository, enter its absolute or relative path. For
example:

```text
Target repository path: ../my-project
```

Next, choose your Codex plan:

```text
Codex plan:
  1) Pro  - GPT-5.6 Sol orchestrates and reviews; GPT-5.6 Luna executes
  2) Plus - GPT-5.6 Luna orchestrates and executes; GPT-5.6 Sol reviews
Select plan [1/2] (default 1):
```

The selected configuration sets both the root and default subagent reasoning.
Agent role files match the selected plan: explorer, worker, tester, and
researcher use Luna at the plan's default effort; the reviewer uses Sol at low
effort on both plans.

The installer then asks whether to install each component:

- `profiles/<plan>/codex` contains the root configuration and agent role profiles, installed as `.codex`.
- `profiles/<plan>/agents` contains the `sol-orchestrator` skill, installed as `.agents`.
- `AGENTS.md` gives Codex the project-level orchestration instructions. If it
  already exists, setup appends the instructions and preserves its contents.
  Re-running setup skips the append when the same instructions are already
  present. Symbolic links and incompatible targets are skipped.

Press Enter or answer `y` to install a component; answer `n` to skip it. All
three components are selected by default.

If a component already exists, the installer lists the exact paths that would
be overwritten and asks again before making changes:

```text
WARNING: the following existing files will be overwritten:
  - .codex/config.toml
Update .codex? New files will be added; only paths listed above will be replaced. [y/N]
```

Existing-file updates default to `n`. If approved, missing files are added and
only the listed paths are replaced. Other files already present in the target
component remain untouched.

After setup, launch Codex from the target repository. Project-scoped `.codex`
configuration is loaded only for trusted projects.

See `guides/` for copy-paste model presets and the Sol + Luna topology. The
guides are intentionally separate from the installers so you can review and
adapt settings for your Codex version without changing a global config
automatically.

## Personal/global setup

For agents, copy the TOML files from `profiles/<plan>/codex/agents/` to:

```text
~/.codex/agents/
```

For the skill, copy `profiles/<plan>/agents/skills/sol-orchestrator/` to:

```text
~/.agents/skills/sol-orchestrator/
```

Merge the settings from `profiles/pro/codex/config.toml` (Pro) or `profiles/plus/codex/config.toml`
(Plus) into your existing:

```text
~/.codex/config.toml
```

Do not blindly overwrite your existing global config if you already have MCP servers, providers, permissions, or other settings.

## Using the skill

Codex may select the skill automatically when the task matches its description.

You can also invoke it explicitly from Codex CLI or the IDE extension with:

```text
$sol-orchestrator
```

Example prompt:

```text
$sol-orchestrator

Implement the new invoice export endpoint.
Have explorer map the existing invoice/export path first.
Use workers for bounded implementation, tester for verification,
and reviewer for an independent final review.
```

## Suggested topology

```text
                 GPT-5.6 Sol
             root / orchestrator
                      |
      +---------------+---------------+
      |               |               |
   explorer          worker         researcher
     Luna             Luna             Luna
      |               |
      +-------+-------+
              |
           tester
            Luna
              |
          reviewer
            Sol
              |
              v
         GPT-5.6 Sol
      integrate + verify
```

## Tuning

For cheaper/faster runs:
- lower Pro's Sol reasoning from `medium` to `low`
- set Luna reasoning to `low` or `medium`
- use 3-4 concurrent threads

For larger codebases:
- consider raising Pro's Sol reasoning to `high`
- start with your plan's Luna default and adjust based on results
- use 6-8 concurrent threads, only when tasks are actually independent

For strict parent/child separation:
- keep explorer/reviewer/researcher read-only
- keep worker/tester workspace-write
- leave the root in workspace-write so it can integrate changes

## Token usage

Orchestration is not free: the root stays in the loop for the whole task and
every subagent carries its own context. Usage depends on repository size and
task shape, so there is no single number. `scripts/token_usage.py` reads the
rollout logs Codex already writes under `~/.codex/sessions` and reports usage
per thread, role, and model, plus the change in your 5-hour and 7-day rate
limit windows:

```bash
scripts/token_usage.py --list --date 2026-09-07
scripts/token_usage.py --latest --date 2026-09-07
```

See [`guides/token-usage.md`](guides/token-usage.md) for a measurement
protocol, one sample run with real numbers, and tips for reducing usage.

Plus users: the root thread is the largest line item, so running it on Luna
saves the most. Selecting `Plus` in the installer does this for you; for a
manual or global setup see [`guides/plus-plan.md`](guides/plus-plan.md):

```toml
# Root
model = "gpt-5.6-luna"
model_reasoning_effort = "max"
```

## Important behavior

Explicit model choices during a spawn override `[agents]` defaults. Custom agent files that specify `model` or `model_reasoning_effort` also take precedence over inherited defaults.

The execution role files are pinned to Luna intentionally, while the reviewer is pinned to Sol for independent final review. Sol remains the Pro orchestrator unless you deliberately change the role configuration.

## License

Licensed under the [Apache License 2.0](LICENSE).
