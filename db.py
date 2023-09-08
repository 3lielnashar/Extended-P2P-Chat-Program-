from pymongo import MongoClient

# Includes database operations
class DB:


    # db initializations
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['p2p-chat']


    # checks if an account with the username exists
    def is_account_exist(self, username):
        if self.db.accounts.find_one({'username': username}):
            return True
        else:
            return False
    

    # registers a user
    def register(self, username, password):
        account = {
            "username": username,
            "password": password
        }
        self.db.accounts.insert_one(account)


    # retrieves the password for a given username
    def get_password(self, username):
        return self.db.accounts.find_one({"username": username})["password"]


    # checks if an account with the username online
    def is_account_online(self, username):
        if self.db.online_peers.find_one({"username": username}):
            return True
        else:
            return False

    
    # logs in the user
    def user_login(self, username, ip, port):
        online_peer = {
            "username": username,
            "ip": ip,
            "port": port
        }
        self.db.online_peers.insert_one(online_peer)
    

    # logs out the user 
    def user_logout(self, username):
        acc=self.db["online_peers"].find_one({"username": username})
        self.db["online_peers"].delete_one(acc)
    

    # retrieves the ip address and the port number of the username
    def get_peer_ip_port(self, username):
        res = self.db.online_peers.find_one({"username": username})
        if res:
            return (res["ip"], res["port"])
        return None

    def create_room(self, room_name):
        room = {
            "room_name": room_name,
            "members": []
        }
        self.db.rooms.insert_one(room)

    def get_room(self, room_name):
        room = self.db.rooms.find_one({"room_name": room_name})
        if room:
            return room
        return None

    def get_rooms(self):
        cursor = self.db.rooms.find({})
        rooms = []
        for room in cursor:
            rooms.append(room['room_name'])

        return rooms
    def add_member(self, room_name, member):
        self.db.rooms.update_one({"room_name": room_name}, {"$push": {"members": member}})

    # remove member from a room by member[0] (username)
    def remove_member_by_username(self, room_name, username):
        self.db.rooms.update_one({"room_name": room_name}, {"$pull": {"members": {"username": username}}})

    def _remove_member(self, room_name, member):
        self.db.rooms.update_one({"room_name": room_name}, {"$pull": {"members": member}})
    
    # remove member from any room he is in
    def remove_member_from_all_rooms(self, member):
        rooms = self.get_rooms_of_member(member)
        for room in rooms:
            self._remove_member(room["room_name"], member)
    def delete_room(self, room_name):
        self.db.rooms.delete_one({"room_name": room_name})
    
    def get_members(self, room_name):
        room = self.db.rooms.find_one({"room_name": room_name})
        if room:
            return room["members"]
        return None
    
    def get_member(self, room_name, member_name):
        room = self.db.rooms.find_one({"room_name": room_name})
        if room:
            for member in room['members']:
                if member[0] == member_name:
                    return member
        return None

    def remove_member(self, room_name, member_name):
        member = self.get_member(room_name, member_name)
        if member:
            self._remove_member(room_name, member)
            return True
        return False

    def get_rooms_of_member(self, member):
        return self.db.rooms.find({"members": member})
