"""Study coaches — aggressive desktop sticker characters for Student."""

import random

from profile import EXAM, FIRST_NAME

COACHES = {
    "yoda": {
        "key": "yoda",
        "name": "Master Yoda",
        "title": "Jedi Master",
        "emoji": "🟢",
        "accent": "#4ade80",
        "saber": "#4ade80",
        "attack": "force",
    },
    "vader": {
        "key": "vader",
        "name": "Darth Vader",
        "title": "Sith Lord",
        "emoji": "⚫",
        "accent": "#f87171",
        "saber": "#ef4444",
        "attack": "saber",
    },
    "mando": {
        "key": "mando",
        "name": "The Mandalorian",
        "title": "Bounty Hunter",
        "emoji": "🛡️",
        "accent": "#94a3b8",
        "saber": "#38bdf8",
        "attack": "blaster",
    },
    "dooku": {
        "key": "dooku",
        "name": "Count Dooku",
        "title": "Sith Lord",
        "emoji": "🟤",
        "accent": "#c084fc",
        "saber": "#ef4444",
        "attack": "saber",
    },
    "anakin": {
        "key": "anakin",
        "name": "Anakin Skywalker",
        "title": "Jedi Knight",
        "emoji": "🔵",
        "accent": "#60a5fa",
        "saber": "#3b82f6",
        "attack": "saber",
    },
    "deathstar": {
        "key": "deathstar",
        "name": "Desktop companion",
        "title": "Imperial Station",
        "emoji": "🌑",
        "accent": "#94a3b8",
        "saber": "#22c55e",
        "attack": "laser",
    },
}

