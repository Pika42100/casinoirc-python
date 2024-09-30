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
#  casino bot en python                                                                    #
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

# Définir la version du bot
version_bot = "casino BOT- PAR Maxime Version 1.2" # pour le respect de mon trvaille merci de ne pas modifier cette ligne 

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
db_user = "casino"
db_password = "votre-mot-de-pass"
db_name = "casino"

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

# Fonction pour créer un compte utilisateur avec 1000 crédits à l'inscription
def creer_compte(nom_utilisateur):
    try:
        cursor.execute("INSERT INTO comptes (nom_utilisateur, solde_banque, solde_jeux, dernier_credit) VALUES (?, 1000, 0, ?)", (nom_utilisateur, datetime.now().date()))
        conn.commit()
        return True
    except mariadb.Error as e:
        print(f"Erreur lors de la création du compte: {e}")
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
        <html>
        <head>
            <meta charset="UTF-8">
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
            </style>
        </head>
        <body>
            <h1>Statistiques des Joueurs</h1>
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
                    <td>{solde_banque} crédits</td>
                    <td>{solde_jeux} crédits</td>
                </tr>
            """

        # Section des commandes
        html_content += """
            </table>
            <div class="commands">
                <h2>Commandes disponibles</h2>
                <p><strong>!register [nom_utilisateur]</strong> : Créer un compte.</p>
                <p><strong>!solde [nom_utilisateur]</strong> : Voir le solde du compte.</p>
                <p><strong>!convertir [montant]</strong> : Convertir vos crédits de jeux en banque.</p>
                <p><strong>!casino [montant]</strong> : Jouer au jeu du casino (ex: !casino 50).</p>
                <p><strong>!roulette [nombre]</strong> : Jouer au jeu de la roulette.</p>
                <p><strong>!slots [montant]</strong> : Jouer aux machines à sous.</p>
                <p><strong>!des [montant]</strong> : Jouer au jeu de dés.</p>
                <p><strong>!transfert [montant] : transfert des crédits de votre compte en banque vers votre compte de jeux.</p>
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
        return f"{Fore.GREEN}Montant de {montant} crédits ajouté avec succès au compte de {nom_utilisateur}.{Fore.RESET}"
    else:
        return f"{Fore.RED}Erreur lors de l'ajout de crédits au compte de {nom_utilisateur}.{Fore.RESET}"

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
                            return f"{Fore.BLUE}Vous avez déposé {montant} crédits de jeux dans votre compte en banque. Nouveau solde en banque : {nouveau_solde_banque}, Nouveau solde en jeux : {nouveau_solde_jeux}"
                        else:
                            return f"{Fore.RED}Une erreur est survenue lors du dépôt."
                    else:
                        return f"{Fore.RED}Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."
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
                            return f"{Fore.BLUE}Vous avez converti {montant} crédits de jeux en {montant} crédits en banque. Nouveau solde en banque : {nouveau_solde_banque}, Nouveau solde en jeux : {nouveau_solde_jeux}"
                        else:
                            return f"{Fore.RED}Une erreur est survenue lors de la conversion."
                    else:
                        return f"{Fore.RED}Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."
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
            return f"{Fore.RED}Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."
    elif commande.startswith("!solde_jeux"):
        solde_jeux = get_solde_jeux(nom_utilisateur)
        if solde_jeux is not None:
            return f"{Fore.BLUE}Solde en jeux : {solde_jeux}"
        else:
            return f"{Fore.RED}Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."
    if commande.startswith("!solde_banque"):
        solde_banque = get_solde_banque(nom_utilisateur)
        if solde_banque is not None:
            return f"Solde en banque : {solde_banque}"
        else:
            return "Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."
    mots = commande.split()
    if mots[0] == "!deposer":
        if len(mots) == 2:
            montant = int(mots[1])
            if montant > 0:
                solde_banque = get_solde_banque(nom_utilisateur)
                if solde_banque is not None:
                    nouveau_solde_banque = solde_banque + montant
                    if mettre_a_jour_solde_banque(nom_utilisateur, nouveau_solde_banque):
                        return f"Vous avez déposé {montant} crédits dans votre compte en banque. Nouveau solde en banque : {nouveau_solde_banque}"
                    else:
                        return "Une erreur est survenue lors du dépôt."
                else:
                    return "Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."
            else:
                return "Le montant doit être supérieur à zéro."
        else:
            return "Commande invalide. Utilisation : !deposer [montant]"
    elif commande.startswith("!solde_banque"):
        solde_banque = get_solde_banque(nom_utilisateur)
        if solde_banque is not None:
            return f"Solde en banque : {solde_banque}"
        else:
            return "Utilisateur non trouvé veuiller dabors vous enregistre avec la commande !register."

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
        return f"{Fore.BLUE}Vous avez transféré {montant} crédits de votre compte en banque vers votre compte de jeux. Nouveau solde en banque : {nouveau_solde_banque}, Nouveau solde en jeux : {nouveau_solde_jeux}"
    else:
        return f"{Fore.RED}Une erreur est survenue lors du transfert de crédits."

