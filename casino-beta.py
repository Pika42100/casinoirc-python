############################################################################################
#     casino BOT- PAR Maxime                                                               #
#      Version 1.1                                                                        #
#                                                                                          #                                                                                    #
#    modification 31/05/2024:                                                              #
#                                                                                          #
#    ajout du ssl conexion securiser                                                       #
#                                                                                          #
#    ajout d'une identification au oret de nickserv                                        #
#                                                                                          #
#    ajoutle fet que le bot peux ce /oper (IRCOP) si c'est votre server                    #
#                                                                                          #
#    ajout de la commande !restart pour restart le bot                                     #
#                                                                                          #
#    ajout de la commande !demande #votre-salon pour fair rejoindre le bot sur votre salon #
#                                                                                          #
#    ajout de la commande !addadmin pour ajouter des administrateur au bot                 #
#                                                                                          #
#    ajout d'un fichier admins.txt ou son stocker les admins                               #
#                                                                                          #
#    ajout de la commande !deladmin pour supprimer un administrateur au bot                #
#                                                                                          #
#    ajoute de la commande !listadmin pour voir la liste des administrateur disponible     #
#                                                                                          #
#    version 1.2                                                                           #
#                                                                                          #
#    modification 30/09/2024:                                                              #
#                                                                                          #
#    ajout d'une page html des stats joueur                                                #
#                                                                                          #
#    ajout d'une anonce sur un salon pour inviter les users a jouer sur #casino            #
#                                                                                          #
#                                                                                          #
#    version 1.3                                                                           #
#                                                                                          #
#    modification 03/04/2025:                                                              #
#                                                                                          #
#                                                                                          #
#   correction de bug                                                                      #                                                       
#                                                                                          #
#                                                                                          #
#    casino bot en python  by Maxime   irc.extra-cool.fr https://extra-cool.fr/            #
############################################################################################

import sys
import os
import ssl
import irc
import socket
import re
import mariadb
import signal
import time
from datetime import datetime
import random
from colorama import Fore
from dotenv import load_dotenv
from datetime import datetime, timedelta
import threading 
import mysql.connector
import schedule
import pytz

# Définir la version du bot
version_bot = "casino BOT- PAR Maxime Version 1.2"  # pour le respect de mon travail merci de ne pas modifier cette ligne 

class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Écriture du Pid
with open('bot.pid', 'w', encoding='utf-8') as f:
    f.write(str(os.getpid()))

# Configuration de la base de données
db_host = "localhost"
db_user = "utilisateur" #a changer
db_password = "mot-de_pass" #a changer
db_name = "nom-database" #a changer

# Connexion à la base de données
try:
    conn = mariadb.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        database=db_name
    )
    cursor = conn.cursor()
except mariadb.Error as e:
    print(f"Erreur de connexion à la base de données: {e}")
    exit(1)


# Function to get current time in France and Quebec
def obtenir_heure():
    now = datetime.now(pytz.timezone('Europe/Paris'))
    heure_france = now.strftime("%Hh%M (et %S secondes)")
    
    now_quebec = now.astimezone(pytz.timezone('America/Toronto'))
    heure_quebec = now_quebec.strftime("%Hh%M")
    
    return f"[Heure] est à l'heure française (GMT+1). Heure actuelle : {heure_france}. Au Québec, il est {heure_quebec}."

# Function to randomly determine if the player wins or loses
def gagner_ou_perdre():
    return random.choice([True, False])

# Function to manage the casino command
def gestion_commande_casino(nom_utilisateur, commande):
    match = re.match(r"!casino(?: (\d+))?", commande)
    montant = int(match.group(1)) if match and match.group(1) else 10  # Default amount is 10
    
    solde_jeux = get_solde_jeux(nom_utilisateur)
    if solde_jeux is not None:
        if solde_jeux >= montant:
            gagne = gagner_ou_perdre()  # Determine if the player wins or loses
            if gagne:
                nouveau_solde_jeux = solde_jeux + montant * 2
                message = f"{Fore.BLUE}Vous avez gagné {montant} ! Votre nouveau solde en jeux est de {nouveau_solde_jeux}.{Fore.RESET}"
            else:
                nouveau_solde_jeux = solde_jeux - montant
                message = f"{Fore.RED}Vous avez perdu {montant} ! Votre solde en jeux est de {nouveau_solde_jeux}.{Fore.RESET}"
            
            # Update balance
            if mettre_a_jour_solde(nom_utilisateur, get_solde_banque(nom_utilisateur), nouveau_solde_jeux):
                enregistrer_partie(nom_utilisateur, "casino", montant, gagne)
                return message
            else:
                return f"{Fore.RED}Une erreur est survenue lors de la mise à jour du solde.{Fore.RESET}"
        else:
            return f"{Fore.RED}Solde en jeux insuffisant. Vous devez taper !transfert (montant) pour mettre des Extrazino dans votre solde de jeux pour jouer.{Fore.RESET}"
    else:
        return f"{Fore.RED}Utilisateur non trouvé. Veuillez d'abord vous enregistrer avec la commande !register.{Fore.RESET}"

# Command !heur to display the current time
def gestion_commande_heur(commande):
    if commande == "!heur":
        return obtenir_heure()
    else:
        return "Commande non reconnue. Utilisation : !heur"

# Function to handle commands
def gestion_commande(nom_utilisateur, commande):
    mots = commande.split()
    if mots[0] == "!heur":
        return gestion_commande_heur(commande)
    elif mots[0] == "!casino":
        return gestion_commande_casino(nom_utilisateur, commande)
    # Additional commands can be added here
    return "Commande invalide ou non reconnue."

# Automated announcements every hour and half-hour with a fun phrase
def annoncer_heure():
    while True:
        now = datetime.now(pytz.timezone('Europe/Paris'))
        minute = now.minute
        second = now.second
        
        if minute in [0, 30] and second == 0:
            phrases_sympas = [
                "C'est l'heure de se dégourdir les jambes !",
                "Une autre demi-heure vient de passer, continuez votre bon travail !",
                "Il est temps de prendre une petite pause, non ?",
                "Le temps file, profitez de chaque instant !",
                "C'est l'heure de sourire, même sans raison !"
            ]
            phrase = random.choice(phrases_sympas)
            heure_message = obtenir_heure()
            full_message = f"{heure_message} - {phrase}"
            print(full_message)  # Ici on affiche, mais vous pourriez utiliser un envoi de message spécifique au bot

        # Sleep for 1 second before checking again
        time.sleep(1)

# Start a separate thread for hourly announcements
annonce_thread = threading.Thread(target=annoncer_heure, daemon=True)
annonce_thread.start()


    

# Fonction pour vérifier si un utilisateur a un compte
def compte_existe(nom_utilisateur):
    try:
        cursor.execute("SELECT COUNT(*) FROM comptes WHERE nom_utilisateur = ?", (nom_utilisateur,))
        return cursor.fetchone()[0] > 0
    except mariadb.Error as e:
        print(f"Erreur lors de la vérification du compte : {e}")
        return False

# Fonction pour obtenir le nombre de joueurs inscrits
def nombre_joueurs_inscrits():
    try:
        cursor.execute("SELECT COUNT(*) FROM comptes")
        return cursor.fetchone()[0]
    except mariadb.Error as e:
        print(f"Erreur lors de la récupération du nombre de joueurs : {e}")
        return 0

# Fonction pour obtenir le nombre de parties jouées
def nombre_parties_jouees():
    try:
        print("Récupération du nombre de parties jouées...")  # Ligne de débogage
        cursor.execute("SELECT COUNT(*) FROM parties")
        return cursor.fetchone()[0]
    except mariadb.Error as e:
        print(f"Erreur lors de la récupération du nombre de parties jouées : {e}")
        return 0


# Fonction pour envoyer une notice à l'utilisateur qui rejoint sans compte, avec des couleurs IRC et du texte en gras
def envoyer_notice(bot_connection, utilisateur, message):
    bot_connection.send(f"NOTICE {utilisateur} :{message}\n".encode())