_LINES = {
    "yoda": {
        "startup": [
            f"{FIRST_NAME}. Log your hours, or fail {EXAM}, you will.",
            f"Weak your discipline is. Fix it, now.",
            f"PDFs without notes? Foolish, that is.",
            f"{EXAM} waits for no one. Study, you must.",
            f"Distraction is the path to the dark side. Close it.",
        ],
        "nag": [
            f"Studying, are you, {FIRST_NAME}? Or lying to yourself?",
            f"The Force is weak in you right now. Open your notes.",
            f"That screen is not your syllabus. Move.",
            f"Hours unlogged. Shame, this brings.",
            f"Reels will not write your answers. Books will.",
            f"Again you drift. Focus, or fall behind.",
            f"Your rivals study while you stall, {FIRST_NAME}.",
            f"Truth: you are not studying. Correct it.",
            f"Mind like water? Yours is mud. Clear it.",
            f"Another minute wasted. Costly, that is.",
        ],
        "attack": [
            f"Touch me again without studying, and regret you will, {FIRST_NAME}.",
            f"Force choke is mild. Failing {EXAM} is worse.",
            f"Strike you I did. Now strike your syllabus.",
            f"Do not poke the master. Poke your weak topics.",
            f"Pain, you feel? Good. Now study.",
            f"Your finger is bold. Your prep is not.",
            f"Enough games. Notes. Now.",
        ],
        "praise": [
            f"Strong with focus, you are, {FIRST_NAME}. Continue.",
            f"Rare. Discipline shown. Do not stop.",
            f"Good. But complacent, do not become.",
        ],
    },
    "vader": {
        "startup": [
            f"{FIRST_NAME}. Report your study hours. Immediately.",
            f"I find your lack of preparation… disturbing.",
            f"The Empire does not accept excuses. Neither do I.",
            f"Are you studying, or performing studying?",
            f"Your {EXAM} fear is valid. Your laziness is not.",
        ],
        "nag": [
            f"{FIRST_NAME}. I sense distraction. Destroy it.",
            f"You are scrolling. Do not insult my intelligence.",
            f"Your focus is as broken as Alderaan.",
            f"Log your hours, or accept failure.",
            f"I am not asking. I am commanding.",
            f"That tab is not revision. Close it.",
            f"You disappoint me, {FIRST_NAME}. Again.",
            f"The dark side of procrastination has you.",
            f"Study, or be crushed by {EXAM}.",
            f"Your potential means nothing without work.",
        ],
        "attack": [
            f"You dare touch me, {FIRST_NAME}? Study, or suffer.",
            f"That was a lightsaber warning. Next is your ego.",
            f"Do not test me. Test yourself — open your notes.",
            f"I have no patience for your nonsense.",
            f"Strike delivered. Now strike your backlog.",
            f"Pain is a teacher. Learn.",
            f"You wanted my attention. Earn it with work.",
        ],
        "praise": [
            f"Impressive. Most disciplined, you have become.",
            f"You may survive {EXAM}. Do not relax.",
            f"Acceptable performance. Maintain it.",
        ],
    },
    "mando": {
        "startup": [
            f"{FIRST_NAME}. Armour on. Books open. No talk.",
            f"This is the way: log every hour honestly.",
            f"Bounty on your time is being wasted. End it.",
            f"No distractions. No mercy. Study.",
        ],
        "nag": [
            f"{FIRST_NAME}. That is not study. That is escape.",
            f"This is the way: syllabus first, everything else never.",
            f"I have spoken. Move your hands to notes.",
            f"Your focus is worth less than beskar right now.",
            f"Scrolling is not the way.",
            f"Are you studying? I already know the answer.",
            f"Another hour gone. Irrecoverable.",
            f"The Child has more discipline than you today.",
            f"Helmet stays on until work is done.",
            f"Prove you are not soft, {FIRST_NAME}.",
        ],
        "attack": [
            f"Wrong move, {FIRST_NAME}. Blaster was a warning shot.",
            f"Touch again and I relocate you to your desk.",
            f"This is the way: you study, I shoot distractions.",
            f"Do not test a Mandalorian.",
            f"Direct hit. Now hit your targets for today.",
            f"I don't miss. Neither should your prep.",
            f"You poked the hunter. Hunt your syllabus instead.",
        ],
        "praise": [
            f"Good. This is the way, {FIRST_NAME}.",
            f"Focus found. Keep it locked.",
            f"Acceptable. Continue.",
        ],
    },
    "dooku": {
        "startup": [
            f"{FIRST_NAME}. Your {EXAM} prep is beneath you. Elevate it.",
            f"I expect elegance in study. You offer sloth.",
            f"Even a Count demands daily logs. Provide them.",
            f"Mediocrity bores me. Impress me with work.",
        ],
        "nag": [
            f"Twirling away your future, {FIRST_NAME}?",
            f"How uncivilized — reading without retention.",
            f"Your preparation insults your intelligence.",
            f"Refinement requires repetition. You skip both.",
            f"Disturbing, your procrastination is.",
            f"Study, or remain ordinary.",
            f"That distraction is vulgar. Remove it.",
            f"You have talent. Wasting it is criminal.",
            f"Another excuse? I have heard a thousand.",
            f"Fencing with time — and losing.",
        ],
        "attack": [
            f"Presumptuous, {FIRST_NAME}. The blade is faster than your pen.",
            f"You touched a Sith. Now touch your notes.",
            f"An elegant attack. Your study should match it.",
            f"Do not provoke what you cannot outwork.",
            f"Slash delivered. Slash your weak subjects.",
            f"Pain clarifies priorities. Feel it.",
            f"You wanted intensity. Here is your syllabus.",
        ],
        "praise": [
            f"Acceptable. Barely. Do not slip.",
            f"Your discipline improves. Sustain it.",
            f"Finally — something respectable.",
        ],
    },
    "anakin": {
        "startup": [
            f"{FIRST_NAME}! Bad feeling about your study log. Fix it.",
            f"You were chosen for more than scrolling.",
            f"Heroes don't hide from {EXAM}. Face it.",
            f"Your anger at prep is valid. Use it.",
            f"Stop negotiating with laziness. Win.",
        ],
        "nag": [
            f"{FIRST_NAME}, fear of failing is making you fail.",
            f"You're better than this pathetic drift.",
            f"Phone down. Books up. Now.",
            f"The Council would expel you at this pace.",
            f"Every minute you waste, someone else advances.",
            f"Don't lie to me — you're not studying.",
            f"Your potential is screaming. You're ignoring it.",
            f"Turn rage into revision, not reels.",
            f"Padawans work harder than you right now.",
            f"This is how you lose everything.",
        ],
        "attack": [
            f"You touched me, {FIRST_NAME}. Now touch your damn notes!",
            f"Lightsaber says: STOP WASTING TIME.",
            f"I didn't fall to the dark side for you to fall to Instagram.",
            f"Hit back at your syllabus, not me.",
            f"That slash was mercy. {EXAM} won't be.",
            f"Feel that? Good. Now work.",
            f"Attack me again when your hours are logged.",
        ],
        "praise": [
            f"NOW you're fighting the right enemy — {EXAM}.",
            f"Strong focus today. Don't lose it.",
            f"Keep this intensity. It's rare.",
        ],
    },
    "deathstar": {
        "startup": [
            f"Target: {FIRST_NAME}. Status: unprepared. Correct immediately.",
            f"Imperial Command requires your {EXAM} progress report.",
            f"Station online. Your discipline is not.",
            f"Planet-killer focus required. You have none.",
        ],
        "nag": [
            f"{FIRST_NAME}: operational readiness at zero percent.",
            f"Procrastination will not be tolerated.",
            f"Your prep has a critical exhaust port. Patch it.",
            f"Fire discipline, not superlaser, at your backlog.",
            f"Distraction detected. Neutralize.",
            f"Empire built on order. You built chaos.",
            f"Another hour evaporated. Unacceptable.",
            f"Study or be obliterated by {EXAM}.",
            f"Your focus is not fully operational.",
            f"Report to your desk. Immediately.",
        ],
        "attack": [
            f"Superlaser charged. Next target: your excuses, {FIRST_NAME}.",
            f"You touched the station. Bad tactical decision.",
            f"Direct hit. Study is your only escape vector.",
            f"That beam was a warning. {EXAM} is the real weapon.",
            f"Imperial justice delivered. Now imperial discipline.",
            f"Do not approach unless armed with notes.",
            f"Planet destroyed. Next: your distractions.",
        ],
        "praise": [
            f"Operational efficiency: acceptable, {FIRST_NAME}.",
            f"Fully armed and operational — keep it that way.",
            f"Target acquired: progress. Maintain trajectory.",
        ],
    },
}

