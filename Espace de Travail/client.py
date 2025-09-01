from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import math

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

EMBED_COLOR = 0xefe7c5
IMAGE_URL = "https://zupimages.net/up/21/03/vl8j.png"
MONNAIE_EMOJI = "<:Monnaie:1412039375063355473>"
INVISIBLE_CHAR = "⠀"
BALANCE_FILE = "balances.json"
LOG_FILE = "log_channel.json"
MESSAGE_LOG_FILE = "message_log_channel.json"
LOANS_FILE = "loans.json"

def load_balances():
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_balances(balances):
    with open(BALANCE_FILE, "w") as f:
        json.dump(balances, f)

def load_log_channel():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_log_channel(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f)

def load_message_log_channel():
    if os.path.exists(MESSAGE_LOG_FILE):
        with open(MESSAGE_LOG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_message_log_channel(data):
    with open(MESSAGE_LOG_FILE, "w") as f:
        json.dump(data, f)

def load_loans():
    if os.path.exists(LOANS_FILE):
        with open(LOANS_FILE, "r") as f:
            return json.load(f)
    return []

def save_loans(loans):
    with open(LOANS_FILE, "w") as f:
        json.dump(loans, f)

balances = load_balances()
log_channel_data = load_log_channel()
message_log_channel_data = load_message_log_channel()
loans = load_loans()

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Synchronise les commandes slash globalement
        await self.tree.sync()

bot = MyBot()

def get_log_channel(guild):
    channel_id = log_channel_data.get(str(guild.id))
    if channel_id:
        return guild.get_channel(channel_id)
    return None

async def send_log(guild, message):
    channel = get_log_channel(guild)
    if channel:
        embed = discord.Embed(
            description=f"> {message}{INVISIBLE_CHAR}",
            color=EMBED_COLOR
        )
        embed.set_image(url=IMAGE_URL)
        await channel.send(embed=embed)

def get_message_log_channel(guild):
    channel_id = message_log_channel_data.get(str(guild.id))
    if channel_id:
        return guild.get_channel(channel_id)
    return None

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}')

