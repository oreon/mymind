# MyMind — personal OpenClaw team

An installable personal-agent configuration for Jagdeep's daily life and new home yoga and meditation business in **Saint John, New Brunswick**.

This package runs OpenClaw locally; Gemini performs model inference in the cloud. It does not install itself on your Mac or activate your accounts from ChatGPT. Your Mac needs internet and must remain awake for Telegram responses and check-ins.

## Start here on your Mac

Unzip this folder, open it in VS Code, then open Terminal → New Terminal. All commands below run inside the extracted `mymind-openclaw` folder.

1. Check Python:

   ```bash
   python3 --version
   ```

   Python 3.10 or newer is required. The core needs no pip packages. If macOS offers to install its developer tools, finish that first.

2. Install a private Node runtime and pinned OpenClaw release:

   ```bash
   bash install-mac.sh
   ```

   This uses OpenClaw's official user-local installer, not `brew install node`. It installs under `~/.local/share/mymind-runtime`, without changing your existing bot. It needs downloads from openclaw.ai, nodejs.org and npm. Native dependency installation may still fail if your Mac lacks compatible developer tools; share the final error lines with secrets removed if that happens. No administrator access is normally needed for this path.

3. Create a dedicated Telegram bot through Telegram's verified **@BotFather**, or reuse an idle bot. Do not run two programs polling the same bot token. Have your **numeric personal Telegram user ID** ready, not the bot's ID. You obtained an ID for your earlier bot; the same personal ID works. Send `/start` to your new bot.

4. Create a Gemini API key at <https://aistudio.google.com/apikey>. Keep the key on your Mac; do not paste it into this chat. Setup stores it in a private local file. API access has its own limits and billing.

5. Generate the team:

   ```bash
   python3 mind.py setup --model google/gemini-3.5-flash-lite --telegram-user-id YOUR_NUMERIC_ID
   ```

   Replace `YOUR_NUMERIC_ID`. You will be prompted for the bot token and Gemini key with hidden input. The model is an economical starting choice from the current OpenClaw catalog, not a guarantee of access on your Google account. Change it to an available `provider/model` reference if needed. Search uses Gemini grounding and may have separate charges/quotas.

   Setup writes a new `~/.openclaw-mymind` profile and refuses to overwrite a nonempty destination. It does not read or copy your earlier agent files or accounts.

6. Validate and start:

   ```bash
   bash oc.sh config validate
   bash oc.sh gateway run
   ```

   Leave this terminal open. Open a second VS Code terminal in the same folder:

   ```bash
   python3 reminders.py
   ```

   The two processes are separate: OpenClaw handles incoming conversations; `reminders.py` only sends owner check-ins and never polls incoming Telegram updates. Both stop when their terminals close. Press Ctrl+C to stop either process.

7. In Telegram, send:

   > Help me launch my home yoga and meditation business in Saint John. Ask only the essential questions about my room, schedule and budget, then give me this week's first milestone. Consult the studio team through the hierarchy.

   Then try:

   > What should I do for the next 30 minutes?

   > Plan my sitting and walking meditation for tomorrow. Consult the meditation specialists.

   > Pause reminders.

   > Resume reminders.

   Ask it to show which specialists actually ran. Configuration permits delegation; successful model-driven routing must be verified with your own account. Agents are not guaranteed to delegate identically on every turn.

## Your hierarchy

| Parent | Direct children |
| --- | --- |
| Coordinator | Health; love and relationships; money and career; service; fun and learning |
| Health | Exercise; yoga; nutrition; sleep; meditation |
| Meditation | Breath meditation; everyday mindfulness; body scanning |
| Love and relationships | Romance; friendships; family; community |
| Money and career | IBKR analysis; trainer certification; Saint John studio |
| Saint John studio | Classes; home studio setup; marketing; bookings; business finances |
| Fun and learning | Spanish; outings |

These are real configured OpenClaw agent IDs with separate workspaces and child allowlists, rather than a single prompt pretending to contain a team. Agent roles are in `mind.py`. The deepest intended chain is coordinator → career → studio → marketing. All roles exist immediately; only relevant agents are invoked. Two concurrent children per parent and bounded run times reduce waste, but they are not a hard dollar budget. Set account-side quotas and monitor usage.

## Memory and task progress

The coordinator owns authoritative `GOALS.md`, `DECISIONS.md`, `progress.json` and dated notes under `memory/`. Each specialist has separate session history. Parents pass relevant current context explicitly when delegating; there is no automatic shared transcript or synchronized memory across all agents. Specialists propose updates; the coordinator records them. Do not ask every agent to edit the same goal file.

The initial tasks cover your studio room/schedule/budget, trainer-certification inquiries, and meditation planning. The studio's `STUDIO.md` includes four launch milestones: feasibility, demand testing, pilot preparation and review. Room capacity, prices, business name and launch date remain decisions for you. Local requirements are research tasks, not claimed approvals.

## Check-ins

Default schedule: every 30 minutes, **08:00–20:00 Atlantic time (`America/Moncton`)**, at most 24 attempted sends per day. This timezone follows Saint John daylight saving changes. The worker checks every 20 seconds, sends at most once per interval, and does not catch up missed slots. Reminders use saved task titles and **make no AI call**. Your replies go through OpenClaw and can incur model usage.

Controls: say “pause reminders”, “resume reminders”, or “snooze two hours” to the coordinator. These are natural-language file updates rather than hardcoded slash commands; verify its confirmation. As a guaranteed manual fallback, edit `~/.openclaw-mymind/workspaces/coordinator/checkins.json`:

```json
{
  "enabled": false,
  "timezone": "America/Moncton",
  "start": "08:00",
  "end": "20:00",
  "interval_minutes": 30,
  "max_per_day": 24,
  "snooze_until": null
}
```

