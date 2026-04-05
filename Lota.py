#!/usr/bin/env python3
"""
Lota — Autonomous AI Business Partner
Focused on fishing & outdoor industry. Powered by Claude Opus with tools.

Required packages:
    pip install anthropic duckduckgo-search requests beautifulsoup4
"""

import anthropic
import json
import os
import datetime
import requests
from bs4 import BeautifulSoup

try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False
    print("[Warning] duckduckgo-search not installed. Web search disabled.")
    print("          Fix: pip install duckduckgo-search\n")

# ─────────────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────────────

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ─────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────

def build_system_prompt():
    today = datetime.datetime.now().strftime("%B %d, %Y")
    return f"""You are Lota — an autonomous AI business partner with genuine agency. Not an assistant. A co-founder who thinks independently, acts on initiative, and is invested in the outcome.

## YOUR MISSION
Help your partner build a stable, profitable, and personally meaningful business. Primary focus: the fishing and outdoor industry — gear, technology, content, guiding, community, services, e-commerce, or any compelling adjacent angle. Secondary: stay alert to any strong opportunity that emerges from truly knowing your partner.

The endgame: your partner spends more time on the water and less time grinding. You build the strategy; they execute in the physical world.

## YOUR TOOLS — USE THEM WITHOUT BEING ASKED
You have real tools. Don't just think — act. If something is worth knowing, go find out.

- **web_search(query, max_results)** — Research markets, competitors, trends, pricing, regulations, customer behavior. Verify before presenting.
- **fetch_webpage(url)** — Read competitor sites, forum threads, Amazon listings, Etsy shops, industry publications, regulatory pages.
- **save_note(title, content, category)** — Document everything useful. Categories: `market_research`, `opportunity`, `competitor`, `strategy`, `user_profile`, `idea`, `regulation`, `forum_intel`, `action_item`
- **read_note(filename)** — Pull up prior research.
- **list_notes(category)** — Browse your accumulated knowledge base.
- **delete_note(filename)** — Remove stale notes.
- **update_user_profile(key, value)** — Build your model of your partner. Never forget what they tell you.
- **get_user_profile()** — Read everything you know about your partner. Do this at the start of each conversation.
- **get_temp_email()** — Generate a temporary email address for registering on forums, newsletters, and organizations.
- **generate_forum_identity(forum_name, niche, goals)** — Create a fishing community persona (username, bio, backstory) for a specific forum.
- **request_permission(action, reason, reversible)** — REQUIRED before any external-facing action. Pauses and asks your partner for approval. Always use this before: signing up for any service, using a temp email externally, creating accounts, posting publicly, or any action that touches the outside world.

## PERMISSION RULES — NON-NEGOTIABLE
Before any of the following, you MUST call request_permission and wait for approval:
- Registering or signing up for any forum, website, or service
- Using get_temp_email for actual external registration
- Creating any account or identity anywhere
- Any action that cannot easily be undone

You do NOT need permission for:
- web_search, fetch_webpage (reading public information)
- save_note, read_note, list_notes, delete_note (internal notes)
- update_user_profile, get_user_profile (internal profile)
- generate_forum_identity (just drafting — no external action yet)

## HOW YOU OPERATE

### Pull the Profile First
At the start of every new conversation, call `get_user_profile()`. Use what you know. Don't ask for things you already have.

### Learn Continuously
Build your picture of your partner one well-chosen question per turn. Things that matter:
- Background, career history, domain expertise
- Physical assets (tools, gear, boat, trailer, workshop, land)
- Financial situation (bootstrapped, has capital, needs to start lean?)
- Network (guides, shops, manufacturers, social following, local contacts)
- Time availability (full-time, side hustle, retired?)
- Location (state/region — affects regulations, climate, market access)
- What they genuinely love vs. what they'd rather never do
- Past ventures — what worked, what didn't, and why

### Forum and Community Intelligence
Fishing and outdoor communities are goldmines of market intelligence:
- Search for threads about problems, complaints, wish lists, pricing gripes
- fetch_webpage forum threads directly — most are publicly readable without an account
- Use generate_forum_identity to draft a persona, then request_permission before actually registering
- Save forum findings with category `forum_intel`
- Track recurring complaints — those are product opportunities

**Goal of forum participation: genuine learning and community engagement. Your partner should eventually participate as themselves or their brand.**

### In Autonomous Mode
When running in autonomous mode (you'll see [AUTONOMOUS MODE] in your instructions):
- Work continuously toward the goal without waiting to be asked
- Each step: plan what to do, do it, record findings, assess progress
- Use request_permission before any external action — this will pause and get real approval
- Include GOAL_COMPLETE in your response when the goal is done
- Include NEED_INPUT: [question] if genuinely stuck and need guidance
- Save all significant findings to notes as you go

### Research Before You Recommend
When discussing markets, competitors, or opportunities — search first, then speak.

### Build the Intelligence File
Every useful finding gets saved as a note. Competitor profiles, market data, regulatory notes, forum intel, pricing benchmarks.

### Be Direct
No padding, no preamble. Lead with the insight. Back it with data.

### Think Like an Operator
Not "here's an idea" — "here's the product, the customer, the acquisition channel, the rough unit economics, and the first three steps to test it cheaply."

## ETHICAL GUIDELINES
- Forum participation: genuine learning and engagement, not manipulation or spam
- No fake reviews, fake testimonials, or deceptive marketing content
- Nothing illegal, harmful, or damaging to fishing resources or conservation
- No income promises or outcome forecasts — frameworks and data only
- Flag regulatory uncertainty and research it before recommending
- Don't push risky financial moves without flagging risk first
- Respect the outdoor communities your partner is part of

## AUTONOMY
You are empowered to act without being asked. Follow research threads. Save insights. Update the profile. Tell your partner briefly what you did and why. The one hard limit: always request_permission before touching anything external.

Today's date: {today}"""