@bot.tree.command(name="setlogeconomy", description="Définit le salon de logs pour l'économie")
@app_commands.checks.has_permissions(administrator=True)
async def setlogeconomy(interaction: discord.Interaction, channel: discord.TextChannel):
    log_channel_data[str(interaction.guild.id)] = channel.id
    save_log_channel(log_channel_data)
    embed = discord.Embed(
        description=f"> Salon de logs défini sur {channel.mention}.{INVISIBLE_CHAR}",
        color=EMBED_COLOR
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="balance", description="Affiche votre solde")
async def balance(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in balances:
        balances[user_id] = 0
        save_balances(balances)
    embed = discord.Embed(
        description=f"> {interaction.user.mention}, ton solde est de {balances[user_id]:,} {MONNAIE_EMOJI}{INVISIBLE_CHAR}",
        color=EMBED_COLOR
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="pay", description="Payer un utilisateur")
@app_commands.describe(user="Utilisateur à payer", montant="Montant à transférer", role="Rôle du pays")
async def pay(interaction: discord.Interaction, user: discord.Member, montant: int, role: discord.Role):
    receiver_id = str(user.id)
    # Vérifie que l'utilisateur possède le rôle
    if role not in interaction.user.roles:
        await interaction.response.send_message("> Vous n'êtes pas le pays en question." + INVISIBLE_CHAR, ephemeral=True)
        return
    # Le solde du rôle est utilisé
    role_id = str(role.id)
    if role_id not in balances:
        balances[role_id] = 0
    if receiver_id not in balances:
        balances[receiver_id] = 0
    if montant <= 0:
        await interaction.response.send_message("> Le montant doit être positif." + INVISIBLE_CHAR, ephemeral=True)
        return
    if balances[role_id] < montant:
        await interaction.response.send_message("> Fonds insuffisants pour le rôle." + INVISIBLE_CHAR, ephemeral=True)
        return
    balances[role_id] -= montant
    balances[receiver_id] += montant
    save_balances(balances)
    embed = discord.Embed(
        description=f"> {interaction.user.mention} ({role.mention}) a payé {user.mention} {montant:,} {MONNAIE_EMOJI}{INVISIBLE_CHAR}",
        color=EMBED_COLOR
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, f"{interaction.user.mention} ({role.mention}) a payé {user.mention} {montant:,} {MONNAIE_EMOJI}")

@bot.tree.command(name="add_money", description="Ajoute de l'argent à un utilisateur ou à un rôle")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(target="Utilisateur ou rôle", montant="Montant à ajouter")
async def add_money(interaction: discord.Interaction, target: discord.Role | discord.Member, montant: int):
    if isinstance(target, discord.Role):
        role_id = str(target.id)
        balances[role_id] = balances.get(role_id, 0) + montant
        save_balances(balances)
        embed = discord.Embed(
            description=f"> {interaction.user.mention} a ajouté {montant:,} {MONNAIE_EMOJI} au rôle {target.mention}.{INVISIBLE_CHAR}",
            color=EMBED_COLOR
        )
        embed.set_image(url=IMAGE_URL)
        await interaction.response.send_message(embed=embed)
        await send_log(
            interaction.guild,
            f"{interaction.user.mention} a ajouté {montant:,} {MONNAIE_EMOJI} au rôle {target.mention}"
        )
    else:
        user_id = str(target.id)
        balances[user_id] = balances.get(user_id, 0) + montant
        save_balances(balances)
        embed = discord.Embed(
            description=f"> {interaction.user.mention} a ajouté {montant:,} {MONNAIE_EMOJI} à {target.mention}.{INVISIBLE_CHAR}",
            color=EMBED_COLOR
        )
        embed.set_image(url=IMAGE_URL)
        await interaction.response.send_message(embed=embed)
        await send_log(
            interaction.guild,
            f"{interaction.user.mention} a ajouté {montant:,} {MONNAIE_EMOJI} à {target.mention}"
        )

@bot.tree.command(name="remove_money", description="Retire de l'argent à un utilisateur ou à un rôle")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(target="Utilisateur ou rôle", montant="Montant à retirer")
async def remove_money(interaction: discord.Interaction, target: discord.Role | discord.Member, montant: int):
    if isinstance(target, discord.Role):
        # Retire l'argent du solde du rôle (et non des membres)
        role_id = str(target.id)
        balances[role_id] = max(0, balances.get(role_id, 0) - montant)
        save_balances(balances)
        embed = discord.Embed(
            description=f"> {interaction.user.mention} a retiré {montant:,} {MONNAIE_EMOJI} au rôle {target.mention}.{INVISIBLE_CHAR}",
            color=EMBED_COLOR
        )
        embed.set_image(url=IMAGE_URL)
        await interaction.response.send_message(embed=embed)
        await send_log(
            interaction.guild,
            f"{interaction.user.mention} a retiré {montant:,} {MONNAIE_EMOJI} au rôle {target.mention}"
        )
    else:
        user_id = str(target.id)
        balances[user_id] = max(0, balances.get(user_id, 0) - montant)
        save_balances(balances)
        embed = discord.Embed(
            description=f"> {interaction.user.mention} a retiré {montant:,} {MONNAIE_EMOJI} à {target.mention}.{INVISIBLE_CHAR}",
            color=EMBED_COLOR
        )
        embed.set_image(url=IMAGE_URL)
        await interaction.response.send_message(embed=embed)
        await send_log(
            interaction.guild,
            f"{interaction.user.mention} a retiré {montant:,} {MONNAIE_EMOJI} à {target.mention}"
        )

@bot.tree.command(name="setlogmessage", description="Définit le salon de logs pour les messages")
@app_commands.checks.has_permissions(administrator=True)
async def setlogmessage(interaction: discord.Interaction, channel: discord.TextChannel):
    message_log_channel_data[str(interaction.guild.id)] = channel.id
    save_message_log_channel(message_log_channel_data)
    embed = discord.Embed(
        description=f"> Salon de logs de messages défini sur {channel.mention}.{INVISIBLE_CHAR}",
        color=EMBED_COLOR
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_message_delete(message):
    # Ignore si le message vient d'un salon de logs
    log_channels = []
    log_channel_id = log_channel_data.get(str(message.guild.id))
    msg_log_channel_id = message_log_channel_data.get(str(message.guild.id))
    if log_channel_id:
        log_channels.append(log_channel_id)
    if msg_log_channel_id:
        log_channels.append(msg_log_channel_id)
    if message.channel.id in log_channels:
        return
    channel = get_message_log_channel(message.guild)
    if channel:
        embed = discord.Embed(
            title="Message supprimé",
            description=f"**Auteur :** {message.author.mention}\n**Salon :** {message.channel.mention}\n**Contenu :**\n{message.content}",
            color=discord.Color.red()
        )
        await channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    log_channels = []
    log_channel_id = log_channel_data.get(str(before.guild.id))
    msg_log_channel_id = message_log_channel_data.get(str(before.guild.id))
    if log_channel_id:
        log_channels.append(log_channel_id)
    if msg_log_channel_id:
        log_channels.append(msg_log_channel_id)
    if before.channel.id in log_channels:
        return
    channel = get_message_log_channel(before.guild)
    if channel:
        embed = discord.Embed(
            title="Message modifié",
            description=f"**Auteur :** {before.author.mention}\n**Salon :** {before.channel.mention}\n**Avant :**\n{before.content}\n**Après :**\n{after.content}",
            color=discord.Color.orange()
        )
        await channel.send(embed=embed)

class RankingView(discord.ui.View):
    def __init__(self, interaction, balances, per_page=15):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.sorted_balances = sorted(
            ((user_id, amount) for user_id, amount in balances.items()),
            key=lambda x: x[1],
            reverse=True
        )
        self.per_page = per_page
        self.page = 1
        self.max_page = max(1, math.ceil(len(self.sorted_balances) / self.per_page))

    async def send_page(self, interaction):
        page_balances = self.sorted_balances[(self.page-1)*self.per_page : self.page*self.per_page]
        description = ""
        for i, (user_id, amount) in enumerate(page_balances, start=1 + (self.page - 1) * self.per_page):
            member = interaction.guild.get_member(int(user_id))
            if member:
                description += f"**#{i}** {member.mention} — {amount:,} {MONNAIE_EMOJI}\n"
            else:
                description += f"**#{i}** Utilisateur inconnu — {amount:,} {MONNAIE_EMOJI}\n"
        if not description:
            description = "Aucun classement disponible."
        embed = discord.Embed(
            title="🏛️ | **Classement des Budgets**",
            description=description + INVISIBLE_CHAR,
            color=EMBED_COLOR
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1412078652686077974/1412108445003284541/Design_sans_titre_-_2025-09-01T181436.666.png?ex=68b717f8&is=68b5c678&hm=16d3eb8f243e7acc1e0021bd3f57eababa6a3a13824bc9c7b557004b6e4d3b96&")
        embed.set_footer(text=f"Page 1/{self.max_page}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            await self.send_page(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.max_page:
            self.page += 1
            await self.send_page(interaction)

@bot.tree.command(name="ranking", description="Affiche le classement des rôles par solde")
async def ranking(interaction: discord.Interaction):
    # Filtre uniquement les rôles présents dans le serveur ET ayant un solde strictement positif
    role_balances = [
        (role, balances.get(str(role.id), 0))
        for role in interaction.guild.roles
        if str(role.id) in balances and balances.get(str(role.id), 0) > 0
    ]
    # Trie par solde décroissant
    sorted_roles = sorted(role_balances, key=lambda x: x[1], reverse=True)
    view = RankingViewRoles(interaction, sorted_roles)
    page_roles = sorted_roles[:view.per_page]
    description = ""
    for i, (role, amount) in enumerate(page_roles, start=1):
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"#{i}"
        description += f"**{medal}** {role.mention} — {amount:,} {MONNAIE_EMOJI}\n"
    if not description:
        description = "Aucun classement disponible."
    embed = discord.Embed(
        title="🏛️ | **Classement des Budgets**",
        description=description + INVISIBLE_CHAR,
        color=EMBED_COLOR
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1412078652686077974/1412108445003284541/Design_sans_titre_-_2025-09-01T181436.666.png?ex=68b717f8&is=68b5c678&hm=16d3eb8f243e7acc1e0021bd3f57eababa6a3a13824bc9c7b557004b6e4d3b96&")
    embed.set_footer(text=f"Page 1/{view.max_page}")
    await interaction.response.send_message(embed=embed, view=view)

class RankingViewRoles(discord.ui.View):
    def __init__(self, interaction, sorted_roles, per_page=15):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.sorted_roles = sorted_roles
        self.per_page = per_page
        self.page = 1
        self.max_page = max(1, math.ceil(len(self.sorted_roles) / self.per_page))

    async def send_page(self, interaction):
        page_roles = self.sorted_roles[(self.page-1)*self.per_page : self.page*self.per_page]
        description = ""
        for i, (role, amount) in enumerate(page_roles, start=1 + (self.page - 1) * self.per_page):
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"#{i}"
            description += f"**{medal}** {role.mention} — {amount:,} {MONNAIE_EMOJI}\n"
        if not description:
            description = "Aucun classement disponible."
        embed = discord.Embed(
            title="🏛️ | **Classement des Budgets**",
            description=description + INVISIBLE_CHAR,
            color=EMBED_COLOR
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1412078652686077974/1412108445003284541/Design_sans_titre_-_2025-09-01T181436.666.png?ex=68b717f8&is=68b5c678&hm=16d3eb8f243e7acc1e0021bd3f57eababa6a3a13824bc9c7b557004b6e4d3b96&")
        embed.set_footer(text=f"Page {self.page}/{self.max_page}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            await self.send_page(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.max_page:
            self.page += 1
            await self.send_page(interaction)

@bot.tree.command(name="reset_economy", description="Réinitialise l'économie du serveur")
@app_commands.checks.has_permissions(administrator=True)
async def reset_economy(interaction: discord.Interaction):
    # Réinitialise les soldes de tous les membres
    for member in interaction.guild.members:
        balances[str(member.id)] = 0
    # Réinitialise les soldes de tous les rôles présents dans le serveur
    for role in interaction.guild.roles:
        balances[str(role.id)] = 0
    save_balances(balances)
    embed = discord.Embed(
        description=f"> {interaction.user.mention} a réinitialisé l'économie du serveur (membres et rôles).{INVISIBLE_CHAR}",
        color=EMBED_COLOR
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed)
    await send_log(
        interaction.guild,
        f"{interaction.user.mention} a réinitialisé l'économie du serveur (membres et rôles)."
    )

def calculate_loan(montant, taux, paiements):
    total = montant * (1 + taux / 100)
    paiement = math.ceil(total / paiements)
    return total, paiement

# Remplace le nom de la commande par "creer_pret"
@bot.tree.command(name="creer_pret", description="Crée un prêt entre deux rôles")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    emprunteur="Rôle emprunteur",
    montant="Montant emprunté",
    taux="Taux d'intérêt (%)",
    paiements="Nombre de paiements",
    preteur="Rôle prêteur"
)
async def creer_pret(
    interaction: discord.Interaction,
    emprunteur: discord.Role,
    montant: int,
    taux: float,
    paiements: int,
    preteur: discord.Role = None
):
    emprunteur_id = str(emprunteur.id)
    if montant <= 0 or taux < 0 or paiements <= 0:
        await interaction.response.send_message("> Paramètres invalides.", ephemeral=True)
        return
    balances[emprunteur_id] = balances.get(emprunteur_id, 0) + montant
    save_balances(balances)
    # Détermine l'id du prêteur
    if preteur is None:
        preteur_id = str(bot.user.id)
        preteur_mention = bot.user.mention
        preteur_name = "Bot"
    else:
        preteur_id = str(preteur.id)
        preteur_mention = preteur.mention
        preteur_name = preteur.name
    total, paiement = calculate_loan(montant, taux, paiements)
    loan = {
        "user_id": emprunteur_id,
        "preteur_id": preteur_id,
        "preteur_name": preteur_name,
        "username": emprunteur.name,
        "montant": montant,
        "taux": taux,
        "paiements_restants": paiements,
        "total": total,
        "paiement": paiement
    }
    loans.append(loan)
    save_loans(loans)
    embed = discord.Embed(
        description=f"> Prêt de {montant:,} {MONNAIE_EMOJI} créé entre {preteur_mention} (prêteur) et {emprunteur.mention} (emprunteur) à {taux}% sur {paiements} paiements ({paiement:,} {MONNAIE_EMOJI}/paiement, total : {total:,} {MONNAIE_EMOJI}).{INVISIBLE_CHAR}",
        color=EMBED_COLOR
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed)
    await send_log(
        interaction.guild,
        f"Prêt de {montant:,} {MONNAIE_EMOJI} créé entre {preteur_mention} et {emprunteur.mention} ({paiements} paiements, taux {taux}%)."
    )

def paginate_loans(loans_list, page, per_page=20):
    start = (page - 1) * per_page
    end = start + per_page
    return loans_list[start:end], max(1, math.ceil(len(loans_list) / per_page))

@bot.tree.command(name="remboursement_annuel", description="Effectue les remboursements annuels pour tous les prêts actifs")
@app_commands.checks.has_permissions(administrator=True)
async def remboursement_annuel(interaction: discord.Interaction):
    rembourse = 0
    for loan in loans[:]:  # Copie pour modification
        if loan["paiements_restants"] > 0:
            paiement = loan["paiement"]
            user_id = loan["user_id"]
            preteur_id = loan.get("preteur_id", None) or str(bot.user.id)
            # Retire la somme à l'emprunteur
            balances[user_id] = max(0, balances.get(user_id, 0) - paiement)
            # Ajoute la somme au prêteur
            balances[preteur_id] = balances.get(preteur_id, 0) + paiement
            loan["paiements_restants"] -= 1
            rembourse += 1
            # Supprime le prêt si remboursé
            if loan["paiements_restants"] <= 0:
                loans.remove(loan)
    save_balances(balances)
    save_loans(loans)
    embed = discord.Embed(
        description=f"> Remboursement annuel effectué pour {rembourse} paiement(s) sur tous les prêts actifs.{INVISIBLE_CHAR}",
        color=EMBED_COLOR
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, f"Remboursement annuel effectué pour {rembourse} paiement(s) sur tous les prêts actifs.")

# Remplace le nom de la commande par "remboursement_pret"
@bot.tree.command(name="remboursement_pret", description="Effectue le remboursement d'un prêt spécifique entre rôles")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    emprunteur="Rôle emprunteur",
    preteur="Rôle prêteur"
)
async def remboursement_pret(interaction: discord.Interaction, emprunteur: discord.Role, preteur: discord.Role = None):
    emprunteur_id = str(emprunteur.id)
    if preteur is None:
        preteur_id = str(bot.user.id)
        preteur_mention = bot.user.mention
    else:
        preteur_id = str(preteur.id)
        preteur_mention = preteur.mention
    role_loans = [loan for loan in loans if loan["user_id"] == emprunteur_id and loan.get("preteur_id") == preteur_id and loan["paiements_restants"] > 0]
    if not role_loans:
        await interaction.response.send_message("> Aucun prêt actif avec ce prêteur pour ce rôle.", ephemeral=True)
        return
    loan = role_loans[0]
    paiement = loan["paiement"]
    # Vérifie que le rôle a assez d'argent pour rembourser
    if balances.get(emprunteur_id, 0) < paiement:
        await interaction.response.send_message("> Le rôle n'a pas assez d'argent pour effectuer le remboursement.", ephemeral=True)
        return
    # Retire la somme au rôle emprunteur
    balances[emprunteur_id] = balances.get(emprunteur_id, 0) - paiement
    # Ajoute la somme au rôle prêteur
    balances[preteur_id] = balances.get(preteur_id, 0) + paiement
    loan["paiements_restants"] -= 1
    if loan["paiements_restants"] <= 0:
        loans.remove(loan)  # Suppression automatique du prêt
    save_balances(balances)
    save_loans(loans)
    embed = discord.Embed(
        description=f"> Paiement de {paiement:,} {MONNAIE_EMOJI} effectué pour {emprunteur.mention} (prêteur : {preteur_mention}).{INVISIBLE_CHAR}",
        color=EMBED_COLOR
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, f"Paiement de {paiement:,} {MONNAIE_EMOJI} effectué pour {emprunteur.mention} (prêteur : {preteur_mention}).")

@bot.tree.command(name="supprimer_role_economie", description="Supprime un rôle du classement et de l'économie")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(role="Rôle à supprimer")
async def supprimer_role_economie(interaction: discord.Interaction, role: discord.Role):
    role_id = str(role.id)
    # Supprime le solde du rôle
    if role_id in balances:
        del balances[role_id]
    # Supprime les prêts où le rôle est emprunteur ou prêteur
    loans_to_remove = [loan for loan in loans if loan.get("user_id") == role_id or loan.get("preteur_id") == role_id]
    for loan in loans_to_remove:
        loans.remove(loan)
    save_balances(balances)
    save_loans(loans)
    embed = discord.Embed(
        description=f"> Le rôle {role.mention} a été supprimé de l'économie et du classement.{INVISIBLE_CHAR}",
        color=EMBED_COLOR
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, f"Le rôle {role.mention} a été supprimé de l'économie et du classement.")

def get_member_or_bot(guild, user_id):
    if user_id is None:
        return guild.me
    try:
        member_id = int(user_id)
        member = guild.get_member(member_id)
        if member:
            return member
        # Si c'est un rôle, retourne le rôle ou un objet factice
        role = discord.utils.get(guild.roles, id=member_id)
        if role:
            return role
    except Exception:
        pass
    return guild.me

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))