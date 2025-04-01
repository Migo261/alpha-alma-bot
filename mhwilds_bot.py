import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

SHARPNESS_MULTIPLIERS = {
    "red": 0.5,
    "orange": 0.75,
    "yellow": 1.0,
    "green": 1.05,
    "blue": 1.2,
    "white": 1.32,
    "purple": 1.39
}

MELEE_WEAPONS = {"gs", "ls", "sns", "db", "hammer", "hh", "lance", "gl", "ig"}

def apply_attack_boost(raw, bonus, level):
    bonus_from_skill = [0, 3, 6, 9, 12, 15][min(level, 5)]
    percent = [0, 0.03, 0.06, 0.09, 0.09, 0.1][min(level, 5)]
    return raw + bonus + bonus_from_skill + round(raw * percent)

def apply_critical_boost(level):
    if level == 1:
        return 1.3
    elif level == 2:
        return 1.35
    elif level == 3:
        return 1.4
    return 1.25

def calculate_damage(raw, bonus_raw, affinity, attack_boost_level, critical_boost_level, sharpness_multiplier):
    effective_crit = apply_critical_boost(critical_boost_level)
    crit_chance = affinity / 100
    avg_crit = crit_chance * effective_crit + (1 - crit_chance) * 1
    total_raw = apply_attack_boost(raw, bonus_raw, attack_boost_level)
    return round(total_raw * avg_crit * sharpness_multiplier, 2)

class DamageModal(discord.ui.Modal, title="🧮 Schaden berechnen"):
    def __init__(self, weapon_type):
        super().__init__()
        self.weapon_type = weapon_type

        self.raw = discord.ui.TextInput(label="Basisangriff", placeholder="z. B. 220", required=True)
        self.bonus = discord.ui.TextInput(label="Zusätzlicher Angriff (z. B. Waffe oder Buffs)", placeholder="z. B. 20", required=True)
        self.affinity = discord.ui.TextInput(label="Affinität (%)", placeholder="z. B. 25", required=True)
        self.ab = discord.ui.TextInput(label="Attack Boost Level (0–5)", placeholder="z. B. 4", required=True)
        self.cb = discord.ui.TextInput(label="Critical Boost Level (0–3)", placeholder="z. B. 3", required=True)

        for field in [self.raw, self.bonus, self.affinity, self.ab, self.cb]:
            self.add_item(field)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            raw = int(self.raw.value)
            bonus = int(self.bonus.value)
            affinity = int(self.affinity.value)
            ab = int(self.ab.value)
            cb = int(self.cb.value)

            if self.weapon_type in MELEE_WEAPONS:
                rows = []
                for sharpness, multiplier in SHARPNESS_MULTIPLIERS.items():
                    dmg = calculate_damage(raw, bonus, affinity, ab, cb, multiplier)
                    rows.append(f"**{sharpness.capitalize()}**: `{dmg}`")
                msg = "\n".join(rows)
            else:
                dmg = calculate_damage(raw, bonus, affinity, ab, cb, 1.0)
                msg = f"**Berechneter Schaden:** `{dmg}` (Fernkampfwaffe ohne Schärfe)"

            await interaction.response.send_message(f"🔧 **Schaden für `{self.weapon_type.upper()}`**\n{msg}", ephemeral=True)

        except ValueError:
            await interaction.response.send_message("❌ Ungültige Eingabe! Bitte nur Zahlen verwenden.", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot {bot.user} ist online und Slash-Befehle wurden synchronisiert!")

@bot.tree.command(name="schaden", description="Berechne den Schaden für eine bestimmte Waffe")
@app_commands.describe(waffe="Waffe (z. B. GS, LS, IG etc.)")
@app_commands.choices(waffe=[
    app_commands.Choice(name="GS (Great Sword)", value="gs"),
    app_commands.Choice(name="LS (Long Sword)", value="ls"),
    app_commands.Choice(name="SNS (Sword & Shield)", value="sns"),
    app_commands.Choice(name="DB (Dual Blades)", value="db"),
    app_commands.Choice(name="Hammer", value="hammer"),
    app_commands.Choice(name="HH (Hunting Horn)", value="hh"),
    app_commands.Choice(name="Lance", value="lance"),
    app_commands.Choice(name="GL (Gunlance)", value="gl"),
    app_commands.Choice(name="IG (Insect Glaive)", value="ig"),
    app_commands.Choice(name="Bow", value="bow"),
    app_commands.Choice(name="HBG (Heavy Bowgun)", value="hbg"),
    app_commands.Choice(name="LBG (Light Bowgun)", value="lbg"),
])
async def schaden(interaction: discord.Interaction, waffe: app_commands.Choice[str]):
    await interaction.response.send_modal(DamageModal(waffe.value))

bot.run(os.getenv("TOKEN"))
