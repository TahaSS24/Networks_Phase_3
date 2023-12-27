from pymongo import MongoClient


class DB:
    def __init__(self):
        # Initialize MongoDB Atlas client and select database and collections
        self.atlas_connection_string = "mongodb+srv://Ahmed_Taha:NetworksGroup30@p2p-chat.h8is5dk.mongodb.net/?retryWrites=true&w=majority"
        self.client = MongoClient(self.atlas_connection_string)
        self.db = self.client["p2p-chat-phase-3"]
        self.accounts = self.db["accounts"]

    def is_account_exist(self, username):
        # Check if an account with the given username exists
        return self.accounts.count_documents({"username": username}) > 0

    def register(self, username, password):
        # Register a new user account
        account = {"username": username, "password": password}
        self.accounts.insert_one(account)

    def get_password(self, username):
        # Retrieve the password for a given username
        user = self.accounts.find_one({"username": username})
        if user:
            return user["password"]
        else:
            return None
