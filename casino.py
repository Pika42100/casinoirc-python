import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
import pymysql
import random
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
        drinks_list = ", ".join([f"{drink.capitalize()} ({price} crédits)" for drink, price in self.drinks.items()])
        connection.privmsg(target, f"Boissons disponibles au bar : {drinks_list}")

    # Fonction pour permettre aux utilisateurs d'acheter des boissons
    def buy_drink(self, connection, target, nickname, drink):
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
        elif message.startswith("!devine"):
            nickname = event.source.nick
            self.play_guess_the_number(connection, event.target, nickname, message)

    def register_user(self, connection, target, nickname):
        self.cursor.execute("SELECT * FROM accounts WHERE nick = %s", (nickname,))
        if self.cursor.fetchone() is None:
            self.cursor.execute("INSERT INTO accounts (nick, balance, last_credit_request) VALUES (%s, %s, %s)", (nickname, 100, datetime.date.today()))
            self.db.commit()
            connection.privmsg(target, f"Vous avez été enregistré avec succès, {nickname}!")
        else:
            connection.privmsg(target, f"Vous êtes déjà enregistré, {nickname}!")

    def play_casino(self, connection, target, nickname, message):
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
                self.cursor.execute("UPDATE accounts SET balance = balance + %s WHERE nick = %s", (bet, nickname))
                self.record_transaction(nickname, bet, "win")
                connection.privmsg(target, f"Félicitations! Vous avez gagné {bet} crédits.")
            else:
                self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (bet, nickname))
                self.record_transaction(nickname, bet, "lose")
                connection.privmsg(target, f"Désolé! Vous avez perdu {bet} crédits.")
            self.db.commit()

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
        connection.privmsg(nickname, "!top10 - Afficher les 10 meilleurs joueurs")
        connection.privmsg(nickname, "!aide - Afficher cet message d'aide")
        connection.privmsg(nickname, "!quit - Quitter le casino")
        connection.privmsg(nickname, "!flipcoin - Lancer une pièce")
        connection.privmsg(nickname, "!roulette <mise> - Jouer à la roulette")
        connection.privmsg(nickname, "!dice <mise> - Jouer au jeu de dés")
        connection.privmsg(nickname, "!slots <mise> - Jouer à la machine à sous")
        connection.privmsg(nickname, "!transfer <destinataire> <montant>")
        connection.privmsg(nickname, "!bar afiche les boisson disponible/!buy <montant> achète la boisson)"
        connection.privmsg(nickname, "!depot <montant> - Déposer de l'argent dans votre compte en banque ########PAS ENCORS FONCTIONEL########")
        connection.privmsg(nickname, "!credit - Demander un crédit bancaire 1 par jour")
        connection.privmsg(nickname, "!delete_account - Supprimer votre compte(1fois par semaine)#######PAS ENCORS FONCTIONEL####### ")

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
        
    def delete_account(self, connection, target, nickname):
        self.cursor.execute("SELECT last_deleted FROM accounts WHERE nick = %s", (nickname,))
        last_deleted = self.cursor.fetchone()
        if last_deleted and (datetime.datetime.now() - last_deleted['last_deleted']).days < 7:
            connection.privmsg(target, "Vous ne pouvez supprimer votre compte qu'une fois par semaine.")
            return
        self.cursor.execute("DELETE FROM accounts WHERE nick = %s", (nickname,))
        self.db.commit()
        connection.privmsg(target, f"Votre compte a été supprimé avec succès, {nickname}!")
        self.cursor.execute("INSERT INTO accounts (nick, balance, bank_balance, last_deleted) VALUES (%s, %s, %s, %s)", (nickname, 0, 0, datetime.datetime.now()))
        self.db.commit()
        
    def deposit(self, connection, target, nickname, amount):
        try:
            amount = int(amount)
        except ValueError:
            connection.privmsg(target, "Le montant doit être un nombre entier.")
            return

        if amount <= 0:
            connection.privmsg(target, "Le montant doit être supérieur à zéro.")
            return

        self.cursor.execute("SELECT balance FROM accounts WHERE nick = %s", (nickname,))
        account = self.cursor.fetchone()
        if account is None:
            connection.privmsg(target, f"Vous devez d'abord vous inscrire avec !register, {nickname}!")
            return

        if account['balance'] < amount:
            connection.privmsg(target, f"Vous n'avez pas assez de crédits pour déposer {amount} crédits.")
            return

        self.cursor.execute("UPDATE accounts SET balance = balance - %s WHERE nick = %s", (amount, nickname))
        self.cursor.execute("UPDATE accounts SET bank_balance = bank_balance + %s WHERE nick = %s", (amount, nickname))
        self.db.commit()
        connection.privmsg(target, f"{nickname}, {amount} crédits ont été ajoutés à votre compte en banque.")

if __name__ == "__main__":
    bot = CasinoBot()
    bot.start()