COACH_ORDER = (
    "vader", "deathstar", "dooku", "mando", "anakin", "yoda",
)


def pick_coach_key():
    return random.choice(COACH_ORDER)


def next_coach_key(current: str | None = None) -> str:
    if current not in COACH_ORDER:
        return COACH_ORDER[0]
    return COACH_ORDER[(COACH_ORDER.index(current) + 1) % len(COACH_ORDER)]


def get_coach(key=None):
    key = key or pick_coach_key()
    return COACHES[key]


def get_line(key, category):
    return random.choice(_LINES[key][category])


def get_startup_brief():
    key = pick_coach_key()
    return get_coach(key), get_line(key, "startup")


def get_nag_brief():
    key = pick_coach_key()
    return get_coach(key), get_line(key, "nag")


def get_in_app_brief(today_hours=0.0, daily_goal=6.0):
    key = pick_coach_key()
    coach = get_coach(key)
    if today_hours >= daily_goal:
        line = get_line(key, "praise")
    elif today_hours <= 0:
        line = get_line(key, "startup")
    else:
        line = get_line(key, "nag")
    return coach, line


def render_coach_html(coach, line):
    safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""
    <div class="coach-card coach-{coach['key']}">
        <div class="coach-avatar">{coach['emoji']}</div>
        <div class="coach-body">
            <p class="coach-name">{coach['name']} <span class="coach-title">· {coach['title']}</span></p>
            <p class="coach-line">"{safe_line}"</p>
        </div>
    </div>
    """