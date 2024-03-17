import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
import pymysql
import random
import datetime
import datetime

class CasinoBot(irc.bot.SingleServerIRCBot):
    def __init__(self):
        # Connexion à la base de données MariaDB
        self.db = pymysql.connect(host='localhost',
                                  user='casino',
                                  password='mot-de-pass',
                                  database='casino',
                                  cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.db.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS accounts (nick VARCHAR(255), balance INT, last_credit_request DATE)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS transactions (id INT AUTO_INCREMENT PRIMARY KEY, nick VARCHAR(255), amount INT, type VARCHAR(10), timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        self.db.commit()
        
        # Configuration du bot IRC
        server = "irc.extra-cool.fr"
        port = 6667
        nickname = "CasinoBot"
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        
        self.quiz_questions = {
            "Quelle est la capitale de la France ?": "Paris",
            "Combien de continents y a-t-il sur Terre ?": "7",
            "Qui a peint la Joconde ?": "Leonardo da Vinci"
        }
        self.wrong_answers = {}
        self.correct_answer = None
        
        # Articles pour le jeu du Juste Prix
        self.articles = {
            "iPhone": (100, 1000),
            "TV": (200, 1500),
            "Console de jeu": (150, 1200),
            "Ordinateur portable": (300, 2000),
            "Montre intelligente": (80, 800)
        }
        self.juste_prix_running = False
        self.duck_hunt_running = False
        self.local_jackpot = 0  # Initialiser le jackpot local à zéro
        self.global_jackpot = 0  # Initialiser le jackpot global à zéro

        
    def check_account(self, connection, target, nickname):
        self.cursor.execute("SELECT * FROM accounts WHERE nick = %s", (nickname,))
        account = self.cursor.fetchone()
        if account is None:
            connection.privmsg(target, f"Vous devez d'abord vous inscrire avec !register, {nickname}!")
            return False
        return True

    def play_quiz(self, connection, target, nickname):
        if not self.check_account(connection, target, nickname):
            return
        question = random.choice(list(self.quiz_questions.keys()))
        self.correct_answer = self.quiz_questions[question]
        self.send_message(connection, target, f"{nickname}, {question}")
        
    def on_welcome(self, connection, event):
        connection.join("#extra-cool")

        self.drinks = {
            "coca": 5,
            "bière": 10,
            "vin": 15,
            "cocktail": 20
        }

    # Fonction pour afficher la liste des boissons disponibles au bar
    def show_drinks(self, connection, target):
        if not self.check_account(connection, target, nickname):
            return
        drinks_list = ", ".join([f"{drink.capitalize()} ({price} crédits)" for drink, price in self.drinks.items()])
        connection.privmsg(target, f"Boissons disponibles au bar : {drinks_list}")

    # Fonction pour permettre aux utilisateurs d'acheter des boissons
    def buy_drink(self, connection, target, nickname, drink):
        if not self.check_account(connection, target, nickname):
            return
        if drink not in self.drinks:
            connection.privmsg(target, f"{drink.capitalize()} n'est pas disponible au bar.")
            return

        price = self.drinks[drink]
        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (nickname,))
        account = self.cursor.fetchone()
        if account is None:
            connection.privmsg(target, f"Vous devez d'abord vous inscrire avec !register, {nickname}!")
            return

        if account['balance'] < price:
            connection.privmsg(target, f"Vous n'avez pas assez de crédits pour acheter {drink.capitalize()}.")
            return

        self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (price, nickname))
        self.record_transaction(nickname, price, "buy_drink")
        self.db.commit()
        connection.privmsg(target, f"{nickname}, vous avez acheté {drink.capitalize()} pour {price} crédits.")

    def on_pubmsg(self, connection, event):
        message = event.arguments[0]
        if message.startswith("!register"):
            nickname = event.source.nick
            self.register_user(connection, event.target, nickname)
        nickname = event.source.nick  # Obtenir le pseudo de l'utilisateur
        
        nickname = event.source.nick
        if message.startswith("!delete_account"):
            self.delete_account(connection, event.target, nickname)
            
        message = event.arguments[0]
        nickname = event.source.nick
        if message.startswith("!duck_hunt") and not self.duck_hunt_running:
            self.start_duck_hunt(connection, event.target, nickname)
        elif message.startswith("!shoot") and self.duck_hunt_running:
            self.shoot_duck(connection, event.target, nickname, message)
        
         # Gérer les autres commandes existantes...
        message = event.arguments[0]
        if message.startswith("!bar"):
            self.show_drinks(connection, event.target)
        elif message.startswith("!buy"):
            args = message.split()
            if len(args) != 2:
                connection.privmsg(event.target, "Usage: !buy <boisson>")
            else:
                nickname = event.source.nick
                drink = args[1].lower()
                self.buy_drink(connection, event.target, nickname, drink)
        elif message.startswith("!gift"):
            args = message.split()
            if len(args) != 3:
                connection.privmsg(event.target, "Usage: !gift <destinataire> <boisson>")
            else:
                sender = event.source.nick
                recipient = args[1]
                drink = args[2].lower()
                self.gift_drink(connection, event.target, sender, recipient, drink)
        elif message.startswith("!casino"):
            nickname = event.source.nick
            self.play_casino(connection, event.target, nickname, message)
        elif message.startswith("!balance"):
            nickname = event.source.nick
            self.check_balance(connection, event.target, nickname)
        elif message.startswith("!aide"):
            self.send_help(connection, event.target, event.source.nick)
        elif message.startswith("!quit"):
            self.quit_bot(connection, event.source.nick)
        elif message.startswith("!top10"):
            self.show_top_players(connection, event.target)
        elif message.startswith("!transfer"):
            args = message.split()
            if len(args) != 3:
                connection.privmsg(event.target, "Usage: !transfer <destinataire> <montant>")
            else:
                sender = event.source.nick
                recipient = args[1]
                amount = args[2]
                self.transfer_credits(connection, event.target, sender, recipient, amount)
        elif message.startswith("!profile"):
            nickname = event.source.nick
            self.show_profile(connection, event.target, nickname)
        elif message.startswith("!flipcoin"):
            nickname = event.source.nick
            self.flip_coin(connection, event.target, nickname)
        elif message.startswith("!roulette"):
            nickname = event.source.nick
            self.play_roulette(connection, event.target, nickname, message)
        elif message.startswith("!dice"):
            nickname = event.source.nick
            self.play_dice(connection, event.target, nickname, message)
        elif message.startswith("!slots"):
            nickname = event.source.nick
            self.play_slots(connection, event.target, nickname, message)
        elif message.startswith("!credit"):
            nickname = event.source.nick
            self.request_credit(connection, event.target, nickname)
            message = event.arguments[0]
            nickname = event.source.nick
        if message.startswith("!juste_prix") and not self.juste_prix_running:
            self.start_juste_prix(connection, event.target, nickname)  # Passer le paramètre nickname
        elif message.startswith("!bid") and self.juste_prix_running:
            self.place_bid(connection, event.target, event.source.nick, message)
        elif message.startswith("!devine"):
            nickname = event.source.nick
            self.play_guess_the_number(connection, event.target, nickname, message)
            message = event.arguments[0]
            
            message = event.arguments[0]
        nickname = event.source.nick  # Get user nickname from the event
        if message.startswith("!quiz"):
            self.play_quiz(connection, event.target, nickname)
        elif message.startswith("!rep"):
            if self.correct_answer is None:
                self.send_message(connection, event.target, "Aucune question n'est en cours.")
                return
            answer = message.split("!rep ", 1)[1]
            if answer.lower() == self.correct_answer.lower():
                self.send_message(connection, event.target, f"Bonne réponse, {nickname} ! Vous gagnez 10 crédits.")
                # Add 10 credits to the player
            else:
                if nickname in self.wrong_answers:
                    self.wrong_answers[nickname] += 1
                else:
                    self.wrong_answers[nickname] = 1
                if self.wrong_answers[nickname] >= 3:
                    self.send_message(connection, event.target, f"{nickname}, vous avez répondu incorrectement 3 fois. Vous perdez 10 crédits.")
                    # Remove 10 credits from the player
                else:
                    self.send_message(connection, event.target, f"Dommage, {nickname} ! Essayez à nouveau.")

    def send_message(self, connection, target, message):
        connection.privmsg(target, message)
            
    def gift_drink(self, connection, target, sender, recipient, drink):
        if not self.check_account(connection, target, nickname):
            return
        if drink not in self.drinks:
            connection.privmsg(target, f"{drink.capitalize()} n'est pas disponible au bar.")
            return

        price = self.drinks[drink]
        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (sender,))
        sender_account = self.cursor.fetchone()
        if sender_account is None:
            connection.privmsg(target, f"Vous devez d'abord vous inscrire avec !register, {sender}!")
            return

        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (recipient,))
        recipient_account = self.cursor.fetchone()
        if recipient_account is None:
            connection.privmsg(target, f"Le destinataire {recipient} n'existe pas.")
            return

        if sender_account['balance'] < price:
            connection.privmsg(target, f"Vous n'avez pas assez de crédits pour acheter {drink.capitalize()}.")
            return

        self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (price, sender))
        self.cursor.execute("UPDATE accounts SET balance = balance + %s WHERE nick = %s", (price, recipient))
        self.record_transaction(sender, price, f"achat_boisson_pour_{recipient}")
        self.record_transaction(recipient, price, f"reception_boisson_de_{sender}")
        self.db.commit()
        connection.privmsg(target, f"{sender} a acheté {drink.capitalize()} pour {recipient}.")

    def register_user(self, connection, target, nickname):
        self.cursor.execute("SELECT * FROM accounts WHERE nick = %s", (nickname,))
        if self.cursor.fetchone() is None:
            self.cursor.execute("INSERT INTO accounts (nick, balance, last_credit_request) VALUES (%s, %s, %s)", (nickname, 100, datetime.date.today()))
            self.db.commit()
            connection.privmsg(target, f"Vous avez été enregistré avec succès, {nickname}!")
        else:
            connection.privmsg(target, f"Vous êtes déjà enregistré, {nickname}!")


    def play_casino(self, connection, target, nickname, message):
        if not self.check_account(connection, target, nickname):
            return
        args = message.split()
        if len(args) != 2:
            connection.privmsg(target, "Usage: !casino <mise>")
            return
        try:
            bet = int(args[1])
        except ValueError:
            connection.privmsg(target, "La mise doit être un nombre entier.")
            return
        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (nickname,))
        account = self.cursor.fetchone()
        if account is None:
            connection.privmsg(target, f"Vous devez d'abord vous inscrire avec !register, {nickname}!")
        elif account['balance'] < bet:
            connection.privmsg(target, "Vous n'avez pas assez de crédits.")
        else:
            outcome = random.choice(["win", "lose"])
            if outcome == "win":
                local_jackpot = self.generate_local_jackpot()  # Générer le jackpot local
                global_jackpot = self.generate_global_jackpot()  # Générer le jackpot global
                bet += local_jackpot + global_jackpot  # Ajouter les jackpots aux gains du joueur
                self.local_jackpot += local_jackpot  # Mettre à jour le jackpot local
                self.global_jackpot += global_jackpot  # Mettre à jour le jackpot global
                self.cursor.execute("UPDATE accounts SET balance = balance + %s WHERE nick = %s", (bet, nickname))
                self.record_transaction(nickname, bet, "win")
                connection.privmsg(target, f"Félicitations! Vous avez gagné {bet} crédits. Jackpot local: {local_jackpot}. Jackpot global: {global_jackpot}")
            else:
                self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (bet, nickname))
                self.record_transaction(nickname, bet, "lose")
                connection.privmsg(target, f"Désolé! Vous avez perdu {bet} crédits.")
            self.db.commit()

    def generate_local_jackpot(self):
        # Implémentation de la logique de génération du jackpot local (identique à celle précédemment fournie)
        pass
    def generate_local_jackpot(self):
    # Implémentation de la logique de génération du jackpot local
        return random.randint(1, 100)

    def generate_global_jackpot(self):
        # Implémentation de la logique de génération du jackpot global (par exemple, un montant aléatoire entre 1 et 100)
        return random.randint(1, 100)

    def get_global_jackpot_amount(self):
        # Renvoyer le montant actuel du jackpot global
        return self.global_jackpot

    def handle_global_jackpot_command(self, connection, target):
        # Gérer la commande pour consulter le montant actuel du jackpot global
        jackpot_amount = self.get_global_jackpot_amount()
        connection.privmsg(target, f"Le montant actuel du jackpot global est de {jackpot_amount} crédits.")

    def handle_command(self, connection, target, command):
        # Méthode pour gérer les différentes commandes
        if command == "!jackpot":
            self.handle_global_jackpot_command(connection, target)
        # Ajoutez d'autres commandes ici si nécessaire

    def main_loop(self):
        # Boucle principale pour gérer les messages entrants
        while True:
            # Code pour recevoir et traiter les messages
            pass
            
    def generate_jackpot(self):
        # Vous pouvez personnaliser cette fonction pour ajuster la logique de génération du jackpot
        # Par exemple, vous pourriez vouloir qu'il y ait une probabilité plus faible d'obtenir un jackpot plus élevé
        # Voici un exemple basé sur une distribution logarithmique où les montants plus élevés sont moins probables

        # Déterminez la probabilité de différents montants de jackpot
        probabilities = [0.1, 0.2, 0.3, 0.2, 0.1, 0.05, 0.03, 0.02]

        # Déterminez les plages de montants de jackpot correspondant à ces probabilités
        amounts = [10, 50, 100, 500, 1000, 5000, 10000, 50000]

        # Utilisez les probabilités pour choisir un montant de jackpot
        jackpot_amount = random.choices(amounts, probabilities)[0]
        
        return jackpot_amount


    def check_balance(self, connection, target, nickname):
        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (nickname,))
        account = self.cursor.fetchone()
        if account is not None:
            connection.privmsg(target, f"Votre solde est de {account['balance']} crédits.")
        else:
            connection.privmsg(target, f"Vous devez d'abord vous inscrire avec !register, {nickname}!")

    def send_help(self, connection, target, nickname):
        connection.privmsg(nickname, "Commandes disponibles:")
        connection.privmsg(nickname, "!register - S'inscrire au casino")
        connection.privmsg(nickname, "!casino <mise> - Jouer au casino avec une mise donnée")
        connection.privmsg(nickname, "!balance - Vérifier votre solde")
        connection.privmsg(nickname, "!transfer <destinataire> <montant> - Transférer des crédits à un autre joueur")
        connection.privmsg(nickname, "!profile - Voir votre profil")
        connection.privmsg(nickname, "!depot <montant> - Déposer de l'argent dans votre compte en banque")
        connection.privmsg(nickname, "!credit - Demander un crédit bancaire 1 par jour")
        connection.privmsg(nickname, "!delete_account - Supprimer votre compte(1fois par semaine)")
        connection.privmsg(nickname, "!top10 - Afficher les 10 meilleurs joueurs")
        connection.privmsg(nickname, "!aide - Afficher cet message d'aide")
        connection.privmsg(nickname, "!quit - Quitter le casino")
        connection.privmsg(nickname, "!flipcoin - Lancer une pièce")
        connection.privmsg(nickname, "!roulette <mise> - Jouer à la roulette")
        connection.privmsg(nickname, "!dice <mise> - Jouer au jeu de dés")
        connection.privmsg(nickname, "!slots <mise> - Jouer à la machine à sous")
        connection.privmsg(nickname, "!bar - afiche les boisson disponible/!buy <montant> achète la boisson)")
        connection.privmsg(nickname, "!quiz - joue au quiz")
        connection.privmsg(nickname, "!juste_prix - lance le jeux du juste prix")
        connection.privmsg(nickname, "!duck_hunt - jeux du chasseur de canard")

    def quit_bot(self, connection, nickname):
        connection.privmsg(nickname, "À bientôt!")
        self.disconnect()

    def show_top_players(self, connection, target):
        self.cursor.execute("SELECT nick, balance FROM accounts ORDER BY balance DESC LIMIT 10")
        top_players = self.cursor.fetchall()
        if top_players:
            connection.privmsg(target, "Top 10 des meilleurs joueurs:")
            for idx, player in enumerate(top_players, start=1):
                connection.privmsg(target, f"{idx}. {player['nick']} - {player['balance']} crédits")
        else:
            connection.privmsg(target, "Aucun joueur trouvé.")

    def transfer_credits(self, connection, target, sender, recipient, amount):
        if not self.check_account(connection, target, nickname):
            return
        try:
            amount = int(amount)
        except ValueError:
            connection.privmsg(target, "Le montant doit être un nombre entier.")
            return

        if amount <= 0:
            connection.privmsg(target, "Le montant doit être supérieur à zéro.")
            return

        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (sender,))
        sender_balance = self.cursor.fetchone()
        if sender_balance is None:
            connection.privmsg(target, f"Le joueur {sender} n'existe pas.")
            return

        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (recipient,))
        recipient_balance = self.cursor.fetchone()
        if recipient_balance is None:
            connection.privmsg(target, f"Le joueur {recipient} n'existe pas.")
            return

        if sender_balance['balance'] < amount:
            connection.privmsg(target, f"Vous n'avez pas assez de crédits pour transférer {amount} crédits.")
            return

        self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (amount, sender))
        self.cursor.execute("UPDATE accounts SET balance = balance + %s WHERE nick = %s", (amount, recipient))
        self.record_transaction(sender, amount, "transfer")
        self.record_transaction(recipient, amount, "receive")
        self.db.commit()
        connection.privmsg(target, f"{sender} a transféré {amount} crédits à {recipient}.")

    def show_profile(self, connection, target, nickname):
        if not self.check_account(connection, target, nickname):
            return
        self.cursor.execute("SELECT * FROM accounts WHERE nick = %s", (nickname,))
        account = self.cursor.fetchone()
        if account is not None:
            connection.privmsg(target, f"Profil de {nickname}: Solde - {account['balance']} crédits")
            self.cursor.execute("SELECT * FROM transactions WHERE nick = %s ORDER BY timestamp DESC LIMIT 5", (nickname,))
            transactions = self.cursor.fetchall()
            if transactions:
                connection.privmsg(target, "Historique des transactions:")
                for transaction in transactions:
                    if transaction['type'] == 'win':
                        connection.privmsg(target, f"{transaction['timestamp']}: Gain de {transaction['amount']} crédits")
                    elif transaction['type'] == 'lose':
                        connection.privmsg(target, f"{transaction['timestamp']}: Perte de {transaction['amount']} crédits")
                    elif transaction['type'] == 'transfer':
                        connection.privmsg(target, f"{transaction['timestamp']}: Transfert de {transaction['amount']} crédits à un autre joueur")
                    elif transaction['type'] == 'receive':
                        connection.privmsg(target, f"{transaction['timestamp']}: Réception de {transaction['amount']} crédits d'un autre joueur")
            else:
                connection.privmsg(target, "Aucune transaction trouvée.")
        else:
            connection.privmsg(target, f"Vous devez d'abord vous inscrire avec !register, {nickname}!")

    def record_transaction(self, nickname, amount, transaction_type):
        self.cursor.execute("INSERT INTO transactions (nick, amount, type) VALUES (%s, %s, %s)", (nickname, amount, transaction_type))
        self.db.commit()

    def flip_coin(self, connection, target, nickname):
        if not self.check_account(connection, target, nickname):
            return
        outcomes = ['pile', 'face']
        result = random.choice(outcomes)
        if result == "pile":
            self.cursor.execute("UPDATE accounts SET balance = balance + %s WHERE nick = %s", (10, nickname))
            self.record_transaction(nickname, 10, "win")
            connection.privmsg(target, f"Bravo! Vous avez gagné 10 crédits en obtenant {result}.")
        else:
            self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (10, nickname))
            self.record_transaction(nickname, 10, "lose")
            connection.privmsg(target, f"Dommage! Vous avez perdu 10 crédits en obtenant {result}.")
        self.db.commit()

    def play_roulette(self, connection, target, nickname, message):
        if not self.check_account(connection, target, nickname):
            return
        if len(message.split()) != 2:
            connection.privmsg(target, "Usage: !roulette <mise>")
            return
        try:
            bet = int(message.split()[1])
        except ValueError:
            connection.privmsg(target, "La mise doit être un nombre entier.")
            return
        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (nickname,))
        account = self.cursor.fetchone()
        if account is None:
            connection.privmsg(target, f"Vous devez d'abord vous inscrire avec !register, {nickname}!")
        elif account['balance'] < bet:
            connection.privmsg(target, "Vous n'avez pas assez de crédits.")
        else:
            outcomes = ['rouge', 'noir']
            result = random.choice(outcomes)
            if result == "rouge":
                self.cursor.execute("UPDATE accounts SET balance = balance + %s WHERE nick = %s", (bet, nickname))
                self.record_transaction(nickname, bet, "win")
                connection.privmsg(target, f"Félicitations! Vous avez gagné {bet} crédits en obtenant {result}.")
            else:
                self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (bet, nickname))
                self.record_transaction(nickname, bet, "lose")
                connection.privmsg(target, f"Désolé! Vous avez perdu {bet} crédits en obtenant {result}.")
            self.db.commit()

    def play_dice(self, connection, target, nickname, message):
        if not self.check_account(connection, target, nickname):
            return
        if len(message.split()) != 2:
            connection.privmsg(target, "Usage: !dice <mise>")
            return
        try:
            bet = int(message.split()[1])
        except ValueError:
            connection.privmsg(target, "La mise doit être un nombre entier.")
            return
        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (nickname,))
        account = self.cursor.fetchone()
        if account is None:
            connection.privmsg(target, f"Vous devez d'abord vous inscrire avec !register, {nickname}!")
        elif account['balance'] < bet:
            connection.privmsg(target, "Vous n'avez pas assez de crédits.")
        else:
            roll = random.randint(1, 6)
            if roll <= 3:  # On considère que le joueur gagne s'il obtient 4, 5 ou 6
                self.cursor.execute("UPDATE accounts SET balance = balance + %s WHERE nick = %s", (bet, nickname))
                self.record_transaction(nickname, bet, "win")
                connection.privmsg(target, f"Félicitations! Vous avez gagné {bet} crédits en lançant un dé et en obtenant {roll}.")
            else:
                self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (bet, nickname))
                self.record_transaction(nickname, bet, "lose")
                connection.privmsg(target, f"Désolé! Vous avez perdu {bet} crédits en lançant un dé et en obtenant {roll}.")
            self.db.commit()

    def play_slots(self, connection, target, nickname, message):
        if not self.check_account(connection, target, nickname):
            return
        if len(message.split()) != 2:
            connection.privmsg(target, "Usage: !slots <mise>")
            return
        try:
            bet = int(message.split()[1])
        except ValueError:
            connection.privmsg(target, "La mise doit être un nombre entier.")
            return
        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (nickname,))
        account = self.cursor.fetchone()
        if account is None:
            connection.privmsg(target, f"Vous devez d'abord vous inscrire avec !register, {nickname}!")
        elif account['balance'] < bet:
            connection.privmsg(target, "Vous n'avez pas assez de crédits.")
        else:
            slot_icons = ["🍒", "🍋", "🍊", "🍇", "🍉"]
            slots_result = [random.choice(slot_icons) for _ in range(3)]
            connection.privmsg(target, f"Résultat des machines à sous: {' '.join(slots_result)}")
            if slots_result.count(slots_result[0]) == 3:
                winnings = bet * 10
                self.cursor.execute("UPDATE accounts SET balance = balance + %s WHERE nick = %s", (winnings, nickname))
                self.record_transaction(nickname, winnings, "win")
                connection.privmsg(target, f"Félicitations! Vous avez gagné {winnings} crédits en alignant 3 symboles identiques!")
            else:
                self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (bet, nickname))
                self.record_transaction(nickname, bet, "lose")
                connection.privmsg(target, f"Désolé! Vous avez perdu {bet} crédits.")
            self.db.commit()
            
    def play_guess_the_number(self, connection, target, nickname, message):
        if not self.check_account(connection, target, nickname):
            return
        if len(message.split()) != 2:
            connection.privmsg(target, "Usage: !devine <nombre>")
            return
        try:
            guess = int(message.split()[1])
        except ValueError:
            connection.privmsg(target, "Veuillez deviner un nombre entier.")
            return
        number = random.randint(1, 10)
        if guess == number:
            winnings = 100
            self.cursor.execute("UPDATE accounts SET balance = balance + %s WHERE nick = %s", (winnings, nickname))
            self.record_transaction(nickname, winnings, "win")
            connection.privmsg(target, f"Félicitations! Vous avez deviné le nombre {number} et gagné {winnings} crédits!")
        else:
            self.cursor.execute("UPDATE accounts SET balance = balance - 10 WHERE nick = %s", (nickname,))
            self.record_transaction(nickname, 10, "lose")
            connection.privmsg(target, f"Dommage! Le nombre était {number}. Vous avez perdu 10 crédits.")
        self.db.commit()

    def request_credit(self, connection, target, nickname):
        # Vérifiez si l'utilisateur a déjà demandé un crédit aujourd'hui
        today = datetime.date.today()
        self.cursor.execute("SELECT last_credit_request FROM accounts WHERE nick = %s", (nickname,))
        last_request_date = self.cursor.fetchone()
        if last_request_date is not None and last_request_date['last_credit_request'] == today:
            connection.privmsg(target, f"{nickname}, vous avez déjà demandé un crédit aujourd'hui. Veuillez réessayer demain.")
            return

        # Mettez à jour la date de la dernière demande de crédit
        self.cursor.execute("UPDATE accounts SET last_credit_request = %s WHERE nick = %s", (today, nickname))

        # Accordez un crédit de 100 crédits à l'utilisateur
        self.cursor.execute("UPDATE accounts SET balance = balance + 100 WHERE nick = %s", (nickname,))
        self.db.commit()

        connection.privmsg(target, f"{nickname}, vous avez reçu un crédit de 100 crédits.")
        
    def start_juste_prix(self, connection, target, nickname):
        if not self.check_account(connection, target, nickname):
            return
        self.juste_prix_item, (min_price, max_price) = random.choice(list(self.articles.items()))
        self.juste_prix_price = random.randint(min_price, max_price)
        self.juste_prix_running = True
        connection.privmsg(target, f"Un nouvel article est en jeu: {self.juste_prix_item}. Faites !bid <votre offre> pour participer!")

    def place_bid(self, connection, target, nickname, message):
        bid = message.split()[1]
        try:
            bid = int(bid)
        except ValueError:
            connection.privmsg(target, "Votre offre doit être un nombre entier.")
            return
        if bid <= 0:
            connection.privmsg(target, "Votre offre doit être supérieure à zéro.")
            return
        if bid > self.juste_prix_price:
            connection.privmsg(target, f"Félicitations, {nickname}! Vous avez gagné l'article {self.juste_prix_item} avec une offre de {bid} crédits.")
            self.cursor.execute("UPDATE accounts SET balance = balance - %s, errors = 0 WHERE nick = %s", (bid, nickname))
            self.cursor.execute("INSERT INTO transactions (nick, amount, type) VALUES (%s, %s, %s)", (nickname, bid, "juste_prix"))
            self.db.commit()
            self.reset_juste_prix()
        else:
            self.cursor.execute("UPDATE accounts SET errors = errors + 1 WHERE nick = %s", (nickname,))
            self.db.commit()
            if self.check_errors(nickname):
                connection.privmsg(target, f"Désolé, {nickname}. Votre offre est trop basse. Essayez à nouveau!")
                self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (10, nickname))  # Perte de 10 crédits en cas d'erreur
                self.db.commit()
                self.reset_juste_prix()

    def check_errors(self, nickname):
        self.cursor.execute("SELECT errors FROM accounts WHERE nick = %s", (nickname,))
        errors = self.cursor.fetchone()['errors']
        return errors >= 3

    def reset_juste_prix(self):
        self.juste_prix_running = False
        self.juste_prix_item = None
        self.juste_prix_price = None

    def record_transaction(self, nickname, amount, transaction_type):
        self.cursor.execute("INSERT INTO transactions (nick, amount, type) VALUES (%s, %s, %s)", (nickname, amount, transaction_type))
        self.db.commit()
       
    def start_duck_hunt(self, connection, target, nickname):
        if not self.check_account(connection, target, nickname):
            return
        self.duck_hunt_running = True
        self.duck_position = random.randint(1, 100)
        connection.privmsg(target, f"Un canard sauvage apparaît! Utilisez !shoot <numéro> pour tirer (1-100).")

    def shoot_duck(self, connection, target, nickname, message):
        if not self.check_account(connection, target, nickname):
            return
        if not self.duck_hunt_running:
            connection.privmsg(target, "Il n'y a pas de canard à chasser pour le moment.")
            return
        try:
            shot_position = int(message.split()[1])
        except (IndexError, ValueError):
            connection.privmsg(target, "Veuillez spécifier un numéro valide pour tirer.")
            return
        if shot_position == self.duck_position:
            connection.privmsg(target, f"Félicitations, {nickname}! Vous avez abattu le canard!")
            reward = random.randint(20, 50)
            self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (10, nickname))
            self.record_transaction(nickname, reward, "duck_hunt_win")
            self.reset_duck_hunt()
        else:
            connection.privmsg(target, f"Dommage, {nickname}. Le canard s'est échappé.")
            self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (10, nickname))  # Pénalité de 10 crédits en cas de tir raté
            self.record_transaction(nickname, 10, "duck_hunt_penalty")
            self.reset_duck_hunt()
        self.db.commit()

    def reset_duck_hunt(self):
        self.duck_hunt_running = False
        self.duck_position = None      
        
    def create_account(self, nickname):
        if nickname not in self.accounts:
            self.accounts[nickname] = 100  # Créer un nouveau compte avec 100 crédits
            return True
        else:
            return False  # Le compte existe déjà

    def delete_account(self, connection, target, nickname):
        if not self.check_account(connection, target, nickname):
            return
        self.cursor.execute("DELETE FROM accounts WHERE nick = %s", (nickname,))
        self.db.commit()
        connection.privmsg(target, f"Le compte de {nickname} a été supprimé avec succès.")
        
if __name__ == "__main__":
    bot = CasinoBot()
    bot.start()