def enregistrer_partie(nom_utilisateur, jeu, montant_mise, gagne):
    try:
        print(f"Enregistrement de la partie pour {nom_utilisateur}...")
        cursor.execute("INSERT INTO parties (nom_utilisateur, jeu, montant_mise, gagne, date_partie) VALUES (?, ?, ?, ?, ?)",
                       (nom_utilisateur, jeu, montant_mise, gagne, datetime.now()))
        conn.commit()
        print(f"Partie enregistrée pour {nom_utilisateur}.")
    except mariadb.Error as e:
        print(f"Erreur lors de l'enregistrement de la partie : {e}")


# Fonction pour créer un compte utilisateur avec 1000 Extrazino à l'inscription
def creer_compte(nom_utilisateur):
    try:
        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT COUNT(*) FROM comptes WHERE nom_utilisateur = ?", (nom_utilisateur,))
        if cursor.fetchone()[0] > 0:
            print(f"Erreur : Le compte pour {nom_utilisateur} existe déjà.")
            return False

        # Créer le compte
        cursor.execute("INSERT INTO comptes (nom_utilisateur, solde_banque, solde_jeux, dernier_credit) VALUES (?, 1000, 0, ?)", (nom_utilisateur, datetime.now().date()))
        conn.commit()
        print(f"Compte {nom_utilisateur} créé avec succès.")
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de la création du compte : {e}")
        conn.rollback()
        return False

