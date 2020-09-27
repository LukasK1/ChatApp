import socket
import select

IP = "127.0.0.1"
PORT = 1234

HEADER_LENGTH = 10
HISTORY_LENGTH = 50  # Number of saved messages per session
MAX_USERS = 2  # Maximum number of users per session

# socket.AF_INET - address family, IPv4
# socket.SOCK_STREAM - TCP, conection-based
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP, PORT))
server_socket.listen(MAX_USERS)

sockets_list = [server_socket]
message_history = []
clients = {}

print(f'Listening for connections on {IP}:{PORT}...')


# Handles message receiving
def receive_message(client):
    try:
        # Receive our "header" containing message length, it's size is defined and constant
        message_header = client.recv(HEADER_LENGTH)
        if not len(message_header):
            return False

        message_length = int(message_header.decode('utf-8').strip())
        # Return an object of message header and message data
        return {'header': message_header, 'data': client.recv(message_length)}

    except:
        # Client closed connection violently
        return False


while True:
    # Calls Unix select() system call or Windows select() WinSock call with three parameters:
    #   - rlist - sockets to be monitored for incoming data
    #   - wlist - sockets for data to be send to
    #   - xlist - sockets to be monitored for exceptions
    # Returns lists:
    #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
    #   - writing - sockets ready for data to be send through them
    #   - errors  - sockets with some exceptions
    # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()

            # First message is username of the Client
            user = receive_message(client_socket)

            # Check if client disconnected before he sent his username
            if user is False:
                continue

            sockets_list.append(client_socket)
            clients[client_socket] = user

            print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
            welcome = "Welcome".encode('utf-8')
            welcome_header = f"{len(welcome):<{HEADER_LENGTH}}".encode('utf-8')
            client_socket.send(welcome_header + welcome + user['header'] + user['data'])
            if message_history:
                for msg in message_history:
                    client_socket.send(msg)
        else:
            message = receive_message(notified_socket)

            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue

            user = clients[notified_socket]
            outgoing_message = user['header'] + user['data'] + message['header'] + message['data']
            if message['data'].decode("utf-8") != 'Typing...':
                print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')
                message_history.append(outgoing_message)
                if len(message_history) > HISTORY_LENGTH:
                    message_history.pop(0)
            # Iterate over connected clients and broadcast message
            for client_socket in clients:
                print(client_socket)
                print(notified_socket)
                if message['data'].decode("utf-8") == 'Typing...':
                    if not (client_socket == notified_socket):
                        client_socket.send(outgoing_message)
                else:
                    client_socket.send(outgoing_message)

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