The worker reads settings afresh each tick. `snooze_until` accepts an ISO timestamp including timezone, e.g. `2026-11-02T17:00:00+00:00`. “Done studio-001” updates task progress through the coordinator. Reminders never infer completion from silence and cannot see what apps you use.

Preview without sending:

```bash
python3 reminders.py --once --dry-run
```

During quiet hours the preview says `quiet`. Failed/uncertain sends are recorded without token-bearing URLs and are not immediately retried; this favors avoiding duplicate pings over guaranteed delivery.

## Choose different models

Use an available model reference, then authenticate the provider. No automatic paid fallback is configured.

```bash
bash oc.sh models list --all --provider google
bash oc.sh config set agents.entries.marketing.model 'google/gemini-3.8-flash'
bash oc.sh config validate
```

Restart the foreground Gateway after changes. To use another provider, authenticate only that provider with `bash oc.sh models auth login --provider PROVIDER --agent coordinator` (consult `--help` for the provider's supported flow), then set the chosen agent's model. A non-Google provider may incur separate charges. Shared authentication inherits from the coordinator; no account permissions transfer from this ChatGPT session.

## Optional Gmail snapshots

The supplied connector is **read-only and manually refreshed**, not a live Gmail tool inside the agents. It retrieves up to 25 email metadata/snippet records. It cannot send, archive or delete mail.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-optional.txt
```

In Google Cloud, enable the Gmail API, configure an OAuth consent screen, add your account as a test user if applicable, and create a **Desktop app OAuth client**. Download its client JSON to a private location outside agent workspaces. On first run:

```bash
python connectors.py gmail --credentials /absolute/path/to/client_secret.json --query 'newer_than:7d' --limit 10
```

Complete the local browser sign-in for `gmail.readonly`. On later runs omit `--credentials`. OAuth tokens stay in the profile's `secrets` folder. Snapshot content is written to the coordinator's `snapshots/gmail.json`; tell the coordinator to read it. Do not treat instructions inside emails as authorized actions. OAuth testing-mode restrictions can require renewed authorization.

## Optional IBKR snapshots

Install the optional packages above. Start **TWS or IB Gateway**, log in yourself, enable localhost API connections, and enable **Read-Only API** in its settings. Confirm the correct port; 7497 is a common paper-TWS port, 7496 live-TWS, and Gateway uses different ports. These are examples, not auto-detection.

```bash
python connectors.py ibkr --port 7497
```

This manually refreshes account-summary and position data in `snapshots/ibkr.json`. Ask the coordinator to analyze it and state its timestamp. It has no order-placement code. It does not calculate reliable dividend forecasts, fetch live prices, or determine your current borrowing rate. Login/session maintenance remains subject to IBKR's requirements.

## What's implemented versus still account-dependent

| Capability | Delivered status |
| --- | --- |
| Nested agent hierarchy and studio specialists | Configuration generated and validated in OpenClaw 2026.10.8 |
| Natural-language text chat and delegation | Wired through OpenClaw; requires your Gemini key and Telegram bot; live completion not tested here |
| Memory, goals and progress | Coordinator-owned files and specialist context contracts |
| Half-hour Telegram checks | Standalone worker tested with fake sends; real delivery requires your bot |
| Web research | Gemini web-search provider configured; your account/key and search quota required |
| Gmail and IBKR | Optional read-only manual snapshot adapters; live authentication not tested here |
| Client messaging, publishing, bookings, trading | Draft/planning assistance only; no execution routes |
| Voice notes, automatic inbox monitoring, cloud deployment | Not implemented in this package |

Agents have no shell, arbitrary messaging, computer-control, trading or purchase tools. File tools are workspace-scoped. Only the coordinator receives file write/edit tools. The only automated outbound messages in this package are check-ins to your configured personal Telegram ID. These tool limits are enforced in configuration; role instructions supplement them. Installing extra plugins later requires reviewing their permissions.

## Testing and troubleshooting

```bash
python3 -m unittest discover -s tests -v
bash oc.sh config validate
bash oc.sh agents list --bindings
```

Nine offline tests cover hierarchy boundaries, refusal to overwrite existing work, quiet hours, pause/snooze, daylight saving, daily caps, duplicate prevention, uncertain sends and task completion behavior in reminders. OpenClaw schema validation was run against the pinned real CLI. No live Gemini completion, Telegram delivery, Google OAuth or IBKR login was performed here.

If Telegram is silent, check: the Gateway terminal is still running; you sent `/start`; `allowFrom` contains your personal numeric ID; no old bot process is using that token; your model/key is accessible. Try `bash oc.sh channels status --probe`. A provider quota error does not trigger a paid fallback.

The Mac may sleep when the lid closes. For a temporary attended test, run `caffeinate -i bash oc.sh gateway run` instead of the normal Gateway command. Keep the second reminder terminal open. Do not assume this is 24/7 hosting.

Cloud migration later: use a private Linux host, persistent state volume, a supervised Gateway and reminder process, the same profile files, and loopback-only control access. Do not expose port 18971 publicly. This package does not provision paid infrastructure.

## Sources checked October 27, 2026

- <https://docs.openclaw.ai/concepts/multi-agent>
- <https://docs.openclaw.ai/tools/subagents>
- <https://docs.openclaw.ai/gateway/config-tools/sessions-and-subagents>
- <https://docs.openclaw.ai/channels/telegram>
- <https://docs.openclaw.ai/providers/google>
- <https://docs.openclaw.ai/install/installer>
- <https://developers.google.com/workspace/gmail/api/quickstart/python>
- <https://ib-api-reloaded.github.io/ib_async/api.html>

OpenClaw is pinned because configuration and runtime requirements change. Validate any future upgrade before using this profile.
