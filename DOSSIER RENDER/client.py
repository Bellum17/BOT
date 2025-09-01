import discord
import os
import json

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Pour accéder aux membres
intents.guilds = True  # Pour accéder aux informations des serveurs

client = discord.Client(intents=intents)

BALANCE_FILE = "balances.json"

def load_balances():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_balances(balances):
    with open(BALANCE_FILE, "w") as f:
        json.dump(balances, f)

balances = load_balances()

def is_admin(message):
    # Vérifie si l'auteur du message a les permissions administrateur sur le serveur
    return message.author.guild_permissions.administrator

@client.event
async def on_ready():
    print(f'Connecté en tant que {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = str(message.author.id)
    if user_id not in balances:
        balances[user_id] = 0
        save_balances(balances)

    # $hello
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    # $balance
    elif message.content.startswith('$balance'):
        await message.channel.send(
            f"{message.author.mention}, ton solde est de {balances[user_id]:,} 💰."
        )

    # $pay @user montant
    elif message.content.startswith('$pay'):
        parts = message.content.split()
        if len(parts) < 3 or not message.mentions:
            await message.channel.send("Utilisation : `$pay @utilisateur montant`")
            return
        target = message.mentions[0]
        try:
            amount = int(parts[2].replace(',', ''))
        except ValueError:
            await message.channel.send("Le montant doit être un nombre entier.")
            return
        if amount <= 0:
            await message.channel.send("Le montant doit être positif.")
            return
        if balances[user_id] < amount:
            await message.channel.send("Fonds insuffisants.")
            return
        target_id = str(target.id)
        balances[user_id] -= amount
        balances[target_id] = balances.get(target_id, 0) + amount
        save_balances(balances)
        await message.channel.send(
            f"{message.author.mention} a payé {amount:,} 💰 à {target.mention}."
        )

    # ADMIN COMMANDS
    elif message.content.startswith('$reset-economy'):
        if not is_admin(message):
            await message.channel.send("Commande réservée aux administrateurs.")
            return
        balances.clear()
        save_balances(balances)
        await message.channel.send("L'économie a été réinitialisée.")

    elif message.content.startswith('$add-money'):
        if not is_admin(message):
            await message.channel.send("Commande réservée aux administrateurs.")
            return
        parts = message.content.split()
        if len(parts) < 3 or not message.mentions:
            await message.channel.send("Utilisation : `$add-money @utilisateur montant`")
            return
        target = message.mentions[0]
        try:
            amount = int(parts[2].replace(',', ''))
        except ValueError:
            await message.channel.send("Le montant doit être un nombre entier.")
            return
        target_id = str(target.id)
        balances[target_id] = balances.get(target_id, 0) + amount
        save_balances(balances)
        await message.channel.send(
            f"{amount:,} 💰 ajoutés à {target.mention}."
        )

    elif message.content.startswith('$remove-money'):
        if not is_admin(message):
            await message.channel.send("Commande réservée aux administrateurs.")
            return
        parts = message.content.split()
        if len(parts) < 3 or not message.mentions:
            await message.channel.send("Utilisation : `$remove-money @utilisateur montant`")
            return
        target = message.mentions[0]
        try:
            amount = int(parts[2].replace(',', ''))
        except ValueError:
            await message.channel.send("Le montant doit être un nombre entier.")
            return
        target_id = str(target.id)
        balances[target_id] = max(0, balances.get(target_id, 0) - amount)
        save_balances(balances)
        await message.channel.send(
            f"{amount:,} 💰 retirés à {target.mention}."
        )

    # $ranking
    elif message.content.startswith('$ranking'):
        sorted_balances = sorted(balances.items(), key=lambda x: x[1], reverse=True)
        if not sorted_balances:
            await message.channel.send("Aucun classement disponible.")
            return

        class RankingView(discord.ui.View):
            def __init__(self, ctx, sorted_balances):
                super().__init__(timeout=60)
                self.ctx = ctx
                self.sorted_balances = sorted_balances
                self.page = 0
                self.per_page = 20
                self.max_page = (len(sorted_balances) - 1) // self.per_page

            async def send_embed(self, interaction=None):
                start = self.page * self.per_page
                end = start + self.per_page
                emojis = ["🥇", "🥈", "🥉"]
                lines = []
                for idx, (user_id, amount) in enumerate(self.sorted_balances[start:end], start=start+1):
                    member = self.ctx.guild.get_member(int(user_id))
                    name = member.display_name if member else f"Utilisateur inconnu ({user_id})"
                    if idx <= 3 and self.page == 0:
                        line = f"{emojis[idx-1]} — {name} — {amount:,} 💰"
                    else:
                        line = f"{idx}. — {name} — {amount:,} 💰"
                    lines.append(line)
                embed = discord.Embed(
                    title="Classement des Budget par Pays",
                    description="\n".join(lines),
                    color=discord.Color.gold()
                )
                embed.set_footer(text=f"Page {self.page+1}/{self.max_page+1}")
                if interaction:
                    await interaction.response.edit_message(embed=embed, view=self)
                else:
                    await self.ctx.channel.send(embed=embed, view=self)

            @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.page > 0:
                    self.page -= 1
                    await self.send_embed(interaction)

            @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.page < self.max_page:
                    self.page += 1
                    await self.send_embed(interaction)

        view = RankingView(message, sorted_balances)
        await view.send_embed()

# Récupère le token depuis une variable d'environnement
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("Le token Discord n'est pas défini dans les variables d'environnement.")

client.run(TOKEN)