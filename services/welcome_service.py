import random

import discord


WELCOME_MESSAGES = [
    (
        "Welcome, {user} 🜂\n\n"
        "Another soul has found the road through ash and ruin.\n\n"
        "Choose your path in #choose-your-path, learn the laws of this place, and begin your rise through the ashes."
    ),
    (
        "The gates open, {user} 🜂\n\n"
        "You have stepped into Ashfall Chronicles.\n\n"
        "The fire remembers every mark, every vow, every contribution. Choose your path and let the ashes judge your worth."
    ),
    (
        "A new wanderer arrives, {user} 🜂\n\n"
        "The roads are broken. The relics are buried. The old world is not dead yet.\n\n"
        "Begin in #choose-your-path and find where your service belongs."
    ),
    (
        "Welcome to the ashes, {user} 🜂\n\n"
        "Here, names are earned through action.\n\n"
        "Speak, create, support, test — and leave your mark on Ashfall Chronicles."
    ),
    (
        "The Chronicle records a new name: {user} 🜂\n\n"
        "Your journey begins now.\n\n"
        "Choose your path, earn Ash Marks, and rise from stranger to legend."
    ),
]


def build_welcome_message(member: discord.Member) -> str:
    template = random.choice(WELCOME_MESSAGES)
    return template.replace("{user}", member.mention).strip()
