# casinoIRC-python beta
jeux de casino en python pour irc

dans cette version je suis reparti de zéro pour modifier la connexion irc du bot Le bot ce connect maintenant en socket ;)



# commandes disponibles (administrateur)

!register [nom_utilisateur] : Créer un compte.

!solde [nom_utilisateur] : Voir le solde du compte.

!convertir [montant] converti vos credit de jeux et les met en banque.

!transfert [montant] : transfert des crédits de votre compte en banque vers votre compte de jeux.

!roulette [nombre] : jouer au jeux de la roulette.\n".encode())

!casino [jeu] [montant] : joue au jeu du casino (ex: !casino 50).

!slots [montant] : joue au machine a sous.

!des [montant] : joue au jeux de dès.

!quit : Déconnecter le bot.

!join [#channel] : fait joindre le bot sur un channel.

!part [#channel] : fait Partire le bot d'un channel.

!supprimer [nom_utilisateur] : Supprimer un compte.

!ajouterargent [nom_utilisateur] [montant] : credite de l'agennt sur le compte d'un joueur

!restart: pour restart le bot

!addadmin: ajoute un admin au bot

!deladmin: supprime un admin au bot



### Commandes disponibles pour les Joueur :

!register [nom_utilisateur] : Créer un compte.

!solde [nom_utilisateur] : Voir le solde du compte.

!convertir [montant] converti vos credit de jeux et les met en banque.

!casino [jeu] [montant] : joue au jeu du casino (ex: !casino 50).

!roulette [nombre] : jouer au jeux de la roulette.

!slots [montant] : joue au machine a sous.

!des [montant] : joue au jeux de dès.

!demande (#salon): demande au bot de fair rejoindre votre salon

!listadmin: dit la list des admin dispo

!version: regarde la version actuel du bot



## Versions

**version beta :** 1.1

ajout d'un salon #logs ou son stocker toutes les commande fait par les joueur 

ajout d'un timer de 30sec entre chaque jeux pour eviter le spamm salon 

ajout d'une commande admin pour ajouter de l'argent a un joueur ( !ajouterargent [nom_utilisateur] [montant] )

version 1.2

modification 30/09/2024:
                                                        
ajout d'une page html des stats joueur
         
ajout d'une anonce sur un salon pour inviter les users a jouer sur #casino  

## Auteurs
* **Maxime** irc.extra-cool.fr https://extra-cool.fr/ )
