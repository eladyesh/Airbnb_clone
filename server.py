# importing the required modules
from select import select
from datetime import datetime
import pickle
from socket import *
from data_base.manage_data_base import *
from Event import Event
import ssl
import warnings
import numpy as np
from os import walk
import os

# getting the file's path
PATH = os.path.dirname(os.path.realpath(__file__))


def get_database(name):
    """
    function gets the database information
    :param name: database name
    :return: database information (as dict)
    """
    data = fetch_all(name)

    data_base_dict = {}
    for i in data:
        data_base_dict[i[0]] = i[1:]

    return data_base_dict


class Server:
    """
    Server class manages all the requests from client connected to it's socket.
    Server is responsible for broadcasting important messages and information
    to the other clients or users that are connected
    """

    def __init__(self):

        # initiating server
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # setting server's socket
        if len(gethostbyname_ex(gethostname())[-1]) > 1:
            self.__HOST = gethostbyname_ex(gethostname())[-1][0]
        else:
            self.__HOST = gethostbyname_ex(gethostname())[-1][-1]
        self.__HOST = "172.16.2.74"

        # creating server socket, wrapping with ssl
        self.server = ssl.wrap_socket(sock=socket(AF_INET, SOCK_STREAM), server_side=True, certfile="certificate.pem",
                                      keyfile="privkey.pem")

        # setting up server
        self._client_time = dict({})
        self.server.bind((self.__HOST, 50002))
        self.server.listen(5)
        self.server.setblocking(False)
        self.main_socks = [self.server]
        self.read_sockets = []
        self.write_sockets = []
        self._BUFFER = 1024

        # setting important variable as None to avoid errors
        self.image = b""
        self.start_image = False
        self._server_time = datetime.now()

        self.event_handler = Event()

        self._purchasing = dict({})
        self._client_image = dict({})
        self._client_purchase = dict({})
        self._client_notifications = dict({})
        self._client_email = dict({})
        self._logged_client = dict({})
        self.run_once = 0
        self.positions_available = None

        # getting information from database
        self.clients = get_database("record")
        self.reviews = get_database("reviews")
        self.offers = get_database("offers")
        self.purchases = get_database("purchases")

        self.read_sockets += self.main_socks

    def _remove_from_lists(self, sock):
        """
        function removes the socket from all the possible lists and dictionaries it's in
        :param sock: the socket connected to the server
        :return: None
        """

        sock.close()
        self.read_sockets.remove(sock)
        self.write_sockets.remove(sock)
        if sock in self._purchasing.keys():
            self._purchasing.pop(sock)

    def _broadcast(self, client, msg, pick):
        """
        function broadcasts to all sockets connected to the server
        :param client: the socket object
        :param pick: whether message should be pickled or not
        :param msg: the message needed to be broadcast
        :return: None
        """

        if not pick:
            for sockobj in self.writeables:
                try:
                    if sockobj.getpeername() != client.getpeername():
                        sockobj.send(msg.encode())
                except (OSError, ValueError):
                    continue

        else:
            for sockobj in self.writeables:
                try:
                    if sockobj.getpeername() != client.getpeername():
                        sockobj.send(pickle.dumps(msg))
                except (OSError, ValueError):
                    continue

    def _broadcast_to_all(self, msg, pick):
        """
        function broadcasts to all sockets connected to the server
        :param writables: writable sockets
        :param msg: the message needed to be broadcast
        :return: None
        """

        if not pick:
            for sockobj in self.writeables:
                try:
                    sockobj.send(msg.encode())
                except (OSError, ValueError):
                    continue

        else:
            for sockobj in self.writeables:
                try:
                    sockobj.send(pickle.dumps(msg))
                except (OSError, ValueError):
                    continue

    def _broadcast_bites(self, client, msg):
        """
        function broadcasts bite message to all clients
        :param client: the client to which don't send the message
        :param msg: the message to be sent
        :return: None
        """

        for sockobj in self.writeables:
            try:
                if sockobj.getpeername() != client.getpeername():
                    sockobj.send(f"NAME {self.image_name}".encode())
                    sockobj.send(msg)
            except (OSError, ValueError):
                continue

    def _get_avarage_rating_for_room(self, offer_id):
        """
        function gets the average rating for an offer by it's id
        :param offer_id: offer id
        :return: average rating for the offer (as int)
        """
        ratings = fetch_row_by_parameter("ratings", "offer_id", offer_id)
        lst = []
        for i in ratings:
            lst.append(float(i[3]))
        return int(np.mean(lst)) if lst != [] else 0

    def _check_for_ending_of_purchase(self, socketobj, date):
        """
        function checks for the ending for purchase, and notifying client when he logs in (online)
        :param socketobj: the socket object of the client
        :param date: the date to check by
        :return:
        """

        if socketobj in self._client_purchase.keys():

            # getting the dates from his purchase
            purchase_id = self._client_purchase[socketobj]
            dates = fetch_row_by_parameter("purchases", "purchase_id", purchase_id)[0][2]
            check_in, check_out = dates.split("-")[0][:-1], dates.split("-")[1][1:]
            date_check_in, date_check_out = datetime.strptime(check_in, '%Y/%m/%d'), datetime.strptime(check_out,
                                                                                                       '%Y/%m/%d')

            # checking if the ending of the purchase has arrived
            time_today = str(date).replace("-", "/")
            date_time_today = datetime.strptime(time_today[:time_today.find(" ")], '%Y/%m/%d')

            if date_time_today > date_check_out:
                # notifying client
                socketobj.send(pickle.dumps(["#TIME IS UP FOR PURCHASE#", dates]))

    def _check_date_by_login(self, socketobj, email):
        """
        function checks for the ending for purchase, and notifying client when he logs in (offline)
        :param socketobj: client socket
        :param email: client email
        :return: None
        """

        # client purchase data
        purchase_data = fetch_row_by_parameter("purchases", "user_email", email)

        if purchase_data != []:

            dates = purchase_data[0][2]

            # getting dates
            check_in, check_out = dates.split("-")[0][:-1], dates.split("-")[1][1:]
            date_check_in, date_check_out = datetime.strptime(check_in, '%Y/%m/%d'), datetime.strptime(check_out,
                                                                                                       '%Y/%m/%d')

            # checking if date has passed
            time_today = str(self._server_time).replace("-", "/")
            if time_today.find(":") != -1:
                date_time_today = datetime.strptime(time_today[:time_today.find(" ")], '%Y/%m/%d')
            else:
                date_time_today = datetime.strptime(time_today, '%Y/%m/%d')

            # if so, notifying client to rate purchase
            if date_time_today > date_check_out:
                socketobj.send(pickle.dumps(["#TIME IS UP FOR PURCHASE#", dates]))
                self._client_notifications[socketobj] = 1

    def run(self):
        """
        function runs the server
        :return: None
        """

        while 1:

            # getting readable sockets, writable socket
            self.readables, self.writeables, exceptions = select(self.read_sockets, self.write_sockets, [], 0)

            # iterating over readable sockets
            for sock in self.readables:
                if sock in self.main_socks:

                    # accepting new clients to the server
                    newsock, address = sock.accept()
                    newsock.send(pickle.dumps(self.offers))
                    self.read_sockets.append(newsock)
                    self.write_sockets.append(newsock)

                    # sending updated offers to every new client
                    if self.positions_available is not None:
                        newsock.send(pickle.dumps(["#UPDATED OFFERS#", self.positions_available]))

                    # sending to a new client all the images required for the map
                    filenames = next(walk(PATH + r"\map_images"), (None, None, []))[2]  # [] if no file
                    for filename in filenames:
                        with open(PATH + f"\map_images\\{filename}", "rb") as f:
                            newsock.send(f"NAME {filename}".encode())
                            newsock.send(f.read())
                else:

                    try:

                        # accepting new image
                        while self.start_image:
                            d = sock.recv(self._BUFFER)
                            self.image += d
                            if len(d) < 1024:

                                self._client_image[sock] = self.image

                                # sending the image to all clients
                                for image in self._client_image.values():
                                    self._broadcast_bites(sock, image)

                                self.start_image = False
                                break

                        # receiving data from user
                        data = sock.recv(self._BUFFER)

                        if self.run_once == 0:
                            self._client_time[sock] = self._server_time
                            self._client_notifications[sock] = 0
                            self.run_once = 1

                        try:

                            # getting the name of the image
                            if data.decode().startswith("NAME"):
                                self.image = b""
                                self.image_name = data.decode().split(" ")[1]
                                self.start_image = True

                        except UnicodeDecodeError:
                            pass

                        # new data from the client
                        pickled_data = pickle.loads(data)

                        # if client sent updated offers
                        if type(pickled_data) == dict:
                            self.positions_available = pickled_data
                            self._broadcast(sock, ["#UPDATED OFFERS#", self.positions_available], True)
                            continue

                        # checking if user exists
                        if pickled_data[0] == "#CHECK FOR USER#":

                            if check_if_user_exists(pickled_data[1]):
                                sock.send("#USER ALREADY EXISTS#".encode())
                                continue
                            else:
                                sock.send("#USER DOESN'T EXISTS#".encode())
                                continue

                        # updating database
                        elif pickled_data[0].startswith("#UPDATE DATA BASE#"):

                            data_base_name = pickled_data[0].split(" ")[3]

                            if data_base_name == "record":
                                insert_to_record(pickled_data[1])

                            # if user has sent a new offer
                            # updating data base and sending offer to all clients connected
                            elif data_base_name == "offers":
                                insert_to_offers(pickled_data[1])
                                self.offers = get_database("offers")
                                self._broadcast_to_all(self.offers, True)

                            elif data_base_name == "purchases":
                                insert_to_purchases(pickled_data[1])

                            elif data_base_name == "ratings":
                                try:
                                    insert_to_rating(pickled_data[1])
                                except sqlite3.IntegrityError:
                                    sock.send("#AlREADY RATED#".encode())
                                    continue

                            continue

                        # deleting a row from data base
                        elif pickled_data[0].startswith("#DELETE FROM DATA BASE#"):

                            data_base_name = pickled_data[0].split(" ")[4]

                            if data_base_name == "purchases":
                                remove_row_by_parameter("purchases", "purchase_id", pickled_data[1])

                                if check_if_exists("ratings", "purchase_id", pickled_data[1]):
                                    remove_row_by_parameter("purchases", "purchase_id", pickled_data[1])

                            # if user has disputed offer
                            # removing from database and sending message to all the clients connected
                            elif data_base_name == "offers":
                                remove_row_by_parameter("offers", "offer_id", pickled_data[1])
                                self.offers = get_database("offers")
                                self._broadcast_to_all(["#DELETE MARKER#", self.offers], True)

                            continue

                        # sending user id by email
                        elif pickled_data[0].startswith("#FETCH USER ID#"):
                            print(fetch_row_by_parameter("record", "email", pickled_data[1])[0][0])
                            sock.send(pickle.dumps(
                                ["#RECORD ANSWER#", fetch_row_by_parameter("record", "email", pickled_data[1])[0][0]]))
                            continue

                        # if a purchase id was sent
                        elif pickled_data[0].startswith("#PURCHASE ID#"):
                            self._client_purchase[sock] = pickled_data[1]
                            continue

                        # checking for dates according to server_time
                        elif pickled_data[0].startswith("#CHECK FOR DATE#"):
                            self._check_date_by_login(sock, pickled_data[1])
                            self._client_email[sock] = pickled_data[1]

                        # sending purchase by email
                        elif pickled_data[0].startswith("#GET PURCHASES#"):
                            sock.send(pickle.dumps(["#LOGGED PURCHASES#",
                                                    fetch_row_by_parameter("purchases", "user_email",
                                                                           pickled_data[1])]))
                            continue

                        # sending location by room name
                        elif pickled_data[0].startswith("#GET LOCATION BY ROOM NAMES#"):
                            sock.send(pickle.dumps(["#LOCATION BY ROOM NAMES#",
                                                    fetch_row_by_parameter("offers", "room_name", pickled_data[1])[0][
                                                        8]]))
                            continue

                        # sending data on offer
                        elif pickled_data[0].startswith("#GET INFORMATION ON OFFER#"):
                            sock.send(pickle.dumps(["#INFORMATION ON OFFER#", fetch_by_location("offers", str(
                                pickled_data[1]) + ", " + str(pickled_data[2]))[0]]))
                            continue

                        # inserting a new purchase
                        elif pickled_data[0].startswith("#INSERT TO PURCHASES#"):
                            insert_to_purchases(pickled_data[1])
                            continue

                        # sending offer by purchase id
                        elif pickled_data[0].startswith("#GET OFFER BY PURCHASE ID#"):
                            sock.send(pickle.dumps(["#OFFER BY PURCHASE ID#",
                                                    fetch_row_by_parameter("purchases", "purchase_id", pickled_data[1])[
                                                        0]]))
                            continue

                        # sending purchase by offer id
                        elif pickled_data[0].startswith("#GET PURCHASE BY OFFER ID#"):
                            sock.send(pickle.dumps(["#PURCHASE BY OFFER ID#",
                                                    fetch_row_by_parameter("purchases", "offer_id", pickled_data[1])]))
                            continue

                        # if a new client logged in
                        elif pickled_data[0].startswith("#LOGGED IN#"):
                            self._logged_client[sock] = pickled_data[1]
                            continue

                        # sending room name by offer id
                        elif pickled_data[0].startswith("#GET ROOM NAME BY OFFER ID#"):
                            sock.send(pickle.dumps(["#ROOM NAME BY OFFER ID#",
                                                    fetch_row_by_parameter("offers", "offer_id", pickled_data[1])[0][
                                                        7]]))
                            continue

                        # sending rating by offer id
                        elif pickled_data[0].startswith("#GET RATING BY OFFER ID#"):
                            sock.send(pickle.dumps(
                                ["#RATING BY OFFER ID#", self._get_avarage_rating_for_room(pickled_data[1])]))
                            continue

                        # sending admin answer for admin login request
                        elif pickled_data[0].startswith("#ADMIN REQUEST#"):
                            sock.send(pickle.dumps(["#ADMIN ANSWER#", check_if_admin(pickled_data[1])]))
                            continue

                        # sending message to add a new marker for a new position
                        elif pickled_data[0].startswith("#ADD NEW POSITION#"):
                            self._broadcast_to_all(["#NEW MARKER#", pickled_data[1], pickled_data[2], pickled_data[3]],
                                                   True)

                        # sending admin query for record
                        elif pickled_data[0].startswith("#GET ADMIN QUERY FOR RECORD#"):
                            sock.send(pickle.dumps(["#ADMIN QUERY FOR RECORD#", search("record",
                                                                                       ["user_id", "email", "name",
                                                                                        "country", "password",
                                                                                        "is_admin"],
                                                                                       pickled_data[1])]))
                            continue

                        # sending admin query for purchase
                        elif pickled_data[0].startswith("#GET ADMIN QUERY FOR PURCHASE#"):
                            sock.send(pickle.dumps(["#ADMIN QUERY FOR PURCHASE#", search("purchases",
                                                                                         ["purchase_id", "offer_id",
                                                                                          "duration", "user_email",
                                                                                          "credit_number",
                                                                                          "is_registered"],
                                                                                         pickled_data[1])]))
                            continue

                        # sending admin query for searching within rating table
                        elif pickled_data[0].startswith("#GET ADMIN QUERY FOR RATING#"):
                            sock.send(pickle.dumps(["#ADMIN QUERY FOR RATING#", search("ratings",
                                                                                       ["purchase_id", "offer_id",
                                                                                        "user_email",
                                                                                        "scale_rating",
                                                                                        "review",
                                                                                        "is_anonymous"],
                                                                                       pickled_data[1])]))
                            continue

                        # sending name by email
                        elif pickled_data[0].startswith("#FETCH NAME BY EMAIL#"):
                            sock.send(pickle.dumps(
                                ["#NAME BY EMAIL#", fetch_row_by_parameter("record", "email", pickled_data[1])[0][2]]))
                            continue

                        # sending offer by email
                        elif pickled_data[0].startswith("#GET OFFER BY EMAIL#"):
                            user_id = fetch_row_by_parameter("record", "email", pickled_data[1])[0][0]
                            sock.send(pickle.dumps(
                                ["#OFFER BY EMAIL#", fetch_row_by_parameter("offers", "user_id", user_id)]))
                            continue

                        # sending review by offer id
                        elif pickled_data[0].startswith("#GET REVIEW BY OFFER ID#"):
                            sock.send(pickle.dumps(["#REVIEW BY OFFER ID#",
                                                    fetch_row_by_parameter("ratings", "offer_id", pickled_data[1])]))
                            continue

                        # if new attraction was uploaded
                        elif pickled_data[0].startswith("#NEW ATTRACTION#"):
                            self._broadcast_to_all(["#NEW ATTRACTION#", pickled_data[1]], True)

                        # changing credentials for user
                        elif pickled_data[0].startswith("#CHANGE CREDENTIALS#"):
                            change = pickled_data[0].split(" ")[2]
                            if change == "name":
                                update("record", "name", pickled_data[1], "password", pickled_data[2])
                                continue

                            elif change == "email":
                                update("record", "email", pickled_data[1], "password", pickled_data[2])
                                continue

                            elif change == "password":
                                update("record", "password", pickled_data[1], "password", pickled_data[2])
                                continue

                        # exporting file to csv
                        elif pickled_data[0].startswith("#SAVE DATA BASE#"):

                            data_base_name = pickled_data[0].split(" ")[3]

                            if data_base_name == "record":

                                export_to_csv("record")
                                with open(PATH + "\\" + "record_table.csv", "rb") as f:
                                    bytes = f.read()

                                os.remove(PATH + "\\" + "record_table.csv")

                                sock.send(pickle.dumps(["#NEW CSV FILE#", "record_table.csv", bytes]))
                                continue

                            elif data_base_name == "offers":
                                export_to_csv("offers")
                                with open(PATH + "\\" + "offers_table.csv", "rb") as f:
                                    bytes = f.read()

                                os.remove(PATH + "\\" + "offers_table.csv")

                                sock.send(pickle.dumps(["#NEW CSV FILE#", "offers_table.csv", bytes]))
                                continue

                            elif data_base_name == "purchases":
                                export_to_csv("purchases")
                                with open(PATH + "\\" + "purchases_table.csv", "rb") as f:
                                    bytes = f.read()

                                os.remove(PATH + "\\" + "purchases_table.csv")

                                sock.send(pickle.dumps(["#NEW CSV FILE#", "purchases_table.csv", bytes]))
                                continue

                            elif data_base_name == "ratings":
                                export_to_csv("ratings")
                                with open(PATH + "\\" + "ratings_table.csv", "rb") as f:
                                    bytes = f.read()

                                os.remove(PATH + "\\" + "ratings_table.csv")

                                sock.send(pickle.dumps(["#NEW CSV FILE#", "ratings_table.csv", bytes]))
                                continue

                        # making user admin
                        elif pickled_data[0].startswith("#MAKE USER ADMIN BY EMAIL#"):
                            client = [s for s, email in self._client_email.items() if email == pickled_data[1]][0]
                            update("record", "is_admin", True, "email", pickled_data[1])
                            client.send("#BECOME ADMIN#".encode())

                    except (pickle.UnpicklingError, MemoryError):

                        data = data.decode()

                        # if admin is changing the date, change the server_time and notify users
                        if data.find("/") != -1 and len(data) < 14 and data.count("/") == 2:
                            self._server_time = data
                            self._check_client_status()
                            self._broadcast_to_all(self._server_time, False)

                        # if user is trying to login
                        if data == "#LOGIN REQUEST#":

                            try:
                                users = []
                                passwords = []
                                con = sqlite3.connect('data_base/user_data.db')
                                c = con.cursor()
                                for row in c.execute("Select * from record"):
                                    username = row[1]
                                    pwd = row[4]
                                    users.append(username)
                                    passwords.append(pwd)

                                sock.send(pickle.dumps(["#LOGIN ANSWER#", users, passwords]))

                            except Exception as ep:
                                messagebox.showerror('', ep)

                            continue

                        # sending all the room names
                        elif data == "#GET ROOM NAMES#":
                            sock.send(pickle.dumps(["#ROOM NAMES#", fetch_by_parameter("offers", "room_name")]))
                            continue

                        # sending offers ordered by price
                        elif data == "#ORDER OFFERS BY PRICE#":
                            sock.send(pickle.dumps(["#OFFERS ORDERED BY PRICE#",
                                                    order_by_parameter("offers", ["room_name"], "price_per_day")]))
                            continue

                        # sending all the records to admin
                        elif data == "#GET ADMIN RECORDS#":
                            sock.send(pickle.dumps(["#ADMIN RECORDS#", get_database("record")]))
                            continue

                        # sending all offers to admin
                        elif data == "#GET ADMIN OFFERS#":
                            sock.send(pickle.dumps(["#ADMIN OFFERS#", get_database("offers")]))
                            continue

                        # sending all purchases to admin
                        elif data == "#GET ADMIN PURCHASES#":
                            sock.send(pickle.dumps(["#ADMIN PURCHASES#", get_database("purchases")]))
                            continue

                        # sending all ratings to admin
                        elif data == "#GET ADMIN RATINGS#":
                            sock.send(pickle.dumps(["#ADMIN RATINGS#", get_database("ratings")]))
                            continue

                        # sending order offers by the average rating
                        elif data == "#ORDER OFFERS BY AVERAGE RATING#":
                            sock.send(pickle.dumps(["#OFFERS ORDERED BY AVERAGE RATING#",
                                                    order_by_parameter("ratings", ["offer_id", "scale_rating"],
                                                                       "scale_rating")]))
                            continue

                    except (ConnectionError, ssl.SSLEOFError, EOFError):

                        # if client has left
                        print(f"----CLIENT  {sock.getpeername()}  LEFT----")
                        self._remove_from_lists(sock)
                        continue

            # checking client status according to server_time variable
            self._check_client_status()

    def _check_client_status(self):
        """
        function checks if one of the client purchases has reached it's deadline
        according to the server's time
        :return: None
        """

        for write_to in self.write_sockets:

            if write_to in self._client_notifications.keys() and write_to in self._client_email.keys():

                if self._client_notifications[write_to] == 0:
                    self._check_date_by_login(write_to, self._client_email[write_to])


if __name__ == "__main__":

    # starting server
    print("----SERVER STARTING----")
    s = Server()
    s.run()
    s.server.close()
    print('DONE, LISTENING')