def gestion_commande_casino(nom_utilisateur, commande):
    match = re.match(r"!casino (\d+)", commande)
    if match:
        montant = int(match.group(1))
        solde = get_solde(nom_utilisateur)
        solde_jeux = get_solde_jeux(nom_utilisateur)  # Récupérer le solde de jeux de l'utilisateur
        if solde_jeux:
            if solde:
                solde_banque, solde_jeux = solde
                if solde_banque >= montant:
                    if gagner_ou_perdre():
                        solde_banque -= montant
                        solde_jeux += montant * 2  
                        message = f"{Fore.BLUE}Vous avez gagné {montant} ! Votre nouveau solde en jeux est de {solde_jeux}.{Fore.RESET}"
                    else:
                        solde_banque -= montant
                        solde_jeux -= montant  
                        message = f"{Fore.RED}Vous avez perdu {montant} ! Votre solde en banque est de {solde_banque}. Votre solde en jeux est de {solde_jeux}.{Color.END}"
                    if mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux):
                        return message
                    else:
                        return f"{Color.PURPLE}Solde insuffisant dans votre banque.{Color.END}"
                else:
                    return f"{Color.PURPLE}Solde insuffisant dans votre banque.{Color.END}"

            else:
                return f"{Fore.RED}Vous n'avez pas suffisamment de crédits de jeux pour jouer veuillez faire un transfert [!transfert montant].{Color.END}"
        else:
            return f"{Fore.RED}Commande invalide. Utilisation : !casino [montant]{Fore.RESET}"

def gestion_commande_stats(nom_utilisateur, commande):
    print(f"Commande reçue: {commande}")  # Pour le débogage

    if commande == "!statscas":
        print(f"{nom_utilisateur} a demandé à voir les statistiques.")
        return f"Voici les statistiques des joueurs: [Cliquez ici pour voir les stats](http://51.38.113.103/stats_joueurs.html)"
    
    # Autres commandes à gérer
    # ...

# Testez la fonction manuellement
response = gestion_commande_casino("joueur_test", "!statscas")
print(response)  # Cela devrait afficher le message avec le lien


# Testez la fonction manuellement
response = gestion_commande_casino("joueur_test", "!statscas")
print(response)  # Cela devrait afficher le message avec le lien

def jeu_de_des(nom_utilisateur, montant_mise):
    if montant_mise <= 0:
        return f"{Fore.RED}Le montant de la mise doit être supérieur à zéro.{Fore.RESET}"
    
    solde_banque = get_solde_banque(nom_utilisateur)
    if solde_banque is None:
        return f"{Fore.RED}Utilisateur non trouvé. Veuillez d'abord vous enregistrer avec la commande !register.{Fore.RESET}"
    
    if solde_banque < montant_mise:
        return f"{Fore.RED}Solde insuffisant.{Fore.RESET}"
    
    # Lancement du dé
    resultat = random.randint(1, 6)
    if resultat == 6:
        gain = montant_mise * 2  # Gain: double de la mise si le résultat est 6
        solde_banque += gain
        message = f"{Fore.GREEN}Vous avez lancé un 6 et gagné {gain} crédits!{Fore.RESET}"
    else:
        solde_banque -= montant_mise
        message = f"{Fore.RED}Vous avez lancé un {resultat}. Vous perdez votre mise de {montant_mise} crédits.{Fore.RESET}"
    
    # Mise à jour du solde en banque après le jeu
    if mettre_a_jour_solde_banque(nom_utilisateur, solde_banque):
        message += f" Nouveau solde en banque : {solde_banque}"
    else:
        message = f"{Fore.RED}Une erreur est survenue lors de la mise à jour du solde.{Fore.RESET}"
    
    return message



