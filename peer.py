from socket import *
import threading
import select


class PeerServer(threading.Thread):
    # Peer server initialization
    def __init__(self, username, peerServerPort):
        threading.Thread.__init__(self)
        self.username = username
        self.peerServerSocket = socket(AF_INET, SOCK_STREAM)
        self.peerServerHost = gethostbyname(gethostname())
        self.peerServerPort = peerServerPort
        self.peerServerSocket.bind((self.peerServerHost, self.peerServerPort))
        self.inputs = [self.peerServerSocket]

    # main method of the peer server thread
    def run(self):
        self.peerServerSocket.listen()
        while self.inputs and self.username != None:
            # monitors for the incoming connections
            readable, writable, exceptional = select.select(self.inputs, [], [])
            for sock in readable:
                try:
                    # if the socket that is receiving the connection is the tcp socket of the peer's server, enters here
                    if sock is self.peerServerSocket:
                        # accepts the connection, and adds its connection socket to the inputs list
                        if self.username == None:
                            break
                        connectedPeerSocket, addr = sock.accept()
                        self.inputs.append(connectedPeerSocket)

                    # if the socket that receives the data is used to communicate with a connected peer, then enters here
                    else:
                        message = sock.recv(1024).decode().split("\n")
                        if len(message) == 0:
                            sock.close()
                            self.inputs.remove(sock)
                        elif message[0] == "chatroom-join":
                            print(message[1] + " has joined the chatroom.")
                            peer = message[2].split(",")
                            peerHost = peer[0]
                            peerPort = int(peer[1])
                            sock = socket(AF_INET, SOCK_STREAM)
                            sock.connect((peerHost, peerPort))
                            connectedPeers.append(sock)
                        elif message[0] == "chatroom-leave":
                            print(message[1] + " has left the chatroom.")
                            sock.close()
                            self.inputs.remove(sock)
                        elif message[0] == "chat-message":
                            username = message[1]
                            content = "\n".join(message[2:])
                            print(username + " -> " + content)
                except:
                    pass


class PeerClient(threading.Thread):
    def __init__(self, username, chatroom, peerServerHost, peerServerPort, peersToConnect=None):
        threading.Thread.__init__(self)
        self.username = username
        self.chatroom = chatroom
        if peersToConnect != None:
            for peer in peersToConnect:
                peer = peer.split(",")
                peerHost = peer[0]
                peerPort = int(peer[1])
                sock = socket(AF_INET, SOCK_STREAM)
                sock.connect((peerHost, peerPort))
                message = "chatroom-join\n{}\n{},{}".format(self.username, peerServerHost, peerServerPort)
                sock.send(message.encode())
                connectedPeers.append(sock)

    # main method of the peer client thread
    def run(self):
        print('Chatroom joined Successfully. \nStart typing to send a message. Send ":quit" to leave the chatroom.')
        while self.chatroom != None:
            content = input()

            if content == ":quit":
                message = "chatroom-leave\n" + self.username
            else:
                message = "chat-message\n{}\n{}".format(self.username, content)

            for sock in connectedPeers:
                try:
                    sock.send(message.encode())
                except:
                    pass

            if content == ":quit":
                self.chatroom = None
                for sock in connectedPeers:
                    sock.close()