def generer_page_stats_joueurs():
    try:
        # Récupérer tous les comptes
        cursor.execute("SELECT nom_utilisateur, solde_banque, solde_jeux FROM comptes")
        joueurs = cursor.fetchall()

        # Commencer la construction de la page HTML avec styles CSS
        html_content = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="css/styles.css?v=1.0">
            <title>Statistiques des Joueurs</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f9;
                    color: #333;
                    margin: 0;
                    display: flex;
                    flex-direction: column;
                    min-height: 100vh;
                }
                h1 {
                    text-align: center;
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px 0;
                    margin-bottom: 20px;
                }
                table {
                    width: 70%;
                    margin: 0 auto;
                    border-collapse: collapse;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    background-color: #fff;
                }
                th, td {
                    padding: 12px;
                    text-align: center;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background-color: #4CAF50;
                    color: white;
                }
                tr:hover {
                    background-color: #f1f1f1;
                }
                td {
                    color: #555;
                }
                .footer {
                    text-align: center;
                    padding: 20px;
                    background-color: #4CAF50;
                    color: white;
                    margin-top: auto;
                }
                .commands {
                    margin: 20px auto;
                    width: 70%;
                    background-color: #e7f3fe;
                    padding: 15px;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                nav {
                    background-color: #333;
                    overflow: hidden;
                }
                nav a {
                    float: left;
                    display: block;
                    color: #f2f2f2;
                    text-align: center;
                    padding: 14px 16px;
                    text-decoration: none;
                }
                nav a:hover {
                    background-color: #ddd;
                    color: black;
                }
            </style>
        </head>
        <body>
            <header>
                <img src="images/logo.png" alt="Logo IRC" style="width: 150px;"> <!-- Ajustez le chemin et la taille -->
                <h1>Statistiques des Joueurs</h1>
            </header>
            <nav>
                <a href="index.php">Accueil</a>
                <a href="staff.html">Équipe</a>
                <a href="status.php">Statut</a>
                <a href="chat.html">Chat</a>
                <a href="download.html">Téléchargements</a>
                <a href="channels.php">Salons</a>
                <a href="github.html">GitHub</a>
                <a href="irc_stats.html">Statistiques salon</a>
                <a href="stats_joueurs.html">Statistiques Casino</a>
            </nav>
            <table>
                <tr>
                    <th>Nom d'utilisateur</th>
                    <th>Solde Banque</th>
                    <th>Solde Jeux</th>
                </tr>
        """

        # Ajouter chaque joueur dans le tableau HTML
        for joueur in joueurs:
            nom_utilisateur, solde_banque, solde_jeux = joueur
            html_content += f"""
                <tr>
                    <td>{nom_utilisateur}</td>
                    <td>{solde_banque} Extrazino</td>
                    <td>{solde_jeux} Extrazino</td>
                </tr>
            """

        # Section des commandes
        html_content += """
            </table>
            <div class="commands">
                <h2>Commandes disponibles</h2>
                <p><strong>!register [nom_utilisateur]</strong> : Créer un compte.</p>
                <p><strong>!solde [nom_utilisateur]</strong> : Voir le solde du compte.</p>
                <p><strong>!convertir [montant]</strong> : Convertir vos Extrazino de jeux en banque.</p>
                <p><strong>!casino [montant]</strong> : Jouer au jeu du casino (ex: !casino 50).</p>
                <p><strong>!roulette [nombre]</strong> : Jouer au jeu de la roulette.</p>
                <p><strong>!slots [montant]</strong> : Jouer aux machines à sous.</p>
                <p><strong>!des [montant]</strong> : Jouer au jeu de dés.</p>
                <p><strong>!transfert [montant]</strong> : Transfert des Extrazino de votre compte en banque vers votre compte de jeux.</p>
                <p>Rejoignez le salon <strong>#casino</strong> pour jouer !</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Casino IRC Python By Maxime - Tous droits réservés.</p>
            </div>
        </body>
        </html>
        """

        # Chemin de la page HTML à générer
        chemin_html = "/var/www/html/stats_joueurs.html"

        # Écrire le contenu HTML dans un fichier
        with open(chemin_html, "w") as file:
            file.write(html_content)

        print(f"Page HTML générée avec succès à l'emplacement: {chemin_html}")

    except mariadb.Error as e:
        print(f"Erreur lors de la génération de la page HTML: {e}")

# Exemple d'utilisation : Créer un compte puis générer la page HTML des stats
if creer_compte("Elias"):
    print("Compte Elias créé avec succès.")
else:
    print("Échec de la création du compte.")

# Générer la page HTML avec les statistiques des joueurs
generer_page_stats_joueurs()



# Ajouter une fonction pour vérifier si un utilisateur est enregistré
def est_enregistre(nom_utilisateur):
    try:
        cursor.execute("SELECT * FROM comptes WHERE nom_utilisateur=?", (nom_utilisateur,))
        row = cursor.fetchone()
        return row is not None
    except mariadb.Error as e:
        print(f"Erreur lors de la vérification de l'enregistrement de l'utilisateur: {e}")
        return False


# Fonction pour récupérer le solde d'un utilisateur
def get_solde(nom_utilisateur):
    try:
        cursor.execute("SELECT solde_banque, solde_jeux FROM comptes WHERE nom_utilisateur=?", (nom_utilisateur,))
        row = cursor.fetchone()
        if row:
            return row
        else:
            return None
    except mariadb.Error as e:
        print(f"Erreur lors de la récupération du solde: {e}")
        return None

# Fonction pour récupérer le solde en banque d'un utilisateur
def get_solde_banque(nom_utilisateur):
    try:
        cursor.execute("SELECT solde_banque FROM comptes WHERE nom_utilisateur=?", (nom_utilisateur,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None
    except mariadb.Error as e:
        print(f"Erreur lors de la récupération du solde en banque: {e}")
        return None

def ajouter_argent(nom_administrateur, commande):
    # Vérifie si l'utilisateur est un administrateur
    if nom_administrateur not in administrateurs:
        return f"{Fore.RED}Vous n'êtes pas autorisé à exécuter cette commande.{Fore.RESET}"
    
    mots = commande.split()
    if len(mots) != 3:
        return f"{Fore.RED}Commande invalide. Utilisation : !ajouterargent [nom_utilisateur] [montant]{Fore.RESET}"
    
    nom_utilisateur, montant_str = mots[1], mots[2]
    try:
        montant = int(montant_str)
    except ValueError:
        return f"{Fore.RED}Le montant doit être un nombre entier.{Fore.RESET}"
    
    # Appel à la fonction pour créditer le compte
    if crediter_compte(nom_utilisateur, montant):
        return f"{Fore.GREEN}Montant de {montant} Extrazino ajouté avec succès au compte de {nom_utilisateur}.{Fore.RESET}"
    else:
        return f"{Fore.RED}Erreur lors de l'ajout de Extrazino au compte de {nom_utilisateur}.{Fore.RESET}"

def crediter_compte(nom_utilisateur, montant):
    try:
        cursor.execute("SELECT solde_banque FROM comptes WHERE nom_utilisateur=?", (nom_utilisateur,))
        row = cursor.fetchone()
        if row:
            nouveau_solde_banque = row[0] + montant
            cursor.execute("UPDATE comptes SET solde_banque=? WHERE nom_utilisateur=?", (nouveau_solde_banque, nom_utilisateur))
            conn.commit()
            return True
        else:
            return False
    except mariadb.Error as e:
        print(f"{Fore.RED}Erreur lors de la mise à jour du solde en banque: {e}{Fore.RESET}")
        conn.rollback()
        return False


def acheter_article(nom_utilisateur, article, channel, irc):
    # Définir les prix spécifiques pour chaque article
    prix_articles = {
        "operateur": 20000,
        "halflop": 10000,
        "voice": 5000
    }

    # Obtenir le prix de l'article demandé
    prix_article = prix_articles.get(article, None)
    if prix_article is None:
        return f"{Fore.RED}Article inconnu. Choisissez entre 'operateur', 'halflop', 'voice'.{Fore.RESET}"

    solde_banque = get_solde_banque(nom_utilisateur)
    if solde_banque is None:
        return f"{Fore.RED}Utilisateur non trouvé. Veuillez d'abord vous enregistrer avec la commande !register.{Fore.RESET}"
    
    if solde_banque >= prix_article:
        nouveau_solde_banque = solde_banque - prix_article
        if mettre_a_jour_solde_banque(nom_utilisateur, nouveau_solde_banque):
            # Envoyer les commandes de mode selon l'article acheté
            if article == "operateur":
                irc.send(f"MODE {channel} +o {nom_utilisateur}\n".encode())  # Opérer l'utilisateur
            elif article == "halflop":
                irc.send(f"MODE {channel} +h {nom_utilisateur}\n".encode())  # Half-op l'utilisateur
            elif article == "voice":
                irc.send(f"MODE {channel} +v {nom_utilisateur}\n".encode())  # Voice l'utilisateur
            return f"{Fore.GREEN}Achat réussi : {article}. Vous êtes maintenant {article} sur {channel}. Nouveau solde en banque : {nouveau_solde_banque}{Fore.RESET}"
        else:
            return f"{Fore.RED}Erreur lors de la mise à jour du solde.{Fore.RESET}"
    else:
        return f"{Fore.RED}Solde insuffisant pour acheter {article}. Solde en banque : {solde_banque}{Fore.RESET}"

def gestion_commande(nom_utilisateur, commande):
    mots = commande.split()
    if mots[0] == "!acheter" and len(mots) == 2:
        article = mots[1]
        if article in ["autovoice", "halflop", "operateur"]:
            return acheter_article(nom_utilisateur, article)
        else:
            return f"{Fore.RED}Article inconnu. Veuillez choisir parmi 'autovoice', 'halflop', 'operateur'.{Fore.RESET}"
    return "Commande invalide ou non reconnue."

def gestion_commande(nom_utilisateur, commande):
    mots = commande.split()
    if mots[0] == "!deposer":
        if len(mots) == 2:
            montant = int(mots[1])
            if montant > 0:
                solde_jeux = get_solde_jeux(nom_utilisateur)
                if solde_jeux is not None and solde_jeux >= montant:
                    nouveau_solde_jeux = solde_jeux - montant
                    solde_banque = get_solde_banque(nom_utilisateur)
                    if solde_banque is not None:
                        nouveau_solde_banque = solde_banque + montant
                        if mettre_a_jour_solde(nom_utilisateur, nouveau_solde_banque, nouveau_solde_jeux):
                            return f"{Fore.BLUE}Vous avez déposé {montant} Extrazino de jeux dans votre compte en banque. Nouveau solde en banque : {nouveau_solde_banque}, Nouveau solde en jeux : {nouveau_solde_jeux}"
                        else:
                            return f"{Fore.RED}Une erreur est survenue lors du dépôt."
                    else:
                        return f"{Fore.RED}Utilisateur non trouvé veuillez d'abord vous enregistrer avec la commande !register."
                else:
                    return f"{Fore.RED}Solde en jeux insuffisant."
            else:
                return f"{Fore.RED}Le montant doit être supérieur à zéro."
        else:
            return f"{Fore.RED}Commande invalide. Utilisation : !deposer [montant]"
    elif mots[0] == "!transfert":
        if len(mots) == 2:
            montant = int(mots[1])
            return transfert_credit(nom_utilisateur, montant)
        else:
            return f"{Fore.RED}Commande invalide. Utilisation : !transfert [montant]"

    elif mots[0] == "!convertir":
        if len(mots) == 2:
            montant = int(mots[1])
            if montant > 0:
                solde_jeux = get_solde_jeux(nom_utilisateur)
                if solde_jeux is not None and solde_jeux >= montant:
                    nouveau_solde_jeux = solde_jeux - montant
                    solde_banque = get_solde_banque(nom_utilisateur)
                    if solde_banque is not None:
                        nouveau_solde_banque = solde_banque + montant
                        if mettre_a_jour_solde(nom_utilisateur, nouveau_solde_banque, nouveau_solde_jeux):
                            return f"{Fore.BLUE}Vous avez converti {montant} Extrazino de jeux en {montant} Extrazino en banque. Nouveau solde en banque : {nouveau_solde_banque}, Nouveau solde en jeux : {nouveau_solde_jeux}"
                        else:
                            return f"{Fore.RED}Une erreur est survenue lors de la conversion."
                    else:
                        return f"{Fore.RED}Utilisateur non trouvé veuillez d'abord vous enregistrer avec la commande !register."
                else:
                    return f"{Fore.RED}Solde en jeux insuffisant."
            else:
                return f"{Fore.RED}Le montant doit être supérieur à zéro."
        else:
            return f"{Fore.RED}Commande invalide. Utilisation : !convertir [montant]"
    elif commande.startswith("!solde_banque"):
        solde_banque = get_solde_banque(nom_utilisateur)
        if solde_banque is not None:
            return f"{Fore.BLUE}Solde en banque : {solde_banque}"
        else:
            return f"{Fore.RED}Utilisateur non trouvé veuillez d'abord vous enregistrer avec la commande !register."
    elif commande.startswith("!solde_jeux"):
        solde_jeux = get_solde_jeux(nom_utilisateur)
        if solde_jeux is not None:
            return f"{Fore.BLUE}Solde en jeux : {solde_jeux}"
        else:
            return f"{Fore.RED}Utilisateur non trouvé veuillez d'abord vous enregistrer avec la commande !register."
    if commande.startswith("!solde_banque"):
        solde_banque = get_solde_banque(nom_utilisateur)
        if solde_banque is not None:
            return f"Solde en banque : {solde_banque}"
        else:
            return "Utilisateur non trouvé veuillez d'abord vous enregistrer avec la commande !register."

    mots = commande.split()
    if mots[0] == "!deposer":
        if len(mots) == 2:
            montant = int(mots[1])
            if montant > 0:
                solde_banque = get_solde_banque(nom_utilisateur)
                if solde_banque is not None:
                    nouveau_solde_banque = solde_banque + montant
                    if mettre_a_jour_solde_banque(nom_utilisateur, nouveau_solde_banque):
                        return f"Vous avez déposé {montant} Extrazino dans votre compte en banque. Nouveau solde en banque : {nouveau_solde_banque}"
                    else:
                        return "Une erreur est survenue lors du dépôt."
                else:
                    return "Utilisateur non trouvé veuillez d'abord vous enregistrer avec la commande !register."
            else:
                return "Le montant doit être supérieur à zéro."
        else:
            return "Commande invalide. Utilisation : !deposer [montant]"
    elif commande.startswith("!solde_banque"):
        solde_banque = get_solde_banque(nom_utilisateur)
        if solde_banque is not None:
            return f"Solde en banque : {solde_banque}"
        else:
            return "Utilisateur non trouvé veuillez d'abord vous enregistrer avec la commande !register."

    if not est_enregistre(nom_utilisateur):  # Vérifier si le joueur est enregistré
        return f"{Fore.RED}Vous devez d'abord vous enregistrer avec !register pour jouer.{Fore.END}"


def get_solde_jeux(nom_utilisateur):
    try:
        cursor.execute("SELECT solde_jeux FROM comptes WHERE nom_utilisateur=?", (nom_utilisateur,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return None
    except mariadb.Error as e:
        print(f"{Fore.RED}Erreur lors de la récupération du solde de jeux: {e}{Fore.END}")
        return None

def mettre_a_jour_solde_banque(nom_utilisateur, nouveau_solde_banque):
    try:
        cursor.execute("UPDATE comptes SET solde_banque=? WHERE nom_utilisateur=?", (nouveau_solde_banque, nom_utilisateur))
        conn.commit()
        return True
    except mariadb.Error as e:
        print(f"{Fore.RED}Erreur lors de la mise à jour du solde en banque: {e}{Fore.END}")
        conn.rollback()
        return False

def mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux):
    try:
        cursor.execute("UPDATE comptes SET solde_banque=?, solde_jeux=? WHERE nom_utilisateur=?", (solde_banque, solde_jeux, nom_utilisateur))
        conn.commit()  # Assurez-vous que les modifications sont engagées
        generer_page_stats_joueurs()  # Générer la page des stats après la mise à jour
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de la mise à jour du solde: {e}")
        return False


def transfert_credit(nom_utilisateur, montant):
    solde_banque = get_solde_banque(nom_utilisateur)
    solde_jeux = get_solde_jeux(nom_utilisateur)

    if solde_banque is None:
        return f"{Fore.RED}Utilisateur non trouvé. Veuillez d'abord vous enregistrer avec la commande !register."

    if montant <= 0:
        return f"{Fore.RED}Le montant doit être supérieur à zéro."

    if solde_banque < montant:
        return f"{Fore.RED}Solde insuffisant dans votre compte en banque."

    nouveau_solde_banque = solde_banque - montant
    nouveau_solde_jeux = solde_jeux + montant

    if mettre_a_jour_solde(nom_utilisateur, nouveau_solde_banque, nouveau_solde_jeux):
        return f"{Fore.BLUE}Vous avez transféré {montant} Extrazino de votre compte en banque vers votre compte de jeux. Nouveau solde en banque : {nouveau_solde_banque}, Nouveau solde en jeux : {nouveau_solde_jeux}"
    else:
        return f"{Fore.RED}Une erreur est survenue lors du transfert de Extrazino."



def gestion_commande_stats(nom_utilisateur, commande):
    print(f"Commande reçue: {commande}")  # Pour le débogage

    if commande == "!statscas":
        print(f"{nom_utilisateur} a demandé à voir les statistiques.")
        return f"Voici les statistiques des joueurs: [Cliquez ici pour voir les stats](http://51.38.113.103/stats_joueurs.html)"
    

# Testez la fonction manuellement
response = gestion_commande_casino("Maxime", "!statscas")
print(response)  # Cela devrait afficher le message avec le lien


def jeu_de_des(nom_utilisateur, montant_mise):
    if montant_mise <= 0:
        return f"{Fore.RED}Le montant de la mise doit être supérieur à zéro.{Fore.RESET}"

    solde_jeux = get_solde_jeux(nom_utilisateur)
    if solde_jeux is None:
        return f"{Fore.RED}Utilisateur non trouvé. Veuillez d'abord vous enregistrer avec la commande !register.{Fore.RESET}"

    if solde_jeux < montant_mise:
        return f"{Fore.RED}Solde insuffisant.{Fore.RESET}"

    # Lancement du dé
    resultat = random.randint(1, 6)
    if resultat == 6:
        gain = montant_mise * 2  # Gain: double de la mise si le résultat est 6
        nouveau_solde_jeux = solde_jeux + gain
        message = f"{Fore.GREEN}Vous avez lancé un 6 et gagné {gain} Extrazino!{Fore.RESET}"
    else:
        nouveau_solde_jeux = solde_jeux - montant_mise
        message = f"{Fore.RED}Vous avez lancé un {resultat}. Vous perdez votre mise de {montant_mise} Extrazino.{Fore.RESET}"

    # Mise à jour du solde en jeux après le jeu
    if mettre_a_jour_solde(nom_utilisateur, get_solde_banque(nom_utilisateur), nouveau_solde_jeux):
        message += f" Nouveau solde en jeux : {nouveau_solde_jeux}"
    else:
        message = f"{Fore.RED}Une erreur est survenue lors de la mise à jour du solde.{Fore.RESET}"

    # Enregistrer la partie dans la base de données
    enregistrer_partie(nom_utilisateur, "dés", montant_mise, resultat == 6)

    return message



def gestion_commande_roulette(nom_utilisateur, commande):
    mots = commande.split()
    if mots[0] == "!roulette":
        if len(mots) == 2:
            montant = int(mots[1])
            solde_jeux = get_solde_jeux(nom_utilisateur)
            if solde_jeux is not None:
                if solde_jeux >= montant:
                    resultat_jeu = jeu_roulette()
                    numero_gagnant, couleur, parite = resultat_jeu
                    if gagner_ou_perdre():
                        nouveau_solde_jeux = solde_jeux + montant * 2
                        message = f"La bille est tombée sur le {numero_gagnant} ({couleur}, {parite}). Vous avez gagné {montant} Extrazino !"
                        gagne = True
                    else:
                        nouveau_solde_jeux = solde_jeux - montant
                        message = f"La bille est tombée sur le {numero_gagnant} ({couleur}, {parite}). Vous avez perdu {montant} Extrazino !"
                        gagne = False

                    if mettre_a_jour_solde(nom_utilisateur, get_solde_banque(nom_utilisateur), nouveau_solde_jeux):
                        message += " Veuillez attendre 30 secondes avant de jouer à nouveau."
                        irc.send(f"PRIVMSG {channel} :{message}\n".encode())
                        time.sleep(30)
                    else:
                        message = "Une erreur est survenue lors de la mise à jour du solde."

                    # Enregistrer la partie dans la base de données
                    enregistrer_partie(nom_utilisateur, "roulette", montant, gagne)
                else:
                    message = "Solde insuffisant dans votre jeu."
            else:
                message = "Utilisateur non trouvé veuillez d'abord vous enregistrer avec la commande !register."
        else:
            message = "Commande invalide. Utilisation : !roulette [montant]"
    else:
        message = "Commande invalide."
    return message


# Définition de la variable globale symboles
symboles = {
    "🍒": 10,
    "🍊": 20,
    "🍋": 30,
    "🍉": 40,
    "🍇": 50,
    "🔔": 75,
    "💎": 100,
    "🎰": 200
}

# Initialisation de la variable globale jackpot
jackpot = 1

def jeu_slots(nom_utilisateur, montant_mise):
    solde_jeux = get_solde_jeux(nom_utilisateur)

    if solde_jeux is None:
        return "Utilisateur non trouvé. Veuillez d'abord vous enregistrer avec la commande !register."

    if solde_jeux >= montant_mise:
        solde_jeux -= montant_mise
        symboles_tires = [random.choice(list(symboles.keys())) for _ in range(3)]
        symboles_alignes = len(set(symboles_tires))

        if jackpot == 1 and symboles_alignes == 1:
            jackpot_amount = random.randint(1000, 10000)
            solde_jeux += jackpot_amount
            message = f"Jackpot !! Vous avez gagné {jackpot_amount} Extrazino de jeux ! Résultat: {' - '.join(symboles_tires)}."
            gagne = True
        elif symboles_alignes == 2:
            gain = montant_mise * 2
            solde_jeux += gain
            message = f"Bravo ! Vous avez gagné {gain} Extrazino de jeux ! Résultat: {' - '.join(symboles_tires)}."
            gagne = True
        else:
            message = f"Dommage ! Vous n'avez rien gagné cette fois-ci. Résultat: {' - '.join(symboles_tires)}."
            gagne = False

        # Mise à jour du solde en jeux
        if mettre_a_jour_solde(nom_utilisateur, get_solde_banque(nom_utilisateur), solde_jeux):
            message += " Veuillez attendre 30 secondes avant de jouer à nouveau."
        else:
            return "Une erreur est survenue lors de la mise à jour du solde."

        # Enregistrement de la partie
        enregistrer_partie(nom_utilisateur, "slots", montant_mise, gagne)
    else:
        message = "Solde insuffisant dans votre jeu pour effectuer cette mise."

    return message



articles = {
    "Livre": 50,
    "Montre": 100,
    "Console de jeu": 200,
    "Vélo": 300,
    "Smartphone": 500
}

def jeu_juste_prix(nom_utilisateur, montant_mise):
    solde_jeux = get_solde_jeux(nom_utilisateur)
    
    if solde_jeux is not None and solde_jeux >= montant_mise:
        solde_jeux -= montant_mise
        prix_a_deviner = random.randint(1, 100)
        numero_propose = random.randint(1, 100)

        if numero_propose == prix_a_deviner:
            gain = montant_mise * 2
            solde_jeux += gain
            message = f"Bravo ! Vous avez deviné le juste prix ({prix_a_deviner}) ! Vous avez gagné {gain} Extrazino de jeux."
            gagne = True
        else:
            message = f"Dommage ! Le juste prix était {prix_a_deviner}. Vous avez perdu votre mise."
            gagne = False

        if mettre_a_jour_solde(nom_utilisateur, get_solde_banque(nom_utilisateur), solde_jeux):
            message += " Veuillez attendre 30 secondes avant de jouer à nouveau."
            irc.send(f"PRIVMSG {channel} :{message}\n".encode())
            time.sleep(30)
        else:
            message = "Une erreur est survenue lors de la mise à jour du solde."
            gagne = False  # Si une erreur survient, on considère que le joueur n'a pas gagné
    else:
        message = "Solde insuffisant dans votre jeu pour effectuer cette mise."
        gagne = False

    # Enregistrer la partie dans la base de données
    enregistrer_partie(nom_utilisateur, "juste_prix", montant_mise, gagne)
    
    return message


def attribuer_article(montant_mise):
    for article, valeur in articles.items():
        if montant_mise * 2 >= valeur:  
            return article
    return "Aucun article"

# Function to randomly determine if the player wins or loses
def gagner_ou_perdre():
    return random.choice([True, False])

def jeu_roulette():
    numero_gagnant = random.randint(0, 36)

    if numero_gagnant % 2 == 0:
        parite = "pair"
    else:
        parite = "impair"

    if numero_gagnant == 0:
        couleur = "vert"
    elif (numero_gagnant >= 1 and numero_gagnant <= 10) or (numero_gagnant >= 19 and numero_gagnant <= 28):
        if numero_gagnant % 2 == 0:
            couleur = "noir"
        else:
            couleur = "rouge"
    else:
        if numero_gagnant % 2 == 0:
            couleur = "rouge"
        else:
            couleur = "noir"

    return numero_gagnant, couleur, parite

# Définir une liste d'administrateurs autorisés
administrateurs = ["Maxime", "KoS_"]  # Remplacez ceci par les noms des administrateurs réels

# Ajouter une fonction pour envoyer de l'aide
def envoyer_aide(nom_utilisateur):
    if nom_utilisateur in administrateurs:
        irc.send(f"PRIVMSG {nom_utilisateur} :\x0304Commandes disponibles (administrateur) :\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !register [nom_utilisateur] : Créer un compte.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !solde [nom_utilisateur] : Voir le solde du compte.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !convertir [montant] converti vos Extrazino de jeux et les met en banque.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !transfert [montant] : transfert des Extrazino de votre compte en banque vers votre compte de jeux.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !roulette [nombre] : jouer au jeux de la roulette.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !casino [montant] : joue au jeu du casino (ex: !casino 50).\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !slots [montant] : joue au machine a sous.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !des [montant] : joue au jeux de dès.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !quit : Déconnecter le bot.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !join [#channel] : fait joindre le bot sur un channel.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !part [#channel] : fait Partire le bot d'un channel.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !supprime [nom_utilisateur] : Supprimer un compte.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !ajouterargent [nom_utilisateur] [montant] : Extrazinoe de l'agennt sur le compte d'un joueur.\n".encode())
    else:
        irc.send(f"PRIVMSG {nom_utilisateur} :\x0304Commandes disponibles :\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !register [nom_utilisateur] : Créer un compte.(ex: register Maxime)\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !casino [montant] : joue au jeu du casino (ex: !casino 50).\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !solde [nom_utilisateur] : Voir le solde du compte.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !convertir [montant] converti vos Extrazino de jeux et les met en banque.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !transfert [montant] : transfert des Extrazino de votre compte en banque vers votre compte de jeux.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !roulette [nombre] : jouer au jeux de la roulette.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !slots [montant] : joue au machine a sous.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !des [montant] : joue au jeux de dès.\n".encode())

# Ajouter une commande pour supprimer un compte
def supprimer_compte(administrateur):
    try:
        cursor.execute("DELETE FROM comptes WHERE nom_utilisateur=?", (administrateur,))
        conn.commit()
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de la suppression du compte: {e}")
        conn.rollback()
        return False

# Configuration IRC changer les infos
server = "irc.extra-cool.fr"
port = 6697  # Port TLS/SSL pour IRC
channel = "#extra-cool"
logs_channel = "#logs"
casino_channel = "#casino"
bot_name = "CasinoBot"
bot_channels = set()
irc_channels = ["#extra-cool", "#casino", "#casinoadmin"]
nickname = "Extraino"
password = "votre-mot-de-pass"
nickserv_password = "votre-mot(de-pass"
ircop_password = "votre-mot-pass"  # Ajoutez votre mot de passe IRCop ici
admins_file = "admins.txt"

# Lire les administrateurs depuis un fichier
def lire_admins():
    if not os.path.exists(admins_file):
        return set()
    with open(admins_file, "r") as f:
        return set(line.strip() for line in f)


# Lire les administrateurs depuis un fichier
def lire_admins():
    if not os.path.exists(admins_file):
        return set()
    with open(admins_file, "r") as f:
        return set(line.strip() for line in f)

admin_users = lire_admins()
print("Admins initiaux : ", admin_users)  # Debugging output

# Enregistrer les administrateurs dans un fichier
def enregistrer_admins():
    with open(admins_file, "w") as f:
        for admin in admin_users:
            f.write(f"{admin}\n")
    print("Admins enregistrés : ", admin_users)  # Debugging output

# Variable pour activer ou désactiver le mode débogage
debug_mode = True

# Fonction pour logger les commandes
def log_commande(message):
    irc.send(f"PRIVMSG {logs_channel} :{message}\n".encode())

# Fonction pour se connecter et s'identifier
def identify_and_oper():
    # Identifier auprès de NickServ
    irc.send(f"PRIVMSG NickServ :IDENTIFY {nickserv_password}\n".encode())
    log_commande("[info]==> Identification auprès de NickServ envoyée.")
    time.sleep(5)  # Attendre un peu pour s'assurer que l'identification est traitée

    # Obtenir les privilèges d'opérateur (IRCop)
    irc.send(f"OPER {nickname} {ircop_password}\n".encode())
    log_commande("[info]==> Commande OPER envoyée pour obtenir les privilèges IRCop.")
    time.sleep(5)  # Attendre un peu pour s'assurer que la commande est traitée

    # Obtenir les privilèges d'opérateur de canal
    irc.send(f"PRIVMSG ChanServ :OP {nickname}\n".encode())
    log_commande("[info]==> Commande OP envoyée à ChanServ.")

# Fonction pour traiter la demande et envoyer un message à #casinoadmin
def traiter_demande(sender, channel_demande):
    log_message = f"[info]==> {sender} a fait une demande aux admins pour rejoindre le salon {channel_demande}"
    print(log_message)  # Afficher pour le débogage
    irc.send(f"PRIVMSG #casinoadmin :{log_message}\n".encode())
    response = irc.recv(2048).decode("UTF-8")
    print(response)  # Afficher la réponse du serveur pour le débogage
    log_commande(log_message)
    
    # Faire rejoindre le salon demandé
    irc.send(f"JOIN {channel_demande}\n".encode())
    bot_channels.add(channel_demande)
    log_commande(f"[info]==> Bot a rejoint le salon {channel_demande}")

# Fonction pour redémarrer le bot
def restart_bot():
    log_commande("[info]==> Redémarrage du bot...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

# Fonction pour ajouter un administrateur
def ajouter_admin(nouveau_admin, sender):
    if sender not in admin_users:
        irc.send(f"PRIVMSG {sender} :Vous n'avez pas les droits pour ajouter un administrateur.\n".encode())
        log_commande(f"Ajout d'administrateur refusé pour {sender}")
        return
    if nouveau_admin in admin_users:
        irc.send(f"PRIVMSG {sender} :{nouveau_admin} est déjà un administrateur.\n".encode())
        log_commande(f"Ajout d'administrateur échoué: {nouveau_admin} est déjà administrateur")
        return
    admin_users.add(nouveau_admin)
    enregistrer_admins()  # Enregistrer les administrateurs après ajout
    irc.send(f"PRIVMSG {sender} :{nouveau_admin} a été ajouté comme administrateur.\n".encode())
    log_commande(f"{nouveau_admin} ajouté comme administrateur par {sender}")

# Fonction pour supprimer un administrateur
def supprimer_admin(admin_a_supprimer, sender):
    if sender not in admin_users:
        irc.send(f"PRIVMSG {sender} :Vous n'avez pas les droits pour supprimer un administrateur.\n".encode())
        log_commande(f"Suppression d'administrateur refusée pour {sender}")
        return
    if admin_a_supprimer not in admin_users:
        irc.send(f"PRIVMSG {sender} :{admin_a_supprimer} n'est pas un administrateur.\n".encode())
        log_commande(f"Suppression d'administrateur échouée: {admin_a_supprimer} n'est pas administrateur")
        return
    admin_users.remove(admin_a_supprimer)
    enregistrer_admins()  # Enregistrer les administrateurs après suppression
    irc.send(f"PRIVMSG {sender} :{admin_a_supprimer} a été supprimé des administrateurs.\n".encode())
    log_commande(f"{admin_a_supprimer} supprimé des administrateurs par {sender}")


# Fonction pour envoyer la liste des administrateurs
def lister_admins(sender, channel):
    admins_list = ", ".join(admin_users)
    irc.send(f"PRIVMSG {channel} :Administrateurs actuels : {admins_list}\n".encode())
    log_commande(f"Liste des administrateurs demandée par {sender}: {admins_list}")


# Création de la socket pour la connexion IRC
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((server, port))

# Envelopper la socket dans une couche SSL/TLS
irc = ssl.wrap_socket(sock)

irc.send(f"USER {bot_name} 0 * :{bot_name}\n".encode())
irc.send(f"NICK {bot_name}\n".encode())

registered = False

while not registered:
    message = irc.recv(2048).decode("UTF-8")
    print(message)  # Afficher le message pour le débogage

    # Répondre aux PINGs du serveur pour garder la connexion active
    if "PING" in message:
        cookie = message.split()[1]
        irc.send(f"PONG {cookie}\n".encode())
    
    # Vérifier si le bot est enregistré
    if "001" in message:
        registered = True

# S'identifier auprès de NickServ et obtenir les privilèges d'opérateur
identify_and_oper()

# Rejoindre les salons définis
irc.send(f"JOIN {channel}\n".encode())
irc.send(f"JOIN {logs_channel}\n".encode())
irc.send(f"JOIN {casino_channel}\n".encode())

for channel in irc_channels:
    irc.send(f"JOIN {channel}\n".encode())
    bot_channels.add(channel)

# Fonction pour envoyer l'annonce toutes les 5 minutes
def send_casino_announcement():
    while True:
        try:
            # Message avec couleur rouge
            message = "\x03" + "04" + "Rejoignez-nous sur #casino pour jouer au casino!"  # Couleur 04 (rouge)
            irc.send(f"PRIVMSG #extra-cool :{message}\n".encode()) # modifier votre salon 
            print("Message envoyé avec succès à #extra-cool")
            time.sleep(300)  # Attendre 300 secondes (5 minutes) avant d'envoyer le prochain message
        except Exception as e:
            print(f"Erreur lors de l'envoi du message : {e}")

# Lancer l'annonce dans un thread séparé
announcement_thread = threading.Thread(target=send_casino_announcement)
announcement_thread.daemon = True  # Le thread se ferme lorsque le programme principal se ferme
announcement_thread.start()



# Fonction pour vérifier si un compte existe
def compte_existe(nom_utilisateur):
    try:
        # Connexion à la base de données
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()

        # Requête pour vérifier si l'utilisateur existe
        cursor.execute(f"SELECT COUNT(*) FROM comptes WHERE nom_utilisateur='{nom_utilisateur}'")
        result = cursor.fetchone()
        
        return result[0] > 0  # Retourne True si l'utilisateur existe, sinon False
    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données: {err}")
        return False
    finally:
        cursor.close()
        conn.close()


# Boucle principale pour traiter les messages
# Ajout à la section où les messages sont traités dans la boucle principale

# Boucle principale pour traiter les messages
while True:
    message = irc.recv(2048).decode("utf-8", errors="replace")
    print(message)  # Afficher le message pour le débogage

    # Répondre aux PINGs du serveur pour garder la connexion active
    if "PING" in message:
        cookie = message.split()[1]
        irc.send(f"PONG {cookie}\n".encode())
        log_commande(f"PING/PONG maintenu avec {cookie}")

    # Gérer le message d'erreur spécifique pour le salon #logs
    if "404" in message and logs_channel in message:
        print(f"[info]==>Erreur : Le bot ne peut pas poster dans {logs_channel} en raison de restrictions.")
        irc.send(f"JOIN {logs_channel}\n".encode())  # Essayer de rejoindre à nouveau si non présent
        irc.send(f"JOIN {casino_channel}\n".encode())
        irc.send("JOIN #casinoadmin\n".encode())
        continue

    # Détection des messages de type JOIN
    if "JOIN" in message:
        join_match = re.match(r"^:(.*?)!.*JOIN\s+:(#\S+)", message)
        if join_match:
            utilisateur = join_match.group(1)
            channel = join_match.group(2)

            # Si l'utilisateur rejoint le salon #casino
            if channel == "#casino":
                if not compte_existe(utilisateur):
                    # Récupérer le nombre de joueurs inscrits et de parties jouées
                    nombre_joueurs = nombre_joueurs_inscrits()
                    nombre_parties = nombre_parties_jouees()

                    # Envoi d'une notice si l'utilisateur n'a pas de compte
                    message_notice = (
                        f"\x0304Salut \x02{utilisateur}\x02\x03 ! Aucun compte Maxino n'a été trouvé sous ton pseudo. "
                        f"\x0302\x02Si c'est la première fois que tu viens, tape !register pour créer ton compte\x02\x03 et commencer à jouer. "
                        f"\x0310Actuellement, il y a \x02{nombre_joueurs}\x02 personnes inscrites et \x02{nombre_parties}\x02 parties jouées. "
                        f"\x0310\x02Bonne chance ^^\x02"
                    )
                    envoyer_notice(irc, utilisateur, message_notice)

    # Détection des messages de type PART
    if "PART" in message:
        part_match = re.match(r"^:(.*?)!.*PART\s+(#\S+)", message)
        if part_match:
            user = part_match.group(1)
            channel = part_match.group(2)
            log_message = f"[info]==> {user} a quitté le salon {channel}"
            print(log_message)  # Afficher pour le débogage
            irc.send(f"PRIVMSG {logs_channel} :{log_message}\n".encode())
            log_commande(log_message)


    elif "PRIVMSG" in message:
        sender_match = re.match(r"^:(.*?)!", message)
        channel_match = re.search(r"PRIVMSG (#\S+)", message)
        msg_match = re.search(r"PRIVMSG #\S+ :(.*)", message)

        if sender_match and channel_match and msg_match:
            sender = sender_match.group(1)
            channel = channel_match.group(1)
            msg = msg_match.group(1).strip()

            # Log toutes les commandes reçues
            log_commande(f"[info]==> Commande reçue de {sender} sur {channel}: {msg}")

            # Gestion de la commande !aide
            if msg.startswith("!aide"):
                envoyer_aide(sender)  # Appel de la fonction pour envoyer les messages d'aide
                log_commande(f"[HELP]==>Commande d'aide demandée par {sender}")

            # Gestion de la commande !demande
            if msg.startswith("!demande"):
                parts = msg.split()
                if len(parts) > 1:
                    channel_demande = parts[1]
                    traiter_demande(sender, channel_demande)
                else:
                    irc.send(f"PRIVMSG {channel} :Syntaxe: !demande <nom_du_channel>\n".encode())

            # Gestion de la commande !version
            elif msg.startswith("!version"):  # Ajout de la commande !version
                irc.send(f"PRIVMSG {channel} :Version actuelle du bot : {version_bot}\n".encode())
                log_commande(f"[info]==> Version du bot demandée par {sender}: {version_bot}")

            # Gestion de la commande !restart
            elif msg.startswith("!recas") and sender in administrateurs:  # Vérification des privilèges
                irc.send(f"PRIVMSG {channel} :Le bot va redémarrer...\n".encode())
                log_commande(f"[info]==> Commande de redémarrage reçue de {sender}")
                restart_bot()
            elif msg.startswith("!recas"):
                irc.send(f"PRIVMSG {channel} :Désolé {sender}, vous n'avez pas les droits pour redémarrer le bot.\n".encode())
                log_commande(f"[ERREUR]==>Commande de redémarrage refusée pour {sender}")

            # Gestion de la commande !addadmin
            elif msg.startswith("!addadmin") and sender in administrateurs:  # Vérification des privilèges
                parts = msg.split()
                if len(parts) > 1:
                    nouveau_admin = parts[1]
                    ajouter_admin(nouveau_admin, sender)
                else:
                    irc.send(f"PRIVMSG {channel} :Syntaxe: !addadmin <nick>\n".encode())
                    log_commande(f"Commande !addadmin incorrecte par {sender}")
            elif msg.startswith("!addadmin"):
                irc.send(f"PRIVMSG {channel} :Désolé {sender}, vous n'avez pas les droits pour ajouter un administrateur.\n".encode())
                log_commande(f"Commande !addadmin refusée pour {sender}")

            # Détection de la commande !deladmin
            elif msg.startswith("!deladmin"):
                parts = msg.split()
                if len(parts) > 1:
                    admin_a_supprimer = parts[1]
                    supprimer_admin(admin_a_supprimer, sender)
                else:
                    irc.send(f"PRIVMSG {channel} :Syntaxe: !deladmin <nick>\n".encode())
                    log_commande(f"Commande !deladmin incorrecte par {sender}")

            elif msg.startswith("!listadmin"):
                lister_admins(sender, channel)

            if msg.startswith("!register"):
                mots = msg.split()

                # Si un nom d'utilisateur est fourni, l'utiliser, sinon utiliser le pseudo de l'expéditeur
                if len(mots) >= 2:
                    nom_utilisateur = mots[1]  # Si un pseudo est fourni
                else:
                    nom_utilisateur = sender  # Utiliser le pseudo de l'expéditeur par défaut

                # Vérifier si le compte existe déjà (fonction à implémenter selon ta logique)
                if not compte_existe(nom_utilisateur):
                    if creer_compte(nom_utilisateur):
                        irc.send(f"PRIVMSG {channel} :Compte {nom_utilisateur} créé avec succès.\n".encode())
                        log_commande(f"[info]==> Compte {nom_utilisateur} créé avec succès par {sender}")
                    else:
                        irc.send(f"PRIVMSG {channel} :Erreur lors de la création du compte.\n".encode())
                        log_commande(f"[ERREUR]==> Erreur lors de la création du compte pour {nom_utilisateur} par {sender}")
                else:
                    irc.send(f"PRIVMSG {channel} :Le compte {nom_utilisateur} existe déjà.\n".encode())
                    log_commande(f"[ERREUR]==> Tentative de création de compte déjà existant par {sender}")

            elif msg.startswith("!solde"):
                mots = msg.split()

                # Si un nom d'utilisateur est fourni, l'utiliser, sinon utiliser le pseudo de l'expéditeur (sender)
                if len(mots) >= 2:
                    nom_utilisateur = mots[1]  # Si l'utilisateur fournit un pseudo
                else:
                    nom_utilisateur = sender  # Sinon, utiliser le pseudo de l'expéditeur

                solde = get_solde(nom_utilisateur)

                if solde:
                    solde_banque, solde_jeux = solde
                    irc.send(f"PRIVMSG {channel} :Solde en banque : {solde_banque}, Solde en jeux : {solde_jeux}\n".encode())
                    log_commande(f"[info]==> Solde vérifié pour {nom_utilisateur} par {sender}")
                else:
                    irc.send(f"PRIVMSG {channel} :Utilisateur non trouvé, veuillez d'abord vous enregistrer avec la commande !register.\n".encode())
                    log_commande(f"[ERREUR]==> Utilisateur non trouvé pour vérification de solde par {sender}")

            elif msg.startswith("!casino"):
                mots = msg.split()
                if len(mots) >= 2:
                    nom_utilisateur = sender
                    commande = msg
                    response = gestion_commande_casino(nom_utilisateur, commande)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !casino [montant]\n".encode())

            elif msg.startswith("!roulette"):
                mots = msg.split()
                if len(mots) >= 2:
                    nom_utilisateur = sender
                    commande = msg
                    response = gestion_commande_roulette(nom_utilisateur, commande)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !roulette [montant]\n".encode())

            elif msg.startswith("!slots"):
                mots = msg.split()
                if len(mots) == 2:
                    montant_mise = int(mots[1])
                    response = jeu_slots(sender, montant_mise)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !slots [montant]\n".encode())

            # Gestion des commandes administratives
            elif msg.startswith("!supprimer"):
                if sender in administrateurs:
                    mots = msg.split()
                    if len(mots) >= 2:
                        nom_utilisateur = mots[1]
                        if supprimer_compte(nom_utilisateur):
                            irc.send(f"PRIVMSG {channel} :Compte {nom_utilisateur} supprimé avec succès.\n".encode())
                        else:
                            irc.send(f"PRIVMSG {channel} :Erreur lors de la suppression du compte.\n".encode())
                    else:
                        irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !supprimer [nom_utilisateur]\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Vous n'êtes pas autorisé à exécuter cette commande.\n".encode())

            if msg.startswith("!transfert"):
                mots = msg.split()
                if len(mots) == 2:
                    montant = int(mots[1])
                    response = gestion_commande(sender, msg)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !transfert [montant]\n".encode())
            if msg.startswith("!solde_banque"):
                response = gestion_commande(sender, msg)
                irc.send(f"PRIVMSG {channel} :{response}\n".encode())
            if msg.startswith("!deposer") or msg.startswith("!solde_banque"):
                response = gestion_commande(sender, msg)
                irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                # Dans la boucle principale
            if msg.startswith("!deposer") or msg.startswith("!convertir") or msg.startswith("!banque") or msg.startswith("!solde_jeux"):
                response = gestion_commande(sender, msg)
                irc.send(f"PRIVMSG {channel} :{response}\n".encode())
            elif msg.startswith("!aide"):
                envoyer_aide(sender)
                    # Intégration de la commande pour jouer au Juste Prix
            elif msg.startswith("!juste_prix"):
                mots = msg.split()
                if len(mots) == 2:
                    montant_mise = int(mots[1])
                    nom_utilisateur = sender
                    response = jeu_juste_prix(nom_utilisateur, montant_mise)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !juste_prix [montant_mise]\n".encode())

            elif msg.startswith("!ajouterargent"):
                response = ajouter_argent(sender, msg)
                irc.send(f"PRIVMSG {channel} :{response}\n".encode())

            elif msg.startswith("!acheter"):
                mots = msg.split()
                if len(mots) == 2:
                    article = mots[1]
                    if article in ["operateur", "halflop", "voice"]:
                        response = acheter_article(sender, article, channel, irc)
                        irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                    else:
                        irc.send(f"PRIVMSG {channel} :Article inconnu. Choisissez entre 'operateur', 'halflop', 'voice'.\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !acheter [article]\n".encode())

                # Gestion de la commande pour jouer au jeu de dés
            elif msg.startswith("!des"):
                mots = msg.split()
                if len(mots) == 2:
                    montant_mise = int(mots[1])
                    nom_utilisateur = sender
                    response = jeu_de_des(nom_utilisateur, montant_mise)
                    irc.send(f"PRIVMSG {channel} :{response}\n".encode())
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !des [montant_mise]\n".encode())

            elif msg.startswith("!join"):
                if sender in administrateurs:
                    mots = msg.split()
                    if len(mots) == 2:
                        channel_to_join = mots[1]
                        irc.send(f"JOIN {channel_to_join}\n".encode())
                        irc.send(f"PRIVMSG {channel} :je rejoint {channel_to_join} le salon.\n".encode())
                        log_commande(f"[info]==> {sender} a fait rejoindre le bot au salon {channel_to_join}")
                    else:
                        irc.send(f"PRIVMSG {sender} :Commande invalide. Utilisation : !join [nom_du_salon]\n".encode())
                        log_commande(f"[ERREUR]==> Commande invalide !join par {sender}")
                else:
                    irc.send(f"PRIVMSG {sender} :Vous n'êtes pas autorisé à utiliser cette commande.\n".encode())
                    log_commande(f"[ERREUR]==> Tentative d'accès non autorisée à la commande !join par {sender}")

            elif msg.startswith("!part"):
                if sender in administrateurs:
                    mots = msg.split()
                    if len(mots) == 2:
                        channel_to_leave = mots[1]
                        irc.send(f"PART {channel_to_leave}\n".encode())
                        irc.send(f"PRIVMSG {channel} :ok je quitte le salon {channel_to_leave} ah bientôt.\n".encode())
                        log_commande(f"[info]==> {sender} a fait quitter le bot du salon {channel_to_leave}")
                    else:
                        irc.send(f"PRIVMSG {sender} :Commande invalide. Utilisation : !part [nom_du_salon]\n".encode())
                        log_commande(f"[ERREUR]==> Commande invalide !part par {sender}")
                else:
                    irc.send(f"PRIVMSG {sender} :Vous n'êtes pas autorisé à utiliser cette commande.\n".encode())
                    log_commande(f"[ERREUR]==> Tentative d'accès non autorisée à la commande !part par {sender}")

            elif msg.startswith("!quit"):
                if sender in administrateurs:
                    irc.send("QUIT Maintenance Technique bot casino beta-0.01 by Max\n".encode())
                    pid = open("bot.pid", "r").read().strip()
                    os.kill(int(pid), signal.SIGTERM)
                    log_commande(f"[ADMIN]==> Bot quitte sur commande par {sender}")
                else:
                    irc.send(f"PRIVMSG {sender} :Vous n'êtes pas autorisé à utiliser cette commande.\n".encode())
                    log_commande(f"[ERREUR]==> Tentative d'accès non autorisée à la commande !quit par {sender}")

# Commande !bank pour déposer des extrazinos dans le compte épargne
def bank_extrazinos(pseudo, montant):
    if montant <= 0:
        return f"{pseudo}, le montant à épargner doit être supérieur à zéro !"

    try:
        # Vérifier si l'utilisateur a un compte
        cursor.execute("SELECT solde_banque, solde_jeux FROM comptes WHERE nom_utilisateur = ?", (pseudo,))
        result = cursor.fetchone()

        if result:
            solde_banque, solde_jeux = result

            if montant > solde_jeux:
                # Si le montant est supérieur au solde disponible dans le jeu
                return f"{pseudo}, vous n'avez pas assez d'extrazinos pour épargner {montant} ! Vous avez {solde_jeux} extrazinos disponibles."

            # Mettre à jour les soldes
            nouveau_solde_banque = solde_banque + montant
            nouveau_solde_jeux = solde_jeux - montant

            # Mettre à jour les informations dans la base de données
            cursor.execute("UPDATE comptes SET solde_banque = ?, solde_jeux = ? WHERE nom_utilisateur = ?",
                           (nouveau_solde_banque, nouveau_solde_jeux, pseudo))
            conn.commit()

            # Message de confirmation
            return (f"[Crédité] {pseudo}, tu épargnes {montant} extrazinos ! "
                    f"Ton compte épargne atteint {nouveau_solde_banque} extrazinos et "
                    f"tu as actuellement {nouveau_solde_jeux} extrazinos sur le solde jeux.")
        else:
            return f"{pseudo}, vous n'avez pas encore de compte dans le casino."

    except mariadb.Error as e:
        return f"Erreur lors du dépôt d'extrazinos : {e}"

def traiter_commande(message, pseudo):
    if message.startswith("!bank"):
        # Extraire le montant de la commande
        try:
            montant = float(message.split()[1])  # Récupérer le montant après !bank
        except (IndexError, ValueError):
            return f"{pseudo}, veuillez entrer un montant valide après la commande !bank."

        # Appeler la fonction pour banquer le montant
        reponse = bank_extrazinos(pseudo, montant)
        return reponse

    # Autres commandes possibles...
    # elif message.startswith("!balance"):
    #     etc.

# Exécution de l'exemple
message = "!bank 500"
pseudo = "Elias"
reponse = traiter_commande(message, pseudo)
print(reponse)


# Exécution quand un utilisateur entre la commande !ticket
def traiter_commande_ticket(utilisateur, commande):
    if commande.startswith('!ticket'):
        try:
            # Extraction du montant
            _, montant_str = commande.split()
            montant = int(montant_str)
            
            # Validation du montant : Doit être 100 extrazinos pour un ticket
            if montant != 100:
                print(f"Le montant doit être exactement 100 extrazinos pour acheter un ticket.")
                return
            
            # Appeler la fonction pour acheter un ticket
            acheter_ticket(utilisateur, montant)
            
        except ValueError:
            print(f"Commande invalide. Usage: !ticket <montant>")
        except Exception as e:
            print(f"Erreur lors du traitement de la commande !ticket : {str(e)}")


# Function to check if a user has an account
def compte_existe(nom_utilisateur):
    try:
        cursor.execute("SELECT COUNT(*) FROM comptes WHERE nom_utilisateur = ?", (nom_utilisateur,))
        return cursor.fetchone()[0] > 0
    except mariadb.Error as e:
        print(f"Error checking account: {e}")
        return False

# Fermeture de la connexion
irc.close()