def gestion_commande_roulette(nom_utilisateur, commande):
    mots = commande.split()
    if mots[0] == "!roulette":
        if len(mots) == 2:
            montant = int(mots[1])
            solde = get_solde(nom_utilisateur)
            if solde:
                solde_banque, solde_jeux = solde
                if solde_banque >= montant:
                    resultat_jeu = jeu_roulette()
                    numero_gagnant, couleur, parite = resultat_jeu
                    if gagner_ou_perdre():
                        solde_jeux += montant * 2
                        message = f"La bille est tombée sur le {numero_gagnant} ({couleur}, {parite}). Vous avez gagné {montant} crédits !"
                    else:
                        solde_jeux -= montant
                        message = f"La bille est tombée sur le {numero_gagnant} ({couleur}, {parite}). Vous avez perdu {montant} crédits !"

                    if mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux):
                        message += " Veuillez attendre 30 secondes avant de jouer à nouveau."
                        irc.send(f"PRIVMSG {channel} :{message}\n".encode())
                        time.sleep(30)
                    else:
                        message = "Une erreur est survenue lors de la mise à jour du solde."
                else:
                    message = "Solde insuffisant dans votre banque."
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
    solde_banque = get_solde_banque(nom_utilisateur)
    solde_jeux = get_solde_jeux(nom_utilisateur)

    if solde_banque is None or solde_jeux is None:
        return "Solde insuffisant dans votre banque pour effectuer cette mise."

    if solde_banque >= montant_mise:
        solde_banque -= montant_mise
        symboles_tires = [random.choice(list(symboles.keys())) for _ in range(3)]
        resultat = [symboles[symbole] for symbole in symboles_tires]
        symboles_alignes = len(set(symboles_tires))

        if jackpot == 1 and symboles_alignes == 1:
            jackpot_amount = random.randint(1000, 10000)
            solde_jeux += jackpot_amount
            message = f"Jackpot !! Vous avez gagné {jackpot_amount} crédits de jeux ! Résultat: {' - '.join(symboles_tires)}."
        elif symboles_alignes == 2:
            gain = montant_mise * 2
            solde_jeux += gain
            message = f"Bravo ! Vous avez gagné {gain} crédits de jeux ! Résultat: {' - '.join(symboles_tires)}."
        else:
            message = f"Dommage ! Vous n'avez rien gagné cette fois-ci. Résultat: {' - '.join(symboles_tires)}."

        # Mise à jour du solde et préparation du message final
        if mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux):
            message += " Veuillez attendre 30 secondes avant de jouer à nouveau."
        else:
            message = "Une erreur est survenue lors de la mise à jour du solde."
    else:
        message = "Solde insuffisant dans votre banque pour effectuer cette mise."

    # Envoyer le message et appliquer le délai après toutes les interactions
    irc.send(f"PRIVMSG {channel} :{message}\n".encode())
    time.sleep(30)  # Attendre 30 secondes avant que le joueur puisse rejouer
    return message

articles = {
    "Livre": 50,
    "Montre": 100,
    "Console de jeu": 200,
    "Vélo": 300,
    "Smartphone": 500
}

def jeu_juste_prix(nom_utilisateur, montant_mise):
    solde_banque = get_solde_banque(nom_utilisateur)
    if solde_banque is not None and solde_banque >= montant_mise:
        solde_banque -= montant_mise
        prix_a_deviner = random.randint(1, 100)
        numero_propose = random.randint(1, 100)
        if numero_propose == prix_a_deviner:
            gain = montant_mise * 2
            solde_jeux = get_solde_jeux(nom_utilisateur)
            solde_jeux += gain
            message = f"Bravo ! Vous avez deviné le juste prix ({prix_a_deviner}) ! Vous avez gagné {gain} crédits de jeux."
        else:
            message = f"Dommage ! Le juste prix était {prix_a_deviner}. Vous avez perdu votre mise."

        if mettre_a_jour_solde(nom_utilisateur, solde_banque, solde_jeux):
            message += " Veuillez attendre 30 secondes avant de jouer à nouveau."
            irc.send(f"PRIVMSG {channel} :{message}\n".encode())
            time.sleep(30)
        else:
            message = "Une erreur est survenue lors de la mise à jour du solde."
    else:
        message = "Solde insuffisant dans votre banque pour effectuer cette mise."
    return message