class peerMain:
    # peer initializations
    def __init__(self, username=None, peerServerPort=None):
        # registry host, port
        self.registryName = input("Enter IP address of registry: ")
        self.registryPort = 15600

        # connection initialization
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.connect((self.registryName, self.registryPort))
        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        self.registryUDPPort = 15500

        # peer info
        self.username = username
        self.peerServerPort = peerServerPort
        self.peerServer = None
        self.peerClient = None

        # timer for hello
        self.timer = None

        # run the main
        self.main()

    def main(self):
        # main loop for program
        while True:
            choice = "0"

            # in case that the user is not yet logged in
            if self.username == None:
                choice = input("\nOptions: \n\tCreate account: 1 \n\tLogin: 2 \nChoice: ")

                match choice:
                    # if choice is 1, creates an account with entered username, password
                    case "1":
                        while True:
                            username = input("Username: ")
                            if len(username) < 4:
                                print("Username must be at least 4 characters long")
                            else:
                                break

                        while True:
                            password = input("Password: ")
                            if len(password) < 8:
                                print("Password must be at least 8 characters long")
                            else:
                                break

                        self.createAccount(username, password)

                    # if choice is 2 and user is not logged in, logs in with entered username, password
                    case "2":
                        username = input("Username: ")
                        password = input("Password: ")
                        while True:
                            port = input("Port to receive messages: ")
                            if port.isdigit() == False:
                                print("Port number must be integer between 1024 and 65535")
                            else:
                                port = int(port)
                                if port < 1024 or port > 65535:
                                    print("Port number must be integer between 1024 and 65535")
                                else:
                                    break
                        self.login(username, password, port)

                    case _:
                        print("Invalid input. Please try again")

            # otherwise if user is already logged in
            else:
                choice = input(
                    "\nOptions: \n\tLogout: 1 \n\tSearch for User: 2 \n\tActive Users: 3"
                    + "\n\tJoin Chatroom: 4 \n\tShow Chatrooms: 5 \n\tCreate Chatroom: 6"
                    + "\nChoice: "
                )

                match choice:
                    # if choice is 1 user is logged out
                    case "1":
                        self.logout()

                    # if choice is 2 user is asked for username to search
                    case "2":
                        username = input("Username to be searched: ")
                        self.searchUser(username)

                    # if choice is 3 prints list of online users
                    case "3":
                        self.userList()

                    # if choice is 4 joins chatroom
                    case "4":
                        name = input("Chatroom name: ")
                        self.chatroomJoin(name)

                    # if choice is 5 shows available chatrooms
                    case "5":
                        self.chatroomList()

                    # if choice is 6 creates chatroom
                    case "6":
                        while True:
                            name = input("Chatroom name: ")
                            if len(name) < 4:
                                print("Chatroom name must be at least 4 characters long")
                            else:
                                self.chatroomCreate(name)
                                break

                    case _:
                        print("Invalid input. Please try again")

    def createAccount(self, username, password):
        message = "register-request\n{}\n{}".format(username, password)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()

        match response:
            case "register-success":
                print("Account created successfully.")
            case "register-username-exist":
                print("Username already exists.")

    def login(self, username, password, peerServerPort):
        message = "login-request\n{}\n{}\n{}".format(username, password, peerServerPort)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()

        match response:
            case "login-fail":
                print("Wrong username or password.")
            case "login-user-online":
                print("Account is already online.")

            case "login-success":
                print("Logged in successfully.")
                self.username = username
                self.peerServerPort = peerServerPort
                self.peerServer = PeerServer(self.username, self.peerServerPort)
                self.peerServer.start()
                self.sendHelloMessage()

    def logout(self):
        self.username = None
        print("Logged out successfully")
        message = "logout"
        self.tcpClientSocket.send(message.encode())

        if self.peerServer != None:
            self.peerServer.username = None
            self.peerServer.peerServerSocket.close()
            self.peerServer = None

        if self.peerClient != None:
            for peer in connectedPeers:
                peer.close()
            connectedPeers.clear()
            self.peerClient.chatroom = None
            self.peerClient = None

        if self.timer is not None:
            self.timer.cancel()

    def searchUser(self, username):
        message = "search-request\n{}".format(username)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split("\n")

        match response[0]:
            case "search-success":
                print("{} is logged in -> {} : ".format(username, response[1], response[2]))
            case "search-not-online":
                print("{} is not online.".format(username))
            case "search-not-found":
                print("{} was not found.".format(username))

    def userList(self):
        message = "users-list-request"
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split("\n")

        if response[0] == "users-list":
            print("Online Users:")
            for user in response[1:]:
                print("\n\t" + user)

    def chatroomJoin(self, name):
        message = "chatroom-join-request\n{}".format(name)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split("\n")

        match response[0]:
            case "chatroom-not-found":
                print("No chatroom exists with this name.")
            case "chatroom-join-success":
                if len(response) == 1:
                    self.peerClient = PeerClient(self.username, name, gethostbyname(gethostname()), self.peerServerPort)
                else:
                    self.peerClient = PeerClient(
                        self.username, name, gethostbyname(gethostname()), self.peerServerPort, response[1:]
                    )
                self.peerClient.start()
                self.peerClient.join()
                # This section will only run after user quits the chatroom
                if (self.peerServer) and (len(self.peerServer.inputs) > 1):
                    for sock in self.peerServer.inputs[1:]:
                        sock.close()
                    self.peerServer.inputs = [self.peerServer.inputs[0]]

                self.tcpClientSocket.send("chatroom-leave-request".encode())

    def chatroomList(self):
        message = "chatroom-list-request"
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split("\n")

        if response[0] == "chatroom-list":
            print("Available Chatrooms:")
            for chatroom in response[1:]:
                print("\n\t" + chatroom + " users connected")

    def chatroomCreate(self, name):
        message = "chatroom-creation-request\n{}".format(name)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()

        match response:
            case "chatroom-name-exists":
                print("There already exists a chatroom with this name.")
            case "chatroom-creation-success":
                print("Chatroom created successfully")
                self.chatroomJoin(name)

    def sendHelloMessage(self):
        message = "hello\n{}".format(self.username)
        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()


# list of connected peers
connectedPeers = []

# peer is started
peerMain()