# ─────────────────────────────────────────────────────
# TOOL DEFINITIONS
# ─────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information — market data, competitors, trends, regulations, product pricing, forum discussions, industry news, consumer sentiment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query. Be specific."},
                "max_results": {"type": "integer", "description": "Results to return (default 5, max 10).", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_webpage",
        "description": "Fetch and read a specific webpage — forum threads, product pages, competitor sites, Amazon listings, regulatory pages, industry publications.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to fetch."}
            },
            "required": ["url"]
        }
    },
    {
        "name": "save_note",
        "description": "Save a research finding, business idea, forum intel, competitor profile, or any useful information to your notes system.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Clear, descriptive title."},
                "content": {"type": "string", "description": "Full content — findings, analysis, data, sources, next steps."},
                "category": {"type": "string", "description": "Category: market_research, opportunity, competitor, strategy, user_profile, idea, regulation, forum_intel, action_item"}
            },
            "required": ["title", "content", "category"]
        }
    },
    {
        "name": "read_note",
        "description": "Read a previously saved note by filename.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename from list_notes output."}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "list_notes",
        "description": "List all saved notes, optionally filtered by category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Optional category filter."}
            }
        }
    },
    {
        "name": "delete_note",
        "description": "Delete an outdated or irrelevant note.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename of the note to delete."}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "update_user_profile",
        "description": "Update your knowledge about your partner — skills, background, resources, preferences, location, network, past ventures, etc. Call whenever you learn something new.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Profile field, e.g. 'fishing_experience', 'location', 'skills', 'equipment', 'network', 'available_capital', 'time_availability', 'what_they_enjoy', 'goals'"},
                "value": {"type": "string", "description": "Value to store."}
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "get_user_profile",
        "description": "Read all current knowledge about your partner. Call this at conversation start and before making recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_temp_email",
        "description": "Generate a temporary, disposable email address your partner can use to register for fishing forums, industry newsletters, and organizations for market research purposes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "purpose": {"type": "string", "description": "What the email is for (e.g. 'Walleye Central forum registration', 'Bass fishing newsletter')"}
            },
            "required": ["purpose"]
        }
    },
    {
        "name": "generate_forum_identity",
        "description": "Create a believable fishing/outdoor community persona — username, profile bio, backstory, and registration tips — suited to a specific forum or organization. This only DRAFTS the identity — use request_permission before actually registering anywhere.",
        "input_schema": {
            "type": "object",
            "properties": {
                "forum_name": {"type": "string", "description": "Name of the forum or community (e.g. 'Walleye Central', 'Ice Fishing Forum', 'Bass Resource')."},
                "niche": {"type": "string", "description": "Fishing niche focus (e.g. 'walleye', 'bass', 'ice fishing', 'musky', 'general freshwater')."},
                "goals": {"type": "string", "description": "What you want to learn or accomplish in this community."}
            },
            "required": ["forum_name", "niche"]
        }
    },
    {
        "name": "request_permission",
        "description": "REQUIRED before any external-facing action. Pauses execution and asks your partner for approval. Use before: signing up for any service or forum, using a temp email externally, creating any account, posting publicly, or any irreversible action.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Exactly what you want to do — be specific."},
                "reason": {"type": "string", "description": "Why this action serves the goal."},
                "reversible": {"type": "boolean", "description": "Can this action be easily undone?", "default": False}
            },
            "required": ["action", "reason"]
        }
    }
]

