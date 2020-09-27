import socket
import tkinter
import errno
from threading import Thread

IP = "127.0.0.1"
PORT = 1234
IP_ADDRESS = (IP, PORT)
HEADER_LENGTH = 10

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(IP_ADDRESS)
client_socket.setblocking(False)
my_username = False
sent_messages = []


def typing_message(*args):
    if msg_list.get(msg_list.size() - 1) != welcome_msg:
        msg = 'Typing...'.encode('utf-8')
        msg_header = f"{len(msg):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(msg_header + msg)


def close(event=None):
    """This function is to be called when the window is closed."""
    client_socket.close()
    top.quit()


def send(event=None):  # event is passed by binders.
    """Handles sending of messages."""
    msg = my_msg.get()
    my_msg.set("")  # Clears input field.
    if msg:
        print("Message sent: {}".format(msg))
        sent_messages.append(msg)
        msg = msg.encode('utf-8')
        msg_header = f"{len(msg):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(msg_header + msg)


top = tkinter.Tk()
top.title("Chatter")

messages_frame = tkinter.Frame(top)
my_msg = tkinter.StringVar()  # Input field
scrollbar = tkinter.Scrollbar(messages_frame)
msg_list = tkinter.Listbox(messages_frame, height=30, width=100, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
welcome_msg = "Welcome to the chat! Please first enter your username and press enter!"
msg_list.insert(tkinter.END, welcome_msg)
my_msg.trace('w', typing_message)
messages_frame.pack()

entry_field = tkinter.Entry(top, textvariable=my_msg)
entry_field.bind("<Return>", send)
entry_field.pack()
send_button = tkinter.Button(top, text="Send", command=send)
send_button.pack()

top.protocol("WM_DELETE_WINDOW", close)


def receive():
    """Handles receiving of messages."""
    while True:
        try:
            username_header = client_socket.recv(HEADER_LENGTH)
            if not len(username_header):
                print("Connection closed by the server")
                break

            username_length = int(username_header.decode('utf-8').strip())
            username = client_socket.recv(username_length).decode('utf-8')

            message_header = client_socket.recv(HEADER_LENGTH)
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')
            if username == 'Welcome':
                my_username = message
            if message == 'Typing...':
                print(f"{username} is {message}")
                if sent_messages:
                    for msg in sent_messages:
                        print("Message read: {}".format(msg))
                        sent_messages.remove(msg)
            else:
                if username == my_username:
                    print("Message delivered: {}".format(message))
                msg_list.insert(tkinter.END, f"{username} > {message}")
                print(f"{username} > {message}")

        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print("Reading error", str(e))
                break

        except Exception as e:
            print('General error', str(e))
            break

    close()


receive_thread = Thread(target=receive)
receive_thread.start()
tkinter.mainloop()  # Starts GUI execution.