def attribuer_article(montant_mise):
    for article, valeur in articles.items():
        if montant_mise * 2 >= valeur:  
            return article
    return "Aucun article"

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
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !convertir [montant] converti vos credit de jeux et les met en banque.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !transfert [montant] : transfert des crédits de votre compte en banque vers votre compte de jeux.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !roulette [nombre] : jouer au jeux de la roulette.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !casino [montant] : joue au jeu du casino (ex: !casino 50).\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !slots [montant] : joue au machine a sous.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !des [montant] : joue au jeux de dès.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !quit : Déconnecter le bot.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !join [#channel] : fait joindre le bot sur un channel.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !part [#channel] : fait Partire le bot d'un channel.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !supprime [nom_utilisateur] : Supprimer un compte.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !ajouterargent [nom_utilisateur] [montant] : credite de l'agennt sur le compte d'un joueur.\n".encode())
    else:
        irc.send(f"PRIVMSG {nom_utilisateur} :\x0304Commandes disponibles :\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !register [nom_utilisateur] : Créer un compte.(ex: register Maxime)\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !casino [montant] : joue au jeu du casino (ex: !casino 50).\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !solde [nom_utilisateur] : Voir le solde du compte.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !convertir [montant] converti vos credit de jeux et les met en banque.\n".encode())
        irc.send(f"PRIVMSG {nom_utilisateur} : \x0310- !transfert [montant] : transfert des crédits de votre compte en banque vers votre compte de jeux.\n".encode())
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
nickname = "CasinoBot"
password = "votre-mot-de-pass"
nickserv_password = "votre-mot-de-pass"
ircop_password = "votre-mot-de-pass"  # Ajoutez votre mot de passe IRCop ici
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

# Création d'un contexte SSL
context = ssl.create_default_context()

# Envelopper la socket dans une couche SSL/TLS
irc = context.wrap_socket(sock, server_hostname=server)

# Envoyer les commandes IRC
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

# Boucle principale pour traiter les messages
while True:
    message = irc.recv(2048).decode("UTF-8")
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
            user = join_match.group(1)
            channel = join_match.group(2)
            log_message = f"[info]==>{user} a rejoint le salon {channel}"
            print(log_message)  # Afficher pour le débogage
            irc.send(f"PRIVMSG {logs_channel} :{log_message}\n".encode())
            log_commande(log_message)

    # Détection des messages de type PART
    if "PART" in message:
        part_match = re.match(r"^:(.*?)!.*PART\s+(#\S+)", message)
        if part_match:
            user = part_match.group(1)
            channel = part_match.group(2)
            log_message = f"[info]==>{user} a quitté le salon {channel}"
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
            elif msg.startswith("!restart") and sender in administrateurs:  # Vérification des privilèges
                irc.send(f"PRIVMSG {channel} :Le bot va redémarrer...\n".encode())
                log_commande(f"[info]==> Commande de redémarrage reçue de {sender}")
                restart_bot()
            elif msg.startswith("!restart"):
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
                if len(mots) >= 2:
                    nom_utilisateur = mots[1]
                    if creer_compte(nom_utilisateur):
                        irc.send(f"PRIVMSG {channel} :Compte {nom_utilisateur} créé avec succès.\n".encode())
                        log_commande(f"[info]==> Compte {nom_utilisateur} créé avec succès par {sender}")
                    else:
                        irc.send(f"PRIVMSG {channel} :Erreur lors de la création du compte.\n".encode())
                        log_commande(f"[ERREUR]==> Erreur lors de la création du compte pour {nom_utilisateur} par {sender}")
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !register [nom_utilisateur]\n".encode())
                    log_commande(f"[ERREUR]==> Tentative de création de compte avec commande invalide par {sender}")

            elif msg.startswith("!solde"):
                mots = msg.split()
                if len(mots) >= 2:
                    nom_utilisateur = mots[1]
                    solde = get_solde(nom_utilisateur)
                    if solde:
                        solde_banque, solde_jeux = solde
                        irc.send(f"PRIVMSG {channel} :Solde en banque : {solde_banque}, Solde en jeux : {solde_jeux}\n".encode())
                        log_commande(f"[info]==> Solde vérifié pour {nom_utilisateur} par {sender}")
                    else:
                        irc.send(f"PRIVMSG {channel} :Utilisateur non trouvé veuiller d'abord vous enregistrer avec la commande !register.\n".encode())
                        log_commande(f"[ERREUR]==> Utilisateur non trouvé pour vérification de solde par {sender}")
                else:
                    irc.send(f"PRIVMSG {channel} :Commande invalide. Utilisation : !solde [nom_utilisateur]\n".encode())
                    log_commande(f"[ERREUR]==> Commande invalide pour solde effectuée par {sender}")

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

# Fermeture de la connexion
irc.close()