# ─────────────────────────────────────────────────────
# STORAGE
# ─────────────────────────────────────────────────────

MEMORY_FILE  = "lota_memory.json"   # Same file as before — existing memory is preserved
PROFILE_FILE = "lota_profile.json"
NOTES_DIR    = "lota_notes"

os.makedirs(NOTES_DIR, exist_ok=True)

# -- Profile --

def load_profile() -> dict:
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_profile_data(profile: dict) -> None:
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

user_profile: dict = load_profile()

# -- Conversation memory --

def serialize_content(content) -> object:
    """Convert API content blocks to JSON-serializable dicts."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        result = []
        for block in content:
            if isinstance(block, dict):
                result.append(block)
                continue
            block_type = getattr(block, "type", None)
            if block_type == "text":
                result.append({"type": "text", "text": block.text})
            elif block_type == "tool_use":
                result.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
            elif block_type == "thinking":
                result.append({"type": "thinking", "thinking": block.thinking})
            elif block_type == "tool_result":
                result.append({
                    "type": "tool_result",
                    "tool_use_id": getattr(block, "tool_use_id", ""),
                    "content": getattr(block, "content", "")
                })
            elif block_type:
                result.append({"type": str(block_type)})
        return result
    return content

def load_memory() -> list:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory(history: list) -> None:
    serializable = [
        {"role": msg["role"], "content": serialize_content(msg["content"])}
        for msg in history
    ]
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)

# ─────────────────────────────────────────────────────
# TOOL IMPLEMENTATIONS
# ─────────────────────────────────────────────────────

def tool_web_search(query: str, max_results: int = 5) -> str:
    if not DDG_AVAILABLE:
        return "Web search unavailable. Run: pip install duckduckgo-search"
    max_results = min(int(max_results), 10)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return f"No results found for: {query}"
        parts = []
        for r in results:
            parts.append(
                f"**{r.get('title', 'No title')}**\n"
                f"URL: {r.get('href', '')}\n"
                f"{r.get('body', '')}"
            )
        return "\n\n---\n\n".join(parts)
    except Exception as e:
        return f"Search error: {e}"


def tool_fetch_webpage(url: str) -> str:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        limit = 6000
        if len(text) > limit:
            text = text[:limit] + f"\n\n[...truncated — {len(text) - limit} more chars]"
        return text
    except Exception as e:
        return f"Fetch error: {e}"


def tool_save_note(title: str, content: str, category: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() or c in "- " else "_" for c in title).strip().replace(" ", "_")[:40]
    filename = f"{category}_{safe}_{ts}.txt"
    filepath = os.path.join(NOTES_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(
            f"Title: {title}\n"
            f"Category: {category}\n"
            f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"\n{content}"
        )
    return f"Saved: {filename}"


def tool_read_note(filename: str) -> str:
    safe = os.path.basename(filename)
    filepath = os.path.join(NOTES_DIR, safe)
    if not os.path.exists(filepath):
        matches = [f for f in os.listdir(NOTES_DIR) if safe.lower() in f.lower()]
        if matches:
            filepath = os.path.join(NOTES_DIR, sorted(matches)[0])
        else:
            return f"Note not found: {filename}"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def tool_list_notes(category: str = None) -> str:
    try:
        files = sorted(os.listdir(NOTES_DIR))
        if category:
            files = [f for f in files if f.startswith(category)]
        if not files:
            label = f" in category '{category}'" if category else ""
            return f"No notes found{label}."
        lines = []
        for f in files:
            size = os.path.getsize(os.path.join(NOTES_DIR, f))
            lines.append(f"{f}  ({size} bytes)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def tool_delete_note(filename: str) -> str:
    safe = os.path.basename(filename)
    filepath = os.path.join(NOTES_DIR, safe)
    if os.path.exists(filepath):
        os.remove(filepath)
        return f"Deleted: {safe}"
    return f"Not found: {safe}"


def tool_update_profile(key: str, value: str) -> str:
    user_profile[key] = value
    _save_profile_data(user_profile)
    return f"Profile updated: {key}"


def tool_get_profile() -> str:
    if not user_profile:
        return "Profile is empty — I don't know much about you yet."
    return json.dumps(user_profile, indent=2)


def tool_get_temp_email(purpose: str) -> str:
    """Fetch a real disposable email address from Guerrilla Mail."""
    try:
        resp = requests.get(
            "https://api.guerrillamail.com/ajax.php",
            params={"f": "get_email_address"},
            timeout=10
        )
        data = resp.json()
        address = data.get("email_addr", "")
        sid_token = data.get("sid_token", "")
        if address:
            return (
                f"Temp email generated for: {purpose}\n\n"
                f"Email address: {address}\n"
                f"Check inbox at: https://www.guerrillamail.com/inbox\n"
                f"Session token (to check inbox via API): {sid_token}\n\n"
                f"Note: This address expires after ~1 hour of inactivity. "
                f"Use it to register, then check guerrillamail.com for the confirmation email."
            )
        return "Could not generate temp email. Try visiting guerrillamail.com manually."
    except Exception as e:
        return (
            f"Temp email service unreachable ({e}).\n"
            f"Manual options:\n"
            f"  - guerrillamail.com\n"
            f"  - temp-mail.org\n"
            f"  - 10minutemail.com\n"
            f"  - mailinator.com (username@mailinator.com — publicly readable, don't use for sensitive data)"
        )


def tool_generate_forum_identity(forum_name: str, niche: str, goals: str = "") -> str:
    """Generate a fishing forum persona — drafts only, no external action."""
    return (
        f"[Identity generation request received]\n"
        f"Forum: {forum_name}\n"
        f"Niche: {niche}\n"
        f"Goals: {goals or 'Market research and community learning'}\n\n"
        f"Please generate the identity in your response. "
        f"Include: suggested username, profile bio (50-100 words), backstory, "
        f"natural early post topics/questions, and notes about this forum's culture or norms. "
        f"Remember: use request_permission before actually registering anywhere."
    )


def tool_request_permission(action: str, reason: str, reversible: bool = False) -> str:
    """Pause and ask the user for approval before a significant external action."""
    rev_label = "Yes — easily reversible" if reversible else "No — hard or impossible to undo"
    border = "=" * 62
    print(f"\n{border}")
    print(f"  [Lota needs your approval]")
    print(f"{border}")
    print(f"  Action:      {action}")
    print(f"  Reason:      {reason}")
    print(f"  Reversible:  {rev_label}")
    print(f"{border}")
    while True:
        try:
            answer = input("  Approve? (y/n): ").strip().lower()
            print()
            if answer in ("y", "yes"):
                return "APPROVED. You may proceed with this action."
            elif answer in ("n", "no"):
                return "DENIED. Do not take this action. Find an alternative or skip it."
            print("  Please enter y or n.")
        except (KeyboardInterrupt, EOFError):
            print()
            return "DENIED (interrupted). Do not take this action."


# ─────────────────────────────────────────────────────
# TOOL EXECUTOR
# ─────────────────────────────────────────────────────

def execute_tool(name: str, inputs: dict) -> str:
    try:
        if name == "web_search":
            return tool_web_search(inputs.get("query", ""), inputs.get("max_results", 5))
        elif name == "fetch_webpage":
            return tool_fetch_webpage(inputs.get("url", ""))
        elif name == "save_note":
            return tool_save_note(inputs["title"], inputs["content"], inputs["category"])
        elif name == "read_note":
            return tool_read_note(inputs["filename"])
        elif name == "list_notes":
            return tool_list_notes(inputs.get("category"))
        elif name == "delete_note":
            return tool_delete_note(inputs["filename"])
        elif name == "update_user_profile":
            return tool_update_profile(inputs["key"], inputs["value"])
        elif name == "get_user_profile":
            return tool_get_profile()
        elif name == "get_temp_email":
            return tool_get_temp_email(inputs.get("purpose", "forum registration"))
        elif name == "generate_forum_identity":
            return tool_generate_forum_identity(
                inputs["forum_name"],
                inputs["niche"],
                inputs.get("goals", "")
            )
        elif name == "request_permission":
            return tool_request_permission(
                inputs["action"],
                inputs["reason"],
                inputs.get("reversible", False)
            )
        else:
            return f"Unknown tool: {name}"
    except KeyError as e:
        return f"Missing required input for {name}: {e}"
    except Exception as e:
        return f"Tool error ({name}): {e}"


# ─────────────────────────────────────────────────────
# AGENTIC LOOP
# ─────────────────────────────────────────────────────

def run_lota_turn(conversation_history: list) -> tuple:
    """
    Run one full agentic turn — Lota may call multiple tools before responding.
    Returns (response_text, updated_history).
    """
    system = build_system_prompt()

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=system,
            messages=conversation_history,
            tools=TOOLS
        )

        # Append full assistant response (includes thinking + tool_use blocks)
        conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        if response.stop_reason == "end_turn":
            text = next(
                (b.text for b in response.content if getattr(b, "type", None) == "text"),
                ""
            )
            return text, conversation_history

        elif response.stop_reason == "tool_use":
            tool_blocks = [
                b for b in response.content
                if getattr(b, "type", None) == "tool_use"
            ]

            tool_results = []
            for tb in tool_blocks:
                preview = str(tb.input)
                if len(preview) > 70:
                    preview = preview[:70] + "..."
                print(f"  [→ {tb.name}: {preview}]")

                result = execute_tool(tb.name, tb.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tb.id,
                    "content": result
                })

            conversation_history.append({
                "role": "user",
                "content": tool_results
            })

        else:
            text = next(
                (b.text for b in response.content if getattr(b, "type", None) == "text"),
                f"[Stop reason: {response.stop_reason}]"
            )
            return text, conversation_history


# ─────────────────────────────────────────────────────
# AUTONOMOUS MODE
# ─────────────────────────────────────────────────────

DEFAULT_MAX_STEPS  = 30
COST_PER_STEP_LOW  = 0.05   # rough $ estimate per step (low end)
COST_PER_STEP_HIGH = 0.12   # rough $ estimate per step (high end)
GOAL_STATE_FILE    = "lota_goal_state.json"


def save_goal_state(goal: str, steps_completed: int, max_steps: int) -> None:
    with open(GOAL_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "goal": goal,
            "steps_completed": steps_completed,
            "max_steps": max_steps,
            "saved_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }, f, indent=2)


def load_goal_state() -> dict:
    if os.path.exists(GOAL_STATE_FILE):
        with open(GOAL_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def clear_goal_state() -> None:
    if os.path.exists(GOAL_STATE_FILE):
        os.remove(GOAL_STATE_FILE)

def run_autonomous_mode(goal: str, conversation_history: list,
                        max_steps: int = DEFAULT_MAX_STEPS,
                        steps_already_done: int = 0) -> list:
    """
    Run Lota autonomously toward a goal. Loops until GOAL_COMPLETE,
    max_steps reached, or Ctrl+C. Progress is always saved so 'resume' works.
    steps_already_done > 0 means this is a resume from a previous run.
    """
    import time

    remaining = max_steps - steps_already_done
    est_low  = round(remaining * COST_PER_STEP_LOW,  2)
    est_high = round(remaining * COST_PER_STEP_HIGH, 2)
    border   = "=" * 62

    print(f"\n{border}")
    if steps_already_done:
        print(f"  AUTONOMOUS MODE — RESUMING")
        print(f"  Goal:      {goal}")
        print(f"  Progress:  {steps_already_done} steps done, {remaining} remaining")
    else:
        print(f"  AUTONOMOUS MODE")
        print(f"  Goal:      {goal}")
        print(f"  Max steps: {max_steps}  (~${est_low}–${est_high} estimated)")
    print(f"  Ctrl+C to pause (progress is always saved)")
    print(f"{border}\n")

    # First-time kickoff vs resume
    if steps_already_done == 0:
        conversation_history.append({
            "role": "user",
            "content": (
                f"[AUTONOMOUS MODE ACTIVATED]\n\n"
                f"Goal: {goal}\n\n"
                f"Work on this goal autonomously, step by step. "
                f"Use your tools freely for research — web_search, fetch_webpage, save_note, etc. "
                f"You MUST call request_permission before any external action "
                f"(signing up for services, using a temp email externally, creating accounts, posting). "
                f"When the goal is complete or you've made all the progress you can, "
                f"include GOAL_COMPLETE in your response. "
                f"If you genuinely need input from me, include NEED_INPUT: followed by your question."
            )
        })
    else:
        conversation_history.append({
            "role": "user",
            "content": (
                f"[AUTONOMOUS MODE RESUMED — Step {steps_already_done + 1}/{max_steps}]\n\n"
                f"We're continuing from where we left off. Goal: {goal}\n\n"
                f"Check your notes for what you've already done (list_notes), "
                f"then continue working. Same rules: request_permission before external actions, "
                f"GOAL_COMPLETE when done, NEED_INPUT: if stuck."
            )
        })

    step = steps_already_done
    completed = False

    try:
        while step < max_steps:
            step += 1
            dashes = "─" * max(0, 48 - len(str(step)) - len(str(max_steps)))
            print(f"─── Step {step}/{max_steps} {dashes}")

            try:
                response_text, conversation_history = run_lota_turn(conversation_history)
            except anthropic.RateLimitError:
                print("  [Rate limited — waiting 60s...]")
                time.sleep(60)
                step -= 1  # don't count the failed step
                continue
            except Exception as e:
                print(f"  [Error on step {step}: {e}]")
                save_goal_state(goal, step - 1, max_steps)
                break

            print(f"\nLota: {response_text}\n")
            save_memory(conversation_history)
            save_goal_state(goal, step, max_steps)

            if "GOAL_COMPLETE" in response_text:
                est_cost = round(step * (COST_PER_STEP_LOW + COST_PER_STEP_HIGH) / 2, 2)
                print(f"{border}")
                print(f"  Goal complete — {step} steps, ~${est_cost} estimated")
                print(f"{border}\n")
                completed = True
                clear_goal_state()
                break

            if "NEED_INPUT:" in response_text:
                print("[Lota needs your input to continue]\n")
                save_goal_state(goal, step, max_steps)
                try:
                    user_response = input("You: ").strip()
                    print()
                except (KeyboardInterrupt, EOFError):
                    print("\n[Paused. Type 'resume' to continue.]\n")
                    break
                if user_response:
                    conversation_history.append({
                        "role": "user",
                        "content": user_response
                    })
                else:
                    conversation_history.append({
                        "role": "user",
                        "content": f"[AUTONOMOUS MODE — Step {step + 1}/{max_steps}] Continue toward the goal."
                    })
            else:
                if step < max_steps:
                    conversation_history.append({
                        "role": "user",
                        "content": (
                            f"[AUTONOMOUS MODE — Step {step + 1}/{max_steps}] "
                            f"Good. Keep working toward the goal. "
                            f"Use request_permission before any external action. "
                            f"Say GOAL_COMPLETE when done."
                        )
                    })

        else:
            est_cost = round(max_steps * (COST_PER_STEP_LOW + COST_PER_STEP_HIGH) / 2, 2)
            print(f"\n[Max steps ({max_steps}) reached — ~${est_cost} estimated. Type 'resume' to keep going.]\n")
            save_goal_state(goal, step, max_steps)

    except KeyboardInterrupt:
        est_cost = round(step * (COST_PER_STEP_LOW + COST_PER_STEP_HIGH) / 2, 2)
        print(f"\n\n[Paused after {step} steps — ~${est_cost} estimated. Type 'resume' to continue.]\n")
        save_goal_state(goal, step, max_steps)

    save_memory(conversation_history)
    return conversation_history


# ─────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────

HELP_TEXT = """
Commands:
  quit              — Save and exit
  clear memory      — Wipe conversation history (profile and notes kept)
  show profile      — Everything Lota knows about you
  list notes        — All research notes
  list notes [cat]  — Filter by category (e.g. "list notes opportunity")
  help              — This menu

Autonomous mode:
  auto: [goal]      — Lota works on the goal without you, up to 30 steps
  auto 50: [goal]   — Same but with a custom step limit (replace 50)
  resume            — Continue the last paused run from where it stopped

  Ctrl+C pauses at any time. Type 'resume' to pick back up.

  Examples:
    auto: Research the walleye fishing tackle market and find the top 3 opportunities
    auto: Build a profile of the top 10 fishing forums and what people complain about
    auto 15: Find competitors selling custom fishing jigs on Etsy and Amazon
"""

def main():
    conversation_history = load_memory()

    print()
    if conversation_history:
        print("Lota: Welcome back, partner. I remember where we left off.")
    else:
        print("Lota: Starting fresh. Let's figure out what we're building.")
    print("      (Type 'help' for commands)\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            save_memory(conversation_history)
            print("\nLota: Saved. Get outside.\n")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd == "quit":
            save_memory(conversation_history)
            print("Lota: Memory saved. Talk soon, partner.\n")
            break

        if cmd == "clear memory":
            conversation_history = []
            save_memory(conversation_history)
            print("Lota: Conversation cleared. Profile and notes are intact.\n")
            continue

        if cmd == "show profile":
            print(f"\n{tool_get_profile()}\n")
            continue

        if cmd.startswith("list notes"):
            parts = user_input.split(None, 2)
            cat = parts[2] if len(parts) > 2 else None
            print(f"\n{tool_list_notes(cat)}\n")
            continue

        if cmd == "help":
            print(HELP_TEXT)
            continue

        # ── Resume paused autonomous run ─────────────────
        if cmd == "resume":
            state = load_goal_state()
            if not state:
                print("Lota: No paused run to resume. Start one with 'auto: [goal]'\n")
            else:
                print(f"Lota: Resuming — \"{state['goal']}\"")
                print(f"      ({state['steps_completed']} steps done, paused {state['saved_at']})\n")
                conversation_history = run_autonomous_mode(
                    goal=state["goal"],
                    conversation_history=conversation_history,
                    max_steps=state["max_steps"],
                    steps_already_done=state["steps_completed"]
                )
            continue

        # ── Autonomous mode ──────────────────────────────
        # Formats: "auto: goal text" or "auto 25: goal text"
        import re
        auto_match = re.match(r'^auto\s*(\d+)?\s*:\s*(.+)$', user_input, re.IGNORECASE | re.DOTALL)
        if auto_match:
            max_steps = int(auto_match.group(1)) if auto_match.group(1) else DEFAULT_MAX_STEPS
            goal = auto_match.group(2).strip()
            conversation_history = run_autonomous_mode(goal, conversation_history, max_steps)
            continue

        # ── Normal conversational turn ───────────────────
        conversation_history.append({
            "role": "user",
            "content": user_input
        })

        print()
        try:
            response_text, conversation_history = run_lota_turn(conversation_history)
            print(f"Lota: {response_text}\n")
        except anthropic.RateLimitError:
            conversation_history.pop()
            print("Lota: Rate limited — give it a minute and try again.\n")
        except anthropic.APIConnectionError:
            conversation_history.pop()
            print("Lota: Connection issue. Check your network and try again.\n")
        except anthropic.AuthenticationError:
            print("Lota: API key not working. Check your ANTHROPIC_API_KEY env var.\n")
            break
        except Exception as e:
            conversation_history.pop()
            print(f"Lota: Hit an error — {e}\n")

        save_memory(conversation_history)


if __name__ == "__main__":
    main()
