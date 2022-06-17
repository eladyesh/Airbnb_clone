import pickle
from socket import *
from threading import Thread
from tkinter import *
from tkinter import filedialog
from tkinter.filedialog import askopenfilenames, askopenfilename, askopenfile
from tkinter.scrolledtext import ScrolledText
import geocoder
from tkcalendar import *
import tkinter.font as tkFont
import ssl
import warnings
from maps.map import App
from PIL import ImageTk
from PIL import Image
from datetime import datetime
import random as rand
from data_base.manage_data_base import *
import re
import os.path
from tkinter import ttk
import maps.map as map
from customtkinter import *
from client import Client
import json
from tkvideo import tkvideo

f = ('Open Sans', 16)
PATH = os.path.dirname(os.path.realpath(__file__))


class Admin:
    """
    Admin class extends the regular user class and adds features of it's own such as
    admin reports, a unique admin map and attractions loading
    """

    def __init__(self):

        # ignoring deprecation warning
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # starting socket, wrapping with ssl
        self.client = ssl.wrap_socket(socket(AF_INET, SOCK_STREAM), server_side=False)
        if len(gethostbyname_ex(gethostname())[-1]) > 1:
            self.__HOST = gethostbyname_ex(gethostname())[-1][0]
        else:
            self.__HOST = gethostbyname_ex(gethostname())[-1][-1]
        self.__HOST = "172.16.2.74"
        self._BUFFER = 1024
        self._ADDR = (self.__HOST, 50002)

        # initiating important variables to avoid errors
        self.event_handler = Event()
        self.__logged_in = False
        self.map = None
        self.filename = None
        self._save_image = b""
        self.start_image = False
        self.ratings = dict({})
        self.map_data = [None for i in range(10)]
        self.is_admin = False
        self.already_offered, self.already_registered = 0, 0
        self.user_data = [None for i in range(
            10)]  # [self.login_users, self.login_passwords, self.user_id, self.login_purchases, self.user_exists, self.user_data]
        self.room_data = [None for i in range(5)]  # [room name by offer_id, room average rating]
        self.admin_data = [None for i in range(
            8)]  # [is_admin, self.records, self.offers, self.purchases, search_by_query (record), self.name, self.search_by_query (purchase)# ,
        # self.ratings# , self.query_for_rating]
        self.root = None
        self.updated_offers = None
        self.attractions = []
        self.admin_map = None
        self.disputed_id = []

        # initiating the server time
        self.server_time = self.server_time = datetime.now().strftime("%Y/%m/%d")

    def make_directory_for_map(self, path):
        """
        function makes the directory in the running directory for the map_images
        :param path:
        :return: None
        """

        # if directory already exists, saving in there the images for the map
        if os.path.isdir(path):
            with open(path + "\\" + self.image_save, "wb") as f:
                f.write(self._save_image)

        else:

            # making directory called "map_images"
            # directory will save the images for the map
            parent_dir = PATH
            directory = "map_images"
            path = os.path.join(parent_dir, directory)

            if not os.path.exists(path):
                os.mkdir(path)

                with open(path + "\\" + self.image_save, "wb") as f:
                    f.write(self._save_image)

    def recieve(self):
        """
        Function receives input from server and handles it
        """

        while 1:

            try:

                # expecting image
                while self.start_image:

                    d = self.client.recv(self._BUFFER)
                    self._save_image += d
                    if len(d) < self._BUFFER:
                        self.start_image = False

                        # saving in directory for map_images
                        self.make_directory_for_map(PATH + r"\map_images")

                        self._save_image = b""
                        break

                # receiving data from the server
                data = self.client.recv(self._BUFFER)

                try:

                    # name of the image
                    if data.decode().startswith("NAME"):
                        self.image_save = data.decode().split(" ")[1][data.decode().split(" ")[1].rfind("/") + 1:]
                        self.start_image = True

                except UnicodeDecodeError:
                    pass

                # pickling the data
                pickle_data = pickle.loads(data)

                # if the data received is type dictionary
                if type(pickle_data) == dict:

                    self.offers = pickle.loads(data)

                    if self.map is not None:

                        # updating markers
                        self.updated_offers = pickle_data
                        self.map.update_markers(self.updated_offers)

                # if the data received is type list
                elif type(pickle_data) == list:

                    # handling data received from server
                    # if user tries to log in
                    if pickle_data[0] == "#LOGIN ANSWER#":
                        self.user_data[0] = pickle_data[1]
                        self.user_data[1] = pickle_data[2]

                    # if needed to update the current offers
                    elif pickle_data[0] == "#UPDATED OFFERS#":
                        self.updated_offers = pickle_data[1]

                        if self.map is not None:

                            # updating markers on the map
                            self.map.update_markers(self.updated_offers)

                        continue

                    # if record answer was sent
                    elif pickle_data[0] == "#RECORD ANSWER#":
                        self.user_data[2] = pickle_data[1]

                    # if logged purchases was sent
                    elif pickle_data[0] == "#LOGGED PURCHASES#":
                        self.user_data[3] = pickle_data[1]

                    # if room names were sent
                    elif pickle_data[0] == "#ROOM NAMES#":
                        self.map_data[0] = pickle_data[1]
                        continue

                    # if offers ordered by the price was sent
                    elif pickle_data[0] == "#OFFERS ORDERED BY PRICE#":
                        self.map_data[1] = pickle_data[1]

                    # if a location by room name was sent
                    elif pickle_data[0] == "#LOCATION BY ROOM NAMES#":
                        self.map_data[2] = pickle_data[1]

                    # if data on offer was sent
                    elif pickle_data[0] == "#INFORMATION ON OFFER#":
                        self.map_data[3] = pickle_data[1]

                    # if offer by purchase id was sent
                    elif pickle_data[0] == "#OFFER BY PURCHASE ID#":
                        self.map_data[4] = pickle_data[1]

                    # if purchase by offer id was sent
                    elif pickle_data[0] == "#PURCHASE BY OFFER ID#":
                        self.map_data[5] = pickle_data[1]

                    # if offers that are ordered by their rating were sent
                    elif pickle_data[0] == "#OFFERS ORDERED BY AVERAGE RATING#":
                        self.map_data[6] = pickle_data[1]

                    # if room name by offer id was sent
                    elif pickle_data[0] == "#ROOM NAME BY OFFER ID#":
                        self.room_data[0] = pickle_data[1]

                    # if rating by offer id was sent
                    elif pickle_data[0] == "#RATING BY OFFER ID#":
                        self.room_data[1] = pickle_data[1]

                    # if review by offer id was sent
                    elif pickle_data[0] == "#REVIEW BY OFFER ID#":
                        self.room_data[2] = pickle_data[1]

                    # if user is admin
                    elif pickle_data[0] == "#ADMIN ANSWER#":
                        self.admin_data[0] = pickle_data[1]

                    # if the 'records' table was sent
                    elif pickle_data[0] == "#ADMIN RECORDS#":
                        self.admin_data[1] = pickle_data[1]

                    # if the 'offers' table was sent
                    elif pickle_data[0] == "#ADMIN OFFERS#":
                        self.admin_data[2] = pickle_data[1]

                    # if 'purchases' table was sent
                    elif pickle_data[0] == "#ADMIN PURCHASES#":
                        self.admin_data[3] = pickle_data[1]

                    # if an admin query for a record was sent
                    elif pickle_data[0] == "#ADMIN QUERY FOR RECORD#":
                        self.admin_data[4] = pickle_data[1]

                    # if 'ratings' table was sent
                    elif pickle_data[0] == "#ADMIN RATINGS#":
                        self.admin_data[6] = pickle_data[1]

                    # if a new offer was sent, and needed to add a marker
                    elif pickle_data[0] == "#NEW MARKER#" and self.map is not None:
                        self.map.add_marker(pickle_data[1], pickle_data[2], pickle_data[3])

                        if self.admin_map is not None:
                            self.admin_map.add_marker(pickle_data[1], pickle_data[2], pickle_data[3])
                        continue

                    # if a name by email was sent
                    elif pickle_data[0] == "#NAME BY EMAIL#":
                        self.user_data[5] = pickle_data[1]

                    # if an admin query for purchase was sent
                    elif pickle_data[0] == "#ADMIN QUERY FOR PURCHASE#":
                        self.admin_data[5] = pickle_data[1]

                    # if an admin query for rating was sent
                    elif pickle_data[0] == "#ADMIN QUERY FOR RATING#":
                        self.admin_data[7] = pickle_data[1]

                    # if offer by email was sent
                    elif pickle_data[0] == "#OFFER BY EMAIL#":
                        self.user_data[6] = pickle_data[1]

                    # if time is up for a certain purchase
                    elif pickle_data[0] == "#TIME IS UP FOR PURCHASE#":
                        messagebox.showinfo("info", f"Your purchase duration was up for dates\n"
                                                    f"{pickle_data[1]}\nPlease rate")

                    # if a review was sent by offer id
                    elif pickle_data[0] == "#REVIEW BY OFFER ID#":
                        self.room_data[2] = pickle_data[1]

                    # if a new attraction was sent
                    elif pickle_data[0] == "#NEW ATTRACTION#":

                        # adding to regular map and to admin map
                        if self.map is not None:
                            self.map.add_attraction(*pickle_data[1])

                        if self.admin_map is not None:
                            self.admin_map.add_attraction(*pickle_data[1])
                        else:
                            self.attractions.append(pickle_data[1])

                    # if user has disputed offer
                    elif pickle_data[0] == "#DELETE MARKER#":

                        # getting the data on the marker
                        location = list(set(self.offers.items()) - set(pickle_data[1].items()))[0][1][7]
                        room_name = list(set(self.offers.items()) - set(pickle_data[1].items()))[0][1][6]
                        key = list(set(self.offers.items()) - set(pickle_data[1].items()))[0][0]
                        self.offers.pop(key)

                        if self.map is not None:

                            # deleting marker from the map
                            self.map.delete_marker(location, room_name, key)
                            self.disputed_id.append(key)

                        continue

                    # if admin has requested to make a certain table in the data base a .csv file
                    elif pickle_data[0] == "#NEW CSV FILE#":

                        with open(PATH + "\\" + pickle_data[1], "wb") as f:
                            f.write(pickle_data[2])

                        messagebox.showinfo("Success", f"Data Base {pickle_data[1]} was saved in a csv file",
                                            icon="info")
                        continue

            except pickle.UnpicklingError:

                # handling data that doesn't need to be pickled
                try:
                    data = data.decode()
                except UnicodeDecodeError:
                    pass

                if data == "":
                    pass

                # if user already exists
                if data == "#USER ALREADY EXISTS#":
                    self.user_data[4] = True

                # if user doesn't exist
                elif data == "#USER DOESN'T EXISTS#":
                    self.user_data[4] = False

                # if user has already rated
                elif data == "#AlREADY RATED#":
                    messagebox.showerror("Error", "You have already rated")

            except (EOFError, OSError, ssl.SSLEOFError):

                # if there is any connections problems with the server, making user exit
                self.user_quit()
                break

    def change_name(self):
        """
        function shows form for changing name for the user
        :return: None
        """

        # clearing screen
        Client.clear_screen(self.root, self.menubar, self.on_closing)

        # creating frame for form and images
        bigger_frame = Frame(self.root, width=700, height=700, bg="white")

        # setting images and widgets
        CTkLabel(bigger_frame, text="Change Name", text_font=("Roboto Medium", -40), bg="white").pack(pady=30)
        img = ImageTk.PhotoImage(Image.open("airbnb_images//airbnb_sign_up2.png").resize((350, 290)))
        login_lable = Label(bigger_frame, image=img, borderwidth=0, bg='white')
        login_lable.image = img
        login_lable.pack(side="left", expand=1, fill=BOTH, padx=20)

        # widgets of the form
        change_frame = Frame(bigger_frame, bd=2, bg="#F5F5F5", relief=SOLID, padx=10, pady=10, height=300)
        CTkLabel(change_frame, text="Enter New Name", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=0,
                                                                                                           column=0,
                                                                                                           sticky=W,
                                                                                                           pady=10)
        CTkLabel(change_frame, text="Enter Password", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=1,
                                                                                                           column=0,
                                                                                                           pady=10)

        # creating change entries
        self.name_tf = CTkEntry(change_frame, width=200, placeholder_text="Enter New Name")
        self.pwd_tf = CTkEntry(change_frame, show='*', width=200, placeholder_text="Enter Password")
        self.change_btn = CTkButton(change_frame, width=200, text='Submit', relief=SOLID, cursor='hand2',
                                    fg_color="#E0E0E0", hover_color="#33A8FF", border_width=3,
                                    text_font=("Roboto Medium", -18),
                                    command=lambda: self.send_to_server_change("name"))

        # widgets placement
        self.name_tf.grid(row=0, column=1, pady=10, padx=20)
        self.pwd_tf.grid(row=1, column=1, pady=10, padx=20)
        self.change_btn.grid(row=4, pady=(20, 20), column=1)

        change_frame.pack(side="left", pady=70)
        bigger_frame.pack(padx=50, pady=50)

    def send_to_server_change(self, credential):
        """
        function sends to server what to credential to change and that data on the user
        :param credential: the credential to change
        :return: None
        """
        if credential == "name":

            # make sure entries are not empty
            if self.name_tf.get() == "":
                messagebox.showwarning("Warning", "Your new name can't be empty", icon="warning")
                return

            elif self.pwd_tf.get() == "":
                messagebox.showwarning("Warning", "Your password can't be empty", icon="warning")
                return

            # sending to server to change credentials
            self.client.send(pickle.dumps(["#CHANGE CREDENTIALS# name", self.name_tf.get(), self.pwd_tf.get()]))
            messagebox.showinfo("Success", f"Name has changed to {self.name_tf.get()}")
            self.user_data[5] = self.name_tf.get()

            # clean entries
            self.name_tf.delete(0, END)
            self.pwd_tf.delete(0, END)

        # process repeats for email, and password changing
        elif credential == "email":

            if self.email_tf.get() == "":
                messagebox.showwarning("Warning", "Your new email can't be empty", icon="warning")
                return

            elif self.pwd_tf.get() == "":
                messagebox.showwarning("Warning", "Your password can't be empty", icon="warning")
                return

            self.client.send(pickle.dumps(["#CHANGE CREDENTIALS# email", self.email_tf.get(), self.pwd_tf.get()]))
            messagebox.showinfo("Success", f"Email has changed to {self.email_tf.get()}")
            self.uemail = self.email_tf.get()
            self.email_tf.delete(0, END)
            self.pwd_tf.delete(0, END)

        elif credential == "password":

            if self.pwd_tf.get() == "":
                messagebox.showwarning("Warning", "Your password cannot be empty", icon="warning")
                return

            elif self.new_pwd_tf.get() == "":
                messagebox.showwarning("Warning", "Your new password can't be empty", icon="warning")
                return

            elif self.new_pwd_again_tf.get() == "":
                messagebox.showwarning("Warning", "Your re-entering password cannot be empty", icon="warning")
                return

            if self.new_pwd_tf.get() != self.new_pwd_again_tf.get():
                messagebox.showwarning("Warning", "New Password and Re-Enter New Password must match!", icon="warning")
                return

            self.client.send(pickle.dumps(["#CHANGE CREDENTIALS# password", self.new_pwd_tf.get(), self.pwd_tf.get()]))
            messagebox.showinfo("Success", f"Password has changed to {self.new_pwd_tf.get()}")
            self.pwd_tf.delete(0, END)
            self.new_pwd_tf.delete(0, END)
            self.new_pwd_again_tf.delete(0, END)

    def change_password(self):
        """
        function shows form for change password
        :return: None
        """

        # clearing screen
        Client.clear_screen(self.root, self.menubar, self.on_closing)
        bigger_frame = Frame(self.root, width=700, height=700, bg="white")

        # setting images and widgets
        CTkLabel(bigger_frame, text="Change Name", text_font=("Roboto Medium", -40), bg="white").pack(pady=30)
        img = ImageTk.PhotoImage(Image.open("airbnb_images//airbnb_sign_up2.png").resize((350, 290)))
        login_lable = Label(bigger_frame, image=img, borderwidth=0, bg='white')
        login_lable.image = img
        login_lable.pack(side="left", expand=1, fill=BOTH, padx=20)

        # creating widgets for form
        change_frame = Frame(bigger_frame, bd=2, bg="#F5F5F5", relief=SOLID, padx=10, pady=10, height=300)
        CTkLabel(change_frame, text="Enter Password", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=0,
                                                                                                           column=0,
                                                                                                           sticky=W,
                                                                                                           pady=10)
        CTkLabel(change_frame, text="Enter New Password", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=1,
                                                                                                               column=0,
                                                                                                               pady=10,
                                                                                                               sticky=W)
        CTkLabel(change_frame, text="Re-Enter New Password", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=2,
                                                                                                                  column=0,
                                                                                                                  pady=10,
                                                                                                                  sticky=W)

        # creating change entries
        self.pwd_tf = CTkEntry(change_frame, width=200, placeholder_text="Enter Password")
        self.new_pwd_tf = CTkEntry(change_frame, show='*', width=200, placeholder_text="Enter New Password")
        self.new_pwd_again_tf = CTkEntry(change_frame, show='*', width=200, placeholder_text="Re-Enter Password")
        self.change_btn = CTkButton(change_frame, width=200, text='Submit', relief=SOLID, cursor='hand2',
                                    fg_color="#E0E0E0", hover_color="#33A8FF", border_width=3,
                                    text_font=("Roboto Medium", -18),
                                    command=lambda: self.send_to_server_change("password"))

        # widgets placement
        self.pwd_tf.grid(row=0, column=1, pady=10, padx=20)
        self.new_pwd_tf.grid(row=1, column=1, pady=10, padx=20)
        self.new_pwd_again_tf.grid(row=2, column=1, pady=10, padx=20)
        self.change_btn.grid(row=4, pady=(20, 20), column=1)

        change_frame.pack(side="left", pady=70)
        bigger_frame.pack(padx=50, pady=50)

    def change_email(self):
        """
        function shows form for change password
        :return: None
        """

        # clearing screen
        Client.clear_screen(self.root, self.menubar, self.on_closing)

        # creating frame for the widgets
        bigger_frame = Frame(self.root, width=700, height=700, bg="white")

        # setting images and widgets
        CTkLabel(bigger_frame, text="Change Email", text_font=("Roboto Medium", -40), bg="white").pack(pady=30)
        img = ImageTk.PhotoImage(Image.open("airbnb_images//airbnb_sign_up2.png").resize((350, 290)))
        login_lable = Label(bigger_frame, image=img, borderwidth=0, bg='white')
        login_lable.image = img
        login_lable.pack(side="left", expand=1, fill=BOTH, padx=20)

        # creating widgets for the form
        change_frame = Frame(bigger_frame, bd=2, bg="#F5F5F5", relief=SOLID, padx=10, pady=10, height=300)
        CTkLabel(change_frame, text="Enter New Email", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=0,
                                                                                                            column=0,
                                                                                                            sticky=W,
                                                                                                            pady=10)
        CTkLabel(change_frame, text="Enter Password", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=1,
                                                                                                           column=0,
                                                                                                           pady=10)

        # creating change entries
        self.email_tf = CTkEntry(change_frame, width=200, placeholder_text="Enter New Email")
        self.pwd_tf = CTkEntry(change_frame, show='*', width=200, placeholder_text="Enter Password")
        self.change_btn = CTkButton(change_frame, width=200, text='Submit', relief=SOLID, cursor='hand2',
                                    fg_color="#E0E0E0", hover_color="#33A8FF", border_width=3,
                                    text_font=("Roboto Medium", -18),
                                    command=lambda: self.send_to_server_change("email"))

        # widgets placement
        self.email_tf.grid(row=0, column=1, pady=10, padx=20)
        self.pwd_tf.grid(row=1, column=1, pady=10, padx=20)
        self.change_btn.grid(row=4, pady=(20, 20), column=1)

        change_frame.pack(side="left", pady=70)
        bigger_frame.pack(padx=50, pady=50)

    def log_out(self):
        """
        function logs out of the system
        :return: None
        """

        if self.__logged_in:
            self.__logged_in = False
            messagebox.showinfo("info", "You have logged out\n"
                                        "Since this is admin we will close the window for you\n"
                                        "If you wish to enter again, you must reopen the window\n"
                                        "Thank you")
            self.on_closing(True)
        else:

            # handling errors
            messagebox.showerror("Error", "You are not logged in")

    def change_date_for_admin(self):
        """
        function shows form and changes the date of the system (for admin only)
        :return: None
        """

        # starting the root
        date_root = Toplevel(self.root)
        date_root.resizable(False, False)

        var = DoubleVar()

        # creating root, and calendar for changing the date
        CTkLabel(date_root, text=f"Please the current date you want to change to", bg='#04AA6D',
                 text_font=("Roboto Medium", -20)).pack(pady=5)

        # creating entry for change of date
        self.date_change = DateEntry(date_root, font=f, locale='en_US', date_pattern='dd/mm/yyyy',
                                     mindate=datetime.now())
        self.date_change.pack(pady=10)

        # submit button, sending to server the new date
        CTkButton(date_root, fg_color="#E0E0E0", hover_color="#33A8FF",
                  border_width=3, text_font=("Roboto Medium", -18), relief=SOLID, cursor='hand2', text="Submit",
                  command=lambda: [self.client.send(str(self.date_change.get_date()).replace("-", "/").encode()),
                                   messagebox.showinfo("Success", "Date Changed\n"),
                                   date_root.destroy()]).pack(pady=10)

    def convert_address_to_location(self):
        """
        function converts address to location for the user to enter when
        he/she offers a room
        :return: None
        """

        # creating root
        self.location_root = Toplevel(self.root)
        self.location_root.resizable(False, False)
        frame = Frame(self.location_root)

        # creating label
        CTkLabel(self.location_root, text=f"Please enter an address\n\n", bg='#F5F5F5',
                 text_font=("Roboto Medium", -30)).pack(pady=10)

        # creating the entry for
        self.loc = CTkEntry(frame, width=200, placeholder_text="Enter Address")
        self.loc.pack(side="left", padx=5)

        # submit button
        self.w = CTkButton(frame, fg_color="#E0E0E0", hover_color="#33A8FF",
                           border_width=3, text_font=("Roboto Medium", -18), relief=SOLID, cursor='hand2',
                           text="Submit",
                           command=lambda: self.calculate_address(self.loc.get()))
        self.w.pack(side="left", padx=5)

        # widget placements
        frame.pack(pady=5)
        self.lbl = CTkLabel(self.location_root, text="",
                            text_font=("Roboto Medium", -15))
        self.lbl.pack(pady=3)

    def calculate_address(self, address_string):
        """
        function calculates geocode of an address
        :param address_string: the address
        :return: geocode of an address
        """
        x, y = geocoder.osm(address_string).latlng
        self.lbl.config(text="Your location is \n\n"
                             f"'{x, y}'", bg='#F5F5F5')

    def on_closing(self, admin_log_out=None, close_immediately=None):
        """
        function makes sure closing tkinter root goes without errors, closes root and client socket
        admin_log_out: if admin is logging out
        :return: None
        """

        if close_immediately is not None:
            self.root.destroy()
            self.client.close()
            return

        if admin_log_out is not None:
            try:
                self.root.destroy()
                self.client.close()
            except:
                pass

        elif messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            try:
                self.root.destroy()
                self.client.close()
            except:
                pass

            messagebox.showinfo("Success", "Thank you for being with us", icon="info")

    def show_home_screen(self):
        """
        function shows the home screen for the client
        :return:
        """

        # clearing screen
        Client.clear_screen(self.root, self.menubar, self.on_closing)

        # showing entry for changing date to admin
        CTkButton(self.root, width=150, text='Change Date', relief=SOLID, cursor='hand2',
                  fg_color="#E0E0E0", hover_color="#33A8FF", border_width=3,
                  text_font=("Roboto Medium", -20),
                  command=lambda: self.change_date_for_admin()).pack(pady=10, anchor="n", side=TOP)

        # creating a label and an image to begin the trivia
        self.begin = Label(self.root, text="Hello There!!!\n\nWelcome to my airBnB "
                                           "", font=self.lbl_font,
                           bg='white')
        self.begin.pack(expand="Yes", fill=BOTH, anchor=CENTER)
        self.name = StringVar()

        # showing the video on the home screen
        self.video_label = CTkLabel(self.root)
        self.video_label.pack(pady=20)
        player = tkvideo("airbnb_images//airbnb_video.mp4", self.video_label,
                         loop=1, size=(700, 500))
        try:
            player.play()
        except:
            pass

        # showing name if exists
        if self.user_data[5] is not None:
            lbl = CTkLabel(self.root, text=f"Hello {self.user_data[5]}", bg="white", text_font=("Roboto Medium", -30))
            lbl.place(x=20, y=20)

    def start_admin_root(self):
        """
        function starts the admin root - showing login form
        :return:
        """

        # starting the root
        # setting attributes
        self.root = Tk()
        self.root.resizable(False, False)
        self.root.config(bg="white")
        self.root.title("AirBnB")
        self.root.minsize(1000, 800)
        x = 1000
        y = 800
        self.root.geometry(
            f"{str(x)}x{str(y)}+{int(self.root.winfo_screenwidth() / 2 - x / 2)}+{int(self.root.winfo_screenheight() / 2 - y / 2)}")
        self.root.deiconify()
        bigger_frame = Frame(self.root, width=700, height=700, bg="white")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # setting picture of the logo
        CTkLabel(bigger_frame, text="Admin Login", text_font=("Roboto Medium", -40), bg="white").pack(pady=30)
        img = ImageTk.PhotoImage(Image.open("airbnb_images//airbnb_sign_up2.png").resize((350, 290)))
        login_lable = Label(bigger_frame, image=img, borderwidth=0, bg='white')
        login_lable.image = img
        login_lable.pack(side="left", expand=1, fill=BOTH, padx=20)

        # setting labels for form
        login_frame = Frame(bigger_frame, bd=2, bg="#F5F5F5", relief=SOLID, padx=10, pady=10, height=300)
        CTkLabel(login_frame, text="Enter Email", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=0, column=0,
                                                                                                       sticky=W,
                                                                                                       pady=10)
        CTkLabel(login_frame, text="Enter Password", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=1,
                                                                                                          column=0,
                                                                                                          pady=10)

        # setting entries for form
        self.email_tf = CTkEntry(login_frame, width=200, placeholder_text="Enter Email")
        self.pwd_tf = CTkEntry(login_frame, show='*', width=200, placeholder_text="Enter Password")
        self.login_btn = CTkButton(login_frame, width=200, text='Login', relief=SOLID, cursor='hand2',
                                   fg_color="#E0E0E0", hover_color="#33A8FF", border_width=3,
                                   text_font=("Roboto Medium", -18),
                                   command=self.login_response)

        # widgets placement
        self.email_tf.grid(row=0, column=1, pady=10, padx=20)
        self.pwd_tf.grid(row=1, column=1, pady=10, padx=20)
        self.login_btn.grid(row=2, pady=(100, 20), column=1)

        login_frame.pack(side="left", pady=70)
        bigger_frame.pack(padx=50, pady=50)

        # starting the receive thread in order to get messages from the server
        self.receive_thread = Thread(target=self.recieve)
        # self.receive_thread.daemon = True
        self.receive_thread.start()

        self.root.mainloop()

    def connect(self):
        """
        function connects to the server
        :return: None
        """

        while 1:

            try:
                self.client.connect(self._ADDR)
                print("----Connected to server successfully----")
                break
            except (ConnectionRefusedError, TimeoutError):
                continue

        # starting admin root
        self.start_admin_root()

    def start_root(self):
        """
        function starts regular root for the application
        :return: None
        """

        self.root.title("AirBnB")
        self.root.minsize(1000, 800)
        x = 1000
        y = 800
        self.root.geometry(
            f"{str(x)}x{str(y)}+{int(self.root.winfo_screenwidth() / 2 - x / 2)}+{int(self.root.winfo_screenheight() / 2 - y / 2)}")
        self.root.iconphoto(False, PhotoImage(file=PATH + r"\\airbnb_images\\airbnb_sign_up2.png"))
        self.root.deiconify()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # creating the menu
        self.menubar = Menu(self.root)

        # creating submenu for disputes
        self.sub_menu = Menu(self.menubar, tearoff=0)
        self.sub_menu.add_command(label='Dispute Purchases', command=self.show_cancel_purchases)
        self.sub_menu.add_command(label='Dispute Offers', command=self.show_cancel_offers)

        # creating the file menu
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Register", command=self.show_registration)
        self.filemenu.add_command(label="Home Page", command=self.show_home_screen)
        self.filemenu.add_command(label="Sign in", command=self.show_login)
        self.filemenu.add_command(label="See offers", command=self.open_map)
        self.filemenu.add_command(label="Offer Room", command=self.offer_room)
        self.filemenu.add_command(label="Rate Purchases", command=self.show_purchases)
        self.filemenu.add_command(label="Convert Address", command=self.convert_address_to_location)

        # adding separators, adding 'exit', 'log out' commands
        self.filemenu.add_separator()
        self.filemenu.add_cascade(
            label="Dispute",
            menu=self.sub_menu
        )
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_closing)
        self.filemenu.add_command(label="Log out", command=self.log_out)
        self.menubar.add_cascade(label="User menu", menu=self.filemenu)

        # creating 'change' menu
        self.change_menu = Menu(self.menubar, tearoff=0)
        self.change_menu.add_command(label="Change Email", command=self.change_email)
        self.change_menu.add_command(label="Change Password", command=self.change_password)
        self.change_menu.add_command(label="Change Name", command=self.change_name)
        self.menubar.add_cascade(label="Change Credentials", menu=self.change_menu)

        # creating the 'admin' menu
        self.help_menu = Menu(self.menubar, tearoff=0)
        self.help_menu.add_command(label="Show Records", command=self.show_records)
        self.help_menu.add_command(label="Show Offers", command=self.show_offers)
        self.help_menu.add_command(label="Show All Purchases", command=self.show_admin_purchases)
        self.help_menu.add_command(label="Show Ratings", command=self.show_admin_ratings)
        self.help_menu.add_command(label="Upload attractions", command=self.upload_attractions)
        self.help_menu.add_command(label="Open Admin Map", command=self.open_admin_map)
        self.help_menu.add_command(label="Export Data Base To Csv", command=self.data_base_to_csv)
        self.menubar.add_cascade(label="Admin Menu", menu=self.help_menu)
        self.root.config(menu=self.menubar)

        # creating a label font
        self.lbl_font = tkFont.Font(family="Sans-serif", size=20, weight=tkFont.BOLD)

        # showing the home screen
        self.show_home_screen()
        self.root.resizable(False, False)

    def search_records(self):
        """
        function searches all the records given the query by the admin search on the 'record' table
        :return: None
        """

        # if admin hasn't entered any query, showing all records
        if self.search_entry.get() == "":
            for record in self.tree.get_children():
                self.tree.delete(record)

            self.row_counter = 0
            for i in self.record_lst:

                # inserting the data in Treeview widget
                if self.row_counter % 2 == 0:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("evenrow",))
                else:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("oddrow",))
                self.row_counter += 1

        else:

            # getting the requested answer for the query
            self.client.send(pickle.dumps(["#GET ADMIN QUERY FOR RECORD#", self.search_entry.get()]))
            self.wait_for_server_to_respond(self.admin_data, 4)

            # if query is not found
            if not any(list(i) in self.record_lst for i in self.admin_data[4]):
                messagebox.showerror("Error", "Record doesn't seem to appear in this table")
                return

            # showing the relevant results
            self.row_counter = 0
            for record in self.tree.get_children():
                self.tree.delete(record)

            for i in self.admin_data[4]:
                if self.row_counter % 2 == 0:

                    # inserting the data in Treeview widget
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("evenrow",))
                else:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("oddrow",))
                self.row_counter += 1

        # showing how many records were found
        self.w.config(text=f"The number of records found is {self.row_counter}")
        self.admin_data[4] = None

    def upload_attractions(self):
        """
        function shows form to upload attractions
        :return: None
        """

        # starting root
        self.updload_root = Toplevel(self.root)

        # showing label and submit button
        CTkLabel(self.updload_root, text=f"Upload your attractions file!!!!!\n\n"
                                         f"(Remember to only upload a json file)", bg='#F5F5F5',
                 text_font=("Roboto Medium", -20)).pack(pady=20)

        CTkButton(self.updload_root, fg_color="#E0E0E0", hover_color="#33A8FF",
                  border_width=3, relief=SOLID, cursor='hand2', text="Select",
                  command=self.add_attractions_file).pack(side='bottom', pady=10)

    def data_base_to_csv(self):
        """
        function exports any database table to a .csv file in the admin directory
        :return:
        """

        # creating root
        csv_root = Toplevel(self.root)
        csv_root.resizable(False, False)

        CTkLabel(csv_root, text=f"Export To Csv Any Data Base", bg='#F5F5F5',
                 text_font=("Roboto Medium", -30)).pack(pady=20)

        # showing radio buttons --> each radio button representing a table in database
        frame = Frame(csv_root)
        self.radio_var = IntVar(value=0)
        self.radio_button1 = CTkRadioButton(master=frame, variable=self.radio_var, text="record",
                                            text_font=("Roboto Medium", -16), value=0)
        self.radio_button1.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.radio_button2 = CTkRadioButton(master=frame, variable=self.radio_var, text="offers",
                                            text_font=("Roboto Medium", -16), value=1)
        self.radio_button2.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.radio_button3 = CTkRadioButton(master=frame, variable=self.radio_var, text="purchases",
                                            text_font=("Roboto Medium", -16), value=2)
        self.radio_button3.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.radio_button4 = CTkRadioButton(master=frame, variable=self.radio_var, text="ratings",
                                            text_font=("Roboto Medium", -16), value=3)
        self.radio_button4.grid(row=3, column=0, padx=10, pady=5, sticky="w")

        l = ["record", "offers", "purchases", "ratings"]  # list of database tables

        # submit button --> sending to server which database admin wants to save
        CTkButton(frame, fg_color="#E0E0E0", hover_color="#33A8FF",
                  border_width=3, relief=SOLID, cursor='hand2', text="Select",
                  command=lambda: [self.client.send(pickle.dumps([f"#SAVE DATA BASE# {l[self.radio_var.get()]}"])),
                                   csv_root.destroy()]).grid(row=4, column=0, pady=5)

        frame.pack(pady=10)

    def add_attractions_file(self):
        """
        function adds the attraction file (.json) to the system
        :return: None
        """

        # opening task window for user
        self.root.attributes('-topmost', False)
        file_format = [("Json File", "*.json")]
        file = askopenfile(mode='r', filetypes=file_format)

        if not file:

            # handling errors
            self.filenames = None
            messagebox.showerror("Error", "You must choose an image")
            return

        # getting the files real path
        filepath = os.path.abspath(file.name)

        with open(filepath, "r", encoding='utf-8') as f:

            # loading the data from the .json file
            data = json.loads(f.read())

            # sending for each attraction --> the location, the name, and the image name of the attraction
            for location, (name, path_to_picture) in data.items():
                with open(path_to_picture, "rb") as f:
                    bytes = f.read()
                    image_name = path_to_picture[path_to_picture.rfind("\\") + 1:]
                    self.client.send(f"NAME {image_name}".encode())
                    self.client.send(bytes)

                self.client.send(pickle.dumps(["#NEW ATTRACTION#", [location, name, image_name]]))

                with open(PATH + "\\map_images" + "\\" + image_name, "wb") as f:
                    f.write(bytes)

            # showing success pop up message
            messagebox.showinfo("Success", "Thank you for uploading these attractions", icon="info")

        self.root.attributes('-topmost', True)
        self.updload_root.destroy()

    def open_admin_map(self):
        """
        function opens a special admin map too see in which dates certain room are taken
        :return: None
        """

        if self.__logged_in:
            self.admin_map = App(self.root, self.menubar, self.offers, self.__logged_in, self.client, self.map_data,
                                 self.room_data, self.attractions, self.server_time,
                                 self.uemail, True, self.admin_data)

    def search_purchases(self):
        """
        function searches all the purchases given the query by the admin search on the 'purchases' table
        :return: None
        """

        # if admin hasn't entered any query, showing all purchases
        if self.purchase_entry.get() == "":
            for record in self.tree.get_children():
                self.tree.delete(record)

            self.row_counter = 0
            for i in self.purchases_list:
                if self.row_counter % 2 == 0:

                    # inserting the data in Treeview widget
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("evenrow",))
                else:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("oddrow",))
                self.row_counter += 1

        else:

            # getting the requested answer for the query
            self.client.send(pickle.dumps(["#GET ADMIN QUERY FOR PURCHASE#", self.purchase_entry.get()]))
            self.wait_for_server_to_respond(self.admin_data, 5)

            # if query is not found
            if not any(list(i) in self.purchases_list for i in self.admin_data[5]):
                messagebox.showerror("Error", "Record doesn't seem to appear in this table")
                return

            # showing relevant results
            self.row_counter = 0
            for record in self.tree.get_children():
                self.tree.delete(record)

            for i in self.admin_data[5]:

                # inserting the data in Treeview widget
                if self.row_counter % 2 == 0:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("evenrow",))
                else:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("oddrow",))
                self.row_counter += 1

        # showing how many purchases were found
        self.w.config(text=f"The number of records found is {self.row_counter}")
        self.admin_data[5] = None

    def search_offers(self):
        """
        function searches all the offers given the query by the admin search on the 'offers' table
        :return: None
        """

        # if admin didn't chose category for search offer, showing error
        if self.offers_drop_down_variable.get() == "":
            messagebox.showerror("Error", "Please select a category to search for")
            return

        # if admin hasn't entered any query, showing all the offers
        if self.offer_entry.get() == "":
            for record in self.tree.get_children():
                self.tree.delete(record)

            self.row_counter = 0
            for i in self.offer_lst:
                if self.row_counter % 2 == 0:

                    # inserting the data in Treeview widget
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                     tag=("evenrow",))
                else:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                     tag=("oddrow",))
                self.row_counter += 1
        else:

            # if the admin chose category 'offer_id', converting search to integer
            # searching for the offer in the offers list
            if self.offers_drop_down_variable.get() == "offer_id":
                if int(self.offer_entry.get()) not in [i[self.offer_columns.index(self.offers_drop_down_variable.get())]
                                                       for i in
                                                       self.offer_lst]:
                    # if search wasn't found
                    messagebox.showerror("Error", "Offer not in any of the records")
                    return

                self.row_counter = 0
                for record in self.tree.get_children():
                    self.tree.delete(record)

                # if user chose the category 'offer_id'
                if self.offers_drop_down_variable.get() == "offer_id":
                    lst = [i for i in self.offer_lst if
                           i[self.offer_columns.index(self.offers_drop_down_variable.get())] == int(
                               self.offer_entry.get())]
                else:
                    lst = [i for i in self.offer_lst if
                           i[self.offer_columns.index(
                               self.offers_drop_down_variable.get())] == self.offer_entry.get()]
                for i in lst:
                    if self.row_counter % 2 == 0:

                        # inserting the data in Treeview widget
                        self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                         tag=("evenrow",))
                    else:
                        self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                         tag=("oddrow",))
                    self.row_counter += 1

            # if the user chose any other category
            else:

                # if the user chose any of the categories: 'time_available', 'conditions', 'room_name', 'location'
                if self.offer_columns.index(self.offers_drop_down_variable.get()) > 4:
                    if self.offer_entry.get() not in [
                        i[self.offer_columns.index(self.offers_drop_down_variable.get()) + 1] for i in
                        self.offer_lst]:

                        # if search wasn't found
                        messagebox.showerror("Error", "Offer not in any of the records")
                        return

                    self.row_counter = 0
                    for record in self.tree.get_children():
                        self.tree.delete(record)

                    # if user chose the category 'offer_id'
                    if self.offers_drop_down_variable.get() == "offer_id":
                        lst = [i for i in self.offer_lst if
                               i[self.offer_columns.index(self.offers_drop_down_variable.get()) + 1] == int(
                                   self.offer_entry.get())]
                    else:
                        lst = [i for i in self.offer_lst if
                               i[self.offer_columns.index(
                                   self.offers_drop_down_variable.get()) + 1] == self.offer_entry.get()]
                    for i in lst:
                        if self.row_counter % 2 == 0:

                            # inserting the data in Treeview widget
                            self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                             tag=("evenrow",))
                        else:
                            self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                             tag=("oddrow",))
                        self.row_counter += 1

                else:

                    # if search wasn't found
                    if self.offer_entry.get() not in [
                        i[self.offer_columns.index(self.offers_drop_down_variable.get())] for i in
                        self.offer_lst]:
                        messagebox.showerror("Error", "Offer not in any of the records")
                        return

                    self.row_counter = 0
                    for record in self.tree.get_children():
                        self.tree.delete(record)

                    # if user chose the category 'offer_id'
                    if self.offers_drop_down_variable.get() == "offer_id":
                        lst = [i for i in self.offer_lst if
                               i[self.offer_columns.index(self.offers_drop_down_variable.get())] == int(
                                   self.offer_entry.get())]
                    else:
                        lst = [i for i in self.offer_lst if
                               i[self.offer_columns.index(
                                   self.offers_drop_down_variable.get())] == self.offer_entry.get()]
                    for i in lst:
                        if self.row_counter % 2 == 0:

                            # inserting the data in Treeview widget
                            self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                             tag=("evenrow",))
                        else:
                            self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                             tag=("oddrow",))
                        self.row_counter += 1

        # showing the number of offers that were found
        self.w.config(text=f"The number of records found is {self.row_counter}")

    def show_records(self):
        """
        function shows all records that are in the database 'record' table
        :return: None
        """

        # clearing the screen
        Admin.clear_screen(self.root, self.menubar)

        # showing label
        CTkLabel(self.root, text=f"Search users", bg='#F5F5F5',
                 text_font=("Roboto Medium", -30)).pack(pady=20)

        # setting frame, entry for searching users, search image
        search_frame = CTkFrame(bg="white")
        self.search_entry = CTkEntry(search_frame, width=150, height=50, placeholder_text="Enter search")
        img = ImageTk.PhotoImage(Image.open("airbnb_images//search.png").resize((50, 50)))
        search_pil = Label(search_frame, image=img)
        search_pil.image = img
        self.search_entry.pack(side="left")
        search_pil.pack(side="left")
        search_frame.pack(pady=20)

        # sending request for records
        self.client.send("#GET ADMIN RECORDS#".encode())
        self.wait_for_server_to_respond(self.admin_data, 1)
        self.row_counter = 0
        self.record_lst = []
        for key, value in self.admin_data[1].items():
            self.record_lst.append([key] + [i for i in value])

        s = ttk.Style()
        s.theme_use('clam')

        # creating tree for all the records
        self.tree = ttk.Treeview(self.root, column=("#1", "#2", "#3", "#4", "#5", "#6"), show='headings', height=6)

        # setting tree columns
        self.tree.column("# 1", anchor=CENTER, width=100)
        self.tree.heading("# 1", text="User Id")
        self.tree.column("# 2", anchor=CENTER, width=100)
        self.tree.heading("# 2", text="Email")
        self.tree.column("# 3", anchor=CENTER, width=100)
        self.tree.heading("# 3", text="Name")
        self.tree.column("# 4", anchor=CENTER, width=100)
        self.tree.heading("# 4", text="Country")
        self.tree.column("# 5", anchor=CENTER, width=100)
        self.tree.heading("# 5", text="Password")
        self.tree.column("# 6", anchor=CENTER, width=100)
        self.tree.heading("# 6", text="Is Admin")

        # inserting rows
        for i in self.record_lst:
            if self.row_counter % 2 == 0:

                # inserting the data in Treeview widget
                self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("evenrow",))
            else:
                self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("oddrow",))
            self.row_counter += 1

        self.tree.tag_configure('oddrow', background='white')
        self.tree.tag_configure('evenrow', background='#f2f2f2')

        self.tree.pack(pady=20, expand=1, fill=BOTH)

        self.w = Label(self.root, text=f"The number of records found is {self.row_counter}", bg='white',
                       font=("Roboto Medium", 15))
        self.w.pack(pady=20)

        # binding tree to 'search_records' and 'make_user_admin' functions
        self.row_counter = 0
        search_pil.bind("<Button-1>", lambda h: self.search_records())
        self.tree.bind("<Double-1>", lambda h: self.make_user_admin())

    def make_user_admin(self):
        """
        function makes a certain user admin
        :return: None
        """

        # getting the user
        item = self.tree.selection()[0]
        data = self.tree.item(item, "values")
        q = messagebox.askquestion("Confirmation", "Do you want to make this user admin?",
                                   icon='info')

        # sending request to make admin
        if q == "yes":
            self.client.send(pickle.dumps(["#MAKE USER ADMIN BY EMAIL#", data[1]]))
            messagebox.showinfo("Success", f"User {data[2]} is now admin!", icon="info")

    def show_cancel_purchases(self):
        """
        function creates a table tree for purchases client has made
        :return: None
        """

        # clearing the screen
        Client.clear_screen(self.root, self.menubar, self.on_closing)

        # getting purchases
        if self.__logged_in:
            self.client.send(pickle.dumps(["#GET PURCHASES#", self.uemail]))
            self.wait_for_server_to_respond(self.user_data, 3)
            purchases = self.user_data[3]
        else:
            purchases = map.get_recent_orders()

        CTkLabel(self.root, text=f"Your purchases\n\n"
                                 f"(Double click to cancel)", bg='#F5F5F5',
                 text_font=("Roboto Medium", -30)).pack(pady=20)

        # showing note label to user
        f = CTkFrame(self.root, corner_radius=0, border_width=3, bg="white")
        CTkLabel(f, text=f"Note\n\nThe purchases that are shown here are only the ones that\n"
                         f"are until 2 days before the deadline.\n"
                         f"Please take that into consideration 🙏🙏🙏🙏",
                 text_font=("Roboto Medium", -15)).pack(pady=3)
        f.pack(pady=3)

        # choosing style for tree
        s = ttk.Style()
        s.theme_use('clam')

        # creating tree for purchases
        self.tree = ttk.Treeview(self.root, column=("c1", "c2", "c3", "c4", "c5"), show='headings', height=5)

        # setting tree columns
        self.tree.column("# 1", anchor=CENTER)
        self.tree.heading("# 1", text="Purchase id")
        self.tree.column("# 2", anchor=CENTER)
        self.tree.heading("# 2", text="Offer id")
        self.tree.column("# 3", anchor=CENTER)
        self.tree.heading("# 3", text="Check In")
        self.tree.column("# 4", anchor=CENTER)
        self.tree.heading("# 4", text="Check Out")
        self.tree.column("# 5", anchor=CENTER)
        self.tree.heading("# 5", text="Email")

        # inserting rows
        for i in purchases:

            d = datetime.strptime(i[2].split("-")[1][1:], '%Y/%m/%d')

            if int(str(datetime.today() - d)[0]) >= 2:
                # inserting the data in Treeview widget
                self.tree.insert('', 'end', values=(i[0], i[1],
                                                    i[2].split("-")[0], i[2].split("-")[1], i[3]))

        # binding each element to cancel_purchases function
        self.tree.bind("<Double-1>", lambda *args: self.cancel_purchases())

        self.tree.pack(pady=50, fill=X)

    def show_offers(self):
        """
        function shows all records that are in the database 'record' table
        :return: None
        """

        Admin.clear_screen(self.root, self.menubar)

        CTkLabel(self.root, text=f"Search Offers", bg='#F5F5F5',
                 text_font=("Roboto Medium", -30)).pack(pady=20)

        # creating option menu of what the admin wants to search by (category) a certain offer
        self.offers_drop_down_variable = StringVar()
        self.offers_drop_down_variable.set("Select what to search for")
        self.offer_columns = ["offer_id", "user_id", "room_id", "price_per_day", "time_available", "conditions",
                              "room_name", "location"]
        self.dropdown = OptionMenu(self.root, self.offers_drop_down_variable, *self.offer_columns)
        self.dropdown.config(bg='light blue')
        self.dropdown.pack(pady=5)

        # setting frame, entry for searching users, search image
        search_frame = CTkFrame(bg="white")
        self.offer_entry = CTkEntry(search_frame, width=120, height=50, placeholder_text="Enter search")
        img = ImageTk.PhotoImage(Image.open("airbnb_images//search.png").resize((50, 50)))
        search_pil = Label(search_frame, image=img)
        search_pil.image = img
        self.offer_entry.pack(side="left")
        search_pil.pack(side="left")
        search_frame.pack(pady=20)

        # sending request for records
        self.client.send("#GET ADMIN OFFERS#".encode())
        self.wait_for_server_to_respond(self.admin_data, 2)
        self.row_counter = 0
        self.offer_lst = []
        for key, value in self.admin_data[2].items():
            self.offer_lst.append([key] + [i for i in value])

        # creating tree for all the offers
        self.tree = ttk.Treeview(self.root, column=("#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8"),
                                 show='headings')

        # setting tree columns
        self.tree.column("# 1", anchor=CENTER, width=15)
        self.tree.heading("# 1", text="Offer Id")
        self.tree.column("# 2", anchor=CENTER, width=15)
        self.tree.heading("# 2", text="User Id")
        self.tree.column("# 3", anchor=CENTER, width=15)
        self.tree.heading("# 3", text="Room Id")
        self.tree.column("# 4", anchor=CENTER, width=15)
        self.tree.heading("# 4", text="Price Per Night")
        self.tree.column("# 5", anchor=CENTER, width=100)
        self.tree.heading("# 5", text="Duration")
        self.tree.column("# 6", anchor=CENTER, width=50)
        self.tree.heading("# 6", text="Conditions")
        self.tree.column("# 7", anchor=CENTER, width=15)
        self.tree.heading("# 7", text="Room Name")
        self.tree.column("# 8", anchor=CENTER, width=20)
        self.tree.heading("# 8", text="Geo (coordinates)")

        # inserting rows
        for i in self.offer_lst:
            if self.row_counter % 2 == 0:

                # inserting the data in Treeview widget
                self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                 tag=("evenrow",))
            else:
                self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                 tag=("oddrow",))
            self.row_counter += 1

        self.tree.tag_configure('oddrow', background='white')
        self.tree.tag_configure('evenrow', background='#f2f2f2')

        # binding tree to 'show_cash_flow_for_offers' function
        self.tree.pack(pady=20, expand=1, fill=BOTH)
        self.tree.bind("<Double-1>", lambda *args: self.show_cash_flow_for_offers())

        # showing how many offers were found
        self.w = Label(self.root, text=f"The number of records found is {self.row_counter}", bg='white',
                       font=("Roboto Medium", 15))
        self.w.pack(pady=20)
        search_pil.bind("<Button-1>", lambda h: self.search_offers())

    def show_cash_flow_for_offers(self):
        """
        function shows cash flow for offer
        :return: None
        """

        # getting data on the offer
        item = self.tree.selection()[0]
        data = self.tree.item(item, "values")

        # getting check in and check out dates
        check_in, check_out = data[4].split("-")[0][:-1], data[4].split("-")[1][1:]
        date_check_in, date_check_out = datetime.strptime(check_in, '%Y/%m/%d'), datetime.strptime(check_out,
                                                                                                   '%Y/%m/%d')

        # getting the total price for the offer
        total_price_for_offer = len(App.date_range(date_check_in, date_check_out)) * int(data[3].replace(",", ""))
        self.client.send(pickle.dumps(["#GET PURCHASE BY OFFER ID#", data[0]]))
        self.wait_for_server_to_respond(self.map_data, 5)

        if self.map_data[5] != []:

            # iterating over every purchase that was made for this offer
            total_price_for_purchase = 0
            for i in self.map_data[5]:
                # getting check in and check out dates
                purchase_check_in, purchase_check_out = i[2].split("-")[0][:-1], i[2].split("-")[1][1:]
                purchase_date_check_in, purchase_date_check_out = datetime.strptime(purchase_check_in,
                                                                                    '%Y/%m/%d'), datetime.strptime(
                    purchase_check_out,
                    '%Y/%m/%d')

                # adding the bought rooms price to the cash for the offer
                total_price_for_purchase += len(App.date_range(purchase_date_check_in, purchase_date_check_out)) * int(
                    data[3].replace(",", ""))

        else:
            total_price_for_purchase = 0

        # opening root for the cash flow
        cash_flow_root = CTkToplevel(self.root)
        cash_flow_root.resizable(False, False)
        cash_flow_root.title("Cash Flow")
        percentage = float(total_price_for_purchase / total_price_for_offer)

        # showing an explanation to the user about how the cash flow for the offer works
        self.cash_frame = CTkFrame(cash_flow_root)
        self.label_info_1 = CTkLabel(master=self.cash_frame,
                                     text=f"The progress bar presents the cash flow\n" +
                                          "for this current offer.\n" +
                                          "The flow is presented in percentage,\n"
                                          "meaning the bar will go as far as the percentage of the days "
                                          "filled from the total days of the offer,\n"
                                          "times the price for night for the specific offer, so we can "
                                          "see how much money was filled for this offer.\n\n\n"
                                          f"{percentage * 100}% of the total price of the offer is filled",
                                     height=100,
                                     fg_color=("white", "gray38"),  # <- custom tuple-color
                                     justify=LEFT,
                                     text_font=("Roboto Medium", -20))

        # widgets placements, showing progress bar of the cash flow
        self.label_info_1.grid(column=0, row=0, sticky="nwe", padx=15, pady=15)
        self.progressbar = CTkProgressBar(master=self.cash_frame)
        self.progressbar.set(percentage)
        self.progressbar.grid(row=1, column=0, sticky="ew", padx=15, pady=15)
        self.cash_frame.pack()

    def show_admin_purchases(self):
        """
        function shows all purchases that are in the database 'purchases' table
        :return: None
        """

        # clearing the screen
        Admin.clear_screen(self.root, self.menubar)

        CTkLabel(self.root, text=f"Search Purchases", bg='#F5F5F5',
                 text_font=("Roboto Medium", -30)).pack(pady=20)

        # setting frame, entry for searching purchases, search image
        search_frame = CTkFrame(bg="white")
        self.purchase_entry = CTkEntry(search_frame, width=150, height=50, placeholder_text="Enter user's email")
        img = ImageTk.PhotoImage(Image.open("airbnb_images//search.png").resize((50, 50)))
        search_pil = Label(search_frame, image=img)
        search_pil.image = img
        self.purchase_entry.pack(side="left")
        search_pil.pack(side="left")
        search_frame.pack(pady=20)

        # getting all the purchases
        self.client.send("#GET ADMIN PURCHASES#".encode())
        self.wait_for_server_to_respond(self.admin_data, 3)
        self.row_counter = 0
        self.purchases_list = []
        for key, value in self.admin_data[3].items():
            self.purchases_list.append([key] + [i for i in value])

        # creating tree for all the purchases
        self.tree = ttk.Treeview(self.root, column=("#1", "#2", "#3", "#4", "#5", "#6"), show='headings', height=6)

        # setting columns for tree
        self.tree.column("# 1", anchor=CENTER, width=100)
        self.tree.heading("# 1", text="Purchase Id")
        self.tree.column("# 2", anchor=CENTER, width=100)
        self.tree.heading("# 2", text="Offer Id")
        self.tree.column("# 3", anchor=CENTER, width=100)
        self.tree.heading("# 3", text="Duration")
        self.tree.column("# 4", anchor=CENTER, width=100)
        self.tree.heading("# 4", text="User Email")
        self.tree.column("# 5", anchor=CENTER, width=100)
        self.tree.heading("# 5", text="Credit Number")
        self.tree.column("# 6", anchor=CENTER, width=100)
        self.tree.heading("# 6", text="Is Registered")

        # inserting rows
        for i in self.purchases_list:
            if self.row_counter % 2 == 0:

                # inserting the data in Treeview widget
                self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("evenrow",))
            else:
                self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("oddrow",))
            self.row_counter += 1

        self.tree.tag_configure('oddrow', background='white')
        self.tree.tag_configure('evenrow', background='#f2f2f2')

        self.tree.pack(pady=20, expand=1, fill=BOTH)

        # showing how many purchases were found
        self.w = Label(self.root, text=f"The number of records found is {self.row_counter}", bg='white',
                       font=("Roboto Medium", 15))
        self.w.pack(pady=20)

        # binding tree to 'search_purchases' function
        self.row_counter = 0
        search_pil.bind("<Button-1>", lambda h: self.search_purchases())

    def show_admin_ratings(self):
        """
        function shows all ratings that are in the database 'ratings' table
        :return: None
        """

        # clearing the screen
        Admin.clear_screen(self.root, self.menubar)

        CTkLabel(self.root, text=f"Search Ratings", bg='#F5F5F5',
                 text_font=("Roboto Medium", -30)).pack(pady=20)

        # setting frame, entry for searching purchases, search image
        search_frame = CTkFrame(bg="white")
        self.ratings_entry = CTkEntry(search_frame, width=150, height=50, placeholder_text="Enter Search")
        img = ImageTk.PhotoImage(Image.open("airbnb_images//search.png").resize((50, 50)))
        search_pil = Label(search_frame, image=img)
        search_pil.image = img
        self.ratings_entry.pack(side="left")
        search_pil.pack(side="left")
        search_frame.pack(pady=20)

        # getting the 'ratings' table
        self.client.send("#GET ADMIN RATINGS#".encode())
        self.wait_for_server_to_respond(self.admin_data, 6)
        self.row_counter = 0
        self.ratings_list = []
        for key, value in self.admin_data[6].items():
            self.ratings_list.append([key] + [i for i in value])

        # creating tree for all the ratings
        self.tree = ttk.Treeview(self.root, column=("#1", "#2", "#3", "#4", "#5", "#6"), show='headings', height=6)

        # setting columns for tree
        self.tree.column("# 1", anchor=CENTER, width=100)
        self.tree.heading("# 1", text="Purchase Id")
        self.tree.column("# 2", anchor=CENTER, width=100)
        self.tree.heading("# 2", text="Offer Id")
        self.tree.column("# 3", anchor=CENTER, width=100)
        self.tree.heading("# 3", text="User Email")
        self.tree.column("# 4", anchor=CENTER, width=100)
        self.tree.heading("# 4", text="Scale Rating")
        self.tree.column("# 5", anchor=CENTER, width=100)
        self.tree.heading("# 5", text="Review")
        self.tree.column("# 6", anchor=CENTER, width=100)
        self.tree.heading("# 6", text="Is Anonymous")

        # inserting rows
        for i in self.ratings_list:
            if self.row_counter % 2 == 0:

                # inserting the data in Treeview widget
                self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("evenrow",))
            else:
                self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("oddrow",))
            self.row_counter += 1

        self.tree.tag_configure('oddrow', background='white')
        self.tree.tag_configure('evenrow', background='#f2f2f2')

        self.tree.pack(pady=20, expand=1, fill=BOTH)

        # showing how many ratings were found
        self.w = Label(self.root, text=f"The number of records found is {self.row_counter}", bg='white',
                       font=("Roboto Medium", 15))
        self.w.pack(pady=20)

        # binding tree to 'search_ratings' function
        self.row_counter = 0
        search_pil.bind("<Button-1>", lambda h: self.search_ratings())

    def search_ratings(self):
        """
        function searches all the ratings given the query by the admin search on the 'ratings' table
        :return: None
        """

        # if admin hasn't entered any query, showing all records
        if self.ratings_entry.get() == "":
            for record in self.tree.get_children():
                self.tree.delete(record)

            self.row_counter = 0
            for i in self.ratings_list:

                # inserting the data in Treeview widget
                if self.row_counter % 2 == 0:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("evenrow",))
                else:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("oddrow",))
                self.row_counter += 1

        else:

            # getting the requested answer for the query
            self.client.send(pickle.dumps(["#GET ADMIN QUERY FOR RATING#", self.ratings_entry.get()]))
            self.wait_for_server_to_respond(self.admin_data, 7)

            # if query was not found
            if not any(list(i) in self.ratings_list for i in self.admin_data[7]):
                messagebox.showerror("Error", "Record doesn't seem to appear in this table")
                return

            self.row_counter = 0
            for record in self.tree.get_children():
                self.tree.delete(record)

            for i in self.admin_data[7]:

                # inserting the data in Treeview widget
                if self.row_counter % 2 == 0:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("evenrow",))
                else:
                    self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[4], i[5]), tag=("oddrow",))
                self.row_counter += 1

        # showing how many ratings were found
        self.w.config(text=f"The number of records found is {self.row_counter}")
        self.admin_data[7] = None

    def user_quit(self):
        """
        function closes client socket
        :return:None
        """
        try:
            self.client.close()
            print("----CLIENT SHUT DOWN----")
        except:
            pass

    def show_cancel_offers(self):
        """
        function creates a tree for offers client has made
        :return: None
        """

        # clearing the screen
        Client.clear_screen(self.root, self.menubar)

        # if user isn't logged in yet
        if not self.__logged_in:
            messagebox.showerror("Error", "You are not logged in yet")
            self.show_home_screen()
            return

        # showing label
        CTkLabel(self.root, text=f"Your offers\n\n"
                                 f"(Double click to dispute)", bg='#F5F5F5',
                 text_font=("Roboto Medium", -30)).pack(pady=20)

        # getting offers
        self.client.send(pickle.dumps(["#GET OFFER BY EMAIL#", self.uemail]))
        self.wait_for_server_to_respond(self.user_data, 6)

        # creating tree for offers
        self.row_counter = 0
        self.tree = ttk.Treeview(self.root, column=("#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8"),
                                 show='headings')

        # setting tree columns
        self.tree.column("# 1", anchor=CENTER, width=15)
        self.tree.heading("# 1", text="Offer Id")
        self.tree.column("# 2", anchor=CENTER, width=15)
        self.tree.heading("# 2", text="User Id")
        self.tree.column("# 3", anchor=CENTER, width=15)
        self.tree.heading("# 3", text="Room Id")
        self.tree.column("# 4", anchor=CENTER, width=15)
        self.tree.heading("# 4", text="Price Per Night")
        self.tree.column("# 5", anchor=CENTER, width=100)
        self.tree.heading("# 5", text="Duration")
        self.tree.column("# 6", anchor=CENTER, width=50)
        self.tree.heading("# 6", text="Conditions")
        self.tree.column("# 7", anchor=CENTER, width=15)
        self.tree.heading("# 7", text="Room Name")
        self.tree.column("# 8", anchor=CENTER, width=20)
        self.tree.heading("# 8", text="Geo (coordinates)")

        # inserting rows
        for i in self.user_data[6]:

            # inserting the data in Treeview widget
            if self.row_counter % 2 == 0:
                self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                 tag=("evenrow",))
            else:
                self.tree.insert('', 'end', values=(i[0], i[1], i[2], i[3], i[5], i[6], i[7], i[8]),
                                 tag=("oddrow",))
            self.row_counter += 1

        # setting each row in different colors
        self.tree.tag_configure('oddrow', background='white')
        self.tree.tag_configure('evenrow', background='#f2f2f2')

        # binding tree to cancel_offer function
        self.tree.pack(pady=20, expand=1, fill=BOTH)
        self.tree.bind("<Double-1>", lambda *args: self.cancel_offer())

    def cancel_offer(self):
        """
        function cancels offers client has made
        :return: None
        """

        # getting the offer
        try:
            item = self.tree.selection()[0]
            data = self.tree.item(item, "values")
        except IndexError:

            # handling errors
            messagebox.showerror("error", "You haven't offered anything yet")
            return

        q = messagebox.askquestion("Confirmation", "Are you sure you want this offers to be canceled?",
                                   icon='warning')

        # disputing offer
        if q == "yes":
            self.client.send(pickle.dumps(["#DELETE FROM DATA BASE# offers", data[0]]))
            messagebox.showinfo("Success", "You have disputed offer!!!")

        self.tree.delete(item)

    def cancel_purchases(self):
        """
        function cancels purchases client has made
        :return: None
        """

        # getting the purchase
        try:
            item = self.tree.selection()[0]
            data = self.tree.item(item, "values")
        except IndexError:
            messagebox.showerror("error", "You haven't purchased anything yet")
            return

        # getting room name by the offer id
        self.client.send(pickle.dumps(["#GET ROOM NAME BY OFFER ID#", data[1]]))
        self.wait_for_server_to_respond(self.room_data, 0)

        q = messagebox.askquestion("Confirmation", "Are you sure you want this purchase to be canceled?",
                                   icon='warning')

        # deleting purchase
        if q == "yes":
            self.client.send(pickle.dumps(["#DELETE FROM DATA BASE# purchases", data[0]]))
            messagebox.showinfo("Success", "You have disputed purchase!!!")

        self.tree.delete(item)

    def show_purchases(self):
        """
        function shows user his purchases for him/her to rate them
        :return: None
        """

        Client.clear_screen(self.root, self.menubar)

        CTkLabel(self.root, text=f"Your purchases", bg='#F5F5F5',
                 text_font=("Roboto Medium", -30)).pack(pady=20)

        # getting purchases
        if self.__logged_in:
            self.client.send(pickle.dumps(["#GET PURCHASES#", self.uemail]))
            self.wait_for_server_to_respond(self.user_data, 3)
            purchases = self.user_data[3]

            # deleting disputed purchases
            for i in purchases:
                if int(i[1]) in self.disputed_id:
                    purchases.remove(i)
        else:
            purchases = map.get_recent_orders()

        s = ttk.Style()
        s.theme_use('clam')

        # creating tree for showing purchases
        self.tree = ttk.Treeview(self.root, column=("c1", "c2", "c3", "c4", "c5"), show='headings', height=5)

        # setting tree columns
        self.tree.column("# 1", anchor=CENTER)
        self.tree.heading("# 1", text="Purchase id")
        self.tree.column("# 2", anchor=CENTER)
        self.tree.heading("# 2", text="Offer id")
        self.tree.column("# 3", anchor=CENTER)
        self.tree.heading("# 3", text="Check In")
        self.tree.column("# 4", anchor=CENTER)
        self.tree.heading("# 4", text="Check Out")
        self.tree.column("# 5", anchor=CENTER)
        self.tree.heading("# 5", text="Email")

        # inserting rows
        for i in purchases:

            # inserting the data in Treeview widget
            self.tree.insert('', 'end', values=(i[0], i[1],
                                                i[2].split("-")[0], i[2].split("-")[1], i[3]))

        # binding tree to show_rating function
        self.tree.bind("<Double-1>", lambda *args: self.show_rating())

        self.tree.pack(pady=20, fill=X)

    def show_rating(self):
        """
        function shows rating screen for user in order to rate a room he has been in
        :return: None
        """

        # getting data on purchase
        try:
            item = self.tree.selection()[0]
            data = self.tree.item(item, "values")
        except IndexError:
            messagebox.showerror("error", "You haven't purchased anything yet")
            return

        # if user has already rated
        if item in self.ratings.keys():
            messagebox.showerror("error", "You have already rated this purchase")
            return

        # opening rating root
        rating_root = Toplevel(self.root)
        rating_root.resizable(False, False)
        self.client.send(pickle.dumps(["#GET ROOM NAME BY OFFER ID#", data[1]]))
        self.wait_for_server_to_respond(self.room_data, 0)

        var = DoubleVar()

        # getting scale rating
        CTkLabel(rating_root, text=f"How did you like your stay at {self.room_data[0]}", bg='#F5F5F5',
                 text_font=("Roboto Medium", -20)).pack(pady=5)

        # creating widgets and placements, sliders, and scrolled texts
        slider1 = Scale(rating_root, from_=0, to=10, length=400, resolution=1, orient=HORIZONTAL,
                        activebackground="green", variable=var)
        slider1.pack(pady=5)

        CTkLabel(rating_root, text=f"Please tell us more on your stay at {self.room_data[0]}",
                 bg='#F5F5F5',
                 text_font=("Roboto Medium", -20)).pack(pady=10)

        # creating scrolled text for more detailed review
        self.text_frame = ScrolledText(rating_root)
        self.text_frame.pack()

        # getting review from client
        btn_frame = Frame(rating_root)
        self.switch = CTkSwitch(btn_frame, text="Anonymous")

        # submit button
        w = CTkButton(btn_frame, fg_color="#E0E0E0", hover_color="#33A8FF",
                      border_width=3, text_font=("Roboto Medium", -18), relief=SOLID, cursor='hand2', text="Submit",
                      command=lambda: self.update_rating(data, var, rating_root, item, self.text_frame.get(1.0, END),
                                                         str(self.switch.get())))
        w.pack(side="right", padx=50)

        # widget placements
        self.switch.pack(side="left", padx=50)

        btn_frame.pack(side="bottom", pady=10)

    def update_rating(self, data, var, rating_root, item_chosen, review, is_anonymous):
        """
        function updates 'ratings' data base
        :param data: data on purchase
        :param var: the scale rating
        :param rating_root: the rating root
        :param item_chosen: the purchase chosen
        :param review: the review
        :param is_anonymous: does the client want to stay anonymous
        :return: None
        """

        # updating 'ratings' data base
        self.client.send(
            pickle.dumps(["#UPDATE DATA BASE# ratings", [data[0], data[1], data[4], var.get(), review, is_anonymous]]))
        messagebox.showinfo("info", "Rating saved")
        rating_root.destroy()
        self.ratings[item_chosen] = True

    def open_map(self):
        """
        function opens map for client
        :return: None
        """

        # opening the map class for client
        if self.__logged_in:
            self.map = App(self.root, self.menubar, self.offers, self.__logged_in, self.client, self.map_data,
                           self.room_data, self.attractions, self.server_time,
                           self.uemail)
        else:
            self.map = App(self.root, self.menubar, self.offers, self.__logged_in, self.client, self.map_data,
                           self.room_data, self.attractions, self.server_time)

        # events of the map
        if self.updated_offers is not None:
            self.map.update_markers(self.updated_offers)

        self.map.marker_event += self.send_to_server_locations
        self.map.purchase_event += self.send_to_server_purchases

    def send_to_server_locations(self):
        """
        function sends the server a dictionary with location and color of the offer every time a marker is being clicked
        :return: None
        """

        self.locations = self.map.marker_colors
        self.client.send(pickle.dumps(self.locations))

    def send_to_server_purchases(self):
        """
        function sends to server purchases
        :return: None
        """

        self.client.send(pickle.dumps(["#PURCHASE ID#", self.map.purchase_id]))

    def offer_room(self):
        """
        function shows form for offer form
        :return: None
        """

        # if user isn't logged in
        if not self.__logged_in:
            messagebox.showerror("Error", "You are not logged in yet")
            return

        Client.clear_screen(self.root, self.menubar)

        self.var = StringVar()

        self.variable = StringVar()

        # widgets of the form
        self.right_frame = Frame(self.root, bd=2, bg='#F5F5F5', relief=SOLID, padx=10, pady=7, width=300, height=400)
        self.right_frame.columnconfigure(0, weight=10)

        # creating labels to design the form
        CTkLabel(self.root, text="Offer Room", text_font=("Roboto Medium", -30)).pack(pady=15)
        CTkLabel(self.right_frame, text="Enter Price", bg='#CCCCCC', text_font=("Roboto Medium", -24)).grid(row=0,
                                                                                                            column=0,
                                                                                                            sticky=W,
                                                                                                            pady=10)
        CTkLabel(self.right_frame, text="Enter Location", bg='#CCCCCC', text_font=("Roboto Medium", -24)).grid(row=1,
                                                                                                               column=0,
                                                                                                               sticky=W,
                                                                                                               pady=10)
        CTkLabel(self.right_frame, text="Enter Room Name", bg='#CCCCCC', text_font=("Roboto Medium", -24)).grid(row=2,
                                                                                                                column=0,
                                                                                                                sticky=W,
                                                                                                                pady=10)
        CTkLabel(self.right_frame, text="Enter Conditions", bg='#CCCCCC', text_font=("Roboto Medium", -24)).grid(row=3,
                                                                                                                 column=0,
                                                                                                                 sticky=W,
                                                                                                                 pady=10)
        CTkLabel(self.right_frame, text="Enter Dates (from - to)", bg='#CCCCCC', text_font=("Roboto Medium", -24)).grid(
            row=4, column=0, sticky=W,
            pady=10)

        # creating entries for the offer form
        self.offer_price = CTkEntry(self.right_frame, width=200, placeholder_text="Enter Price Per Day")
        self.offer_location = CTkEntry(self.right_frame, width=200, placeholder_text="Enter Location")
        self.offer_name = CTkEntry(self.right_frame, width=200, placeholder_text="Enter Name of the room")
        self.offer_condition = Text(self.right_frame, font=f, width=20, height=10)
        self.offer_dates = DateEntry(self.right_frame, font=f, locale='en_US', date_pattern='dd/mm/yyyy',
                                     mindate=datetime.now())
        self.offer_dates2 = DateEntry(self.right_frame, font=f, locale='en_US', date_pattern='dd/mm/yyyy',
                                      mindate=datetime.now())
        self.offer_btn = CTkButton(self.right_frame, width=200, fg_color="#E0E0E0", hover_color="#33A8FF",
                                   border_width=3, text_font=("Roboto Medium", -18), relief=SOLID, cursor='hand2',
                                   command=self.insert_offers, text="Offer")
        self.offer_btn.bind("<Return>", self.insert_offers)

        # widget placements
        self.offer_price.grid(row=0, column=1, pady=10, padx=20)
        self.offer_location.grid(row=1, column=1, pady=10, padx=20)
        self.offer_name.grid(row=2, column=1, pady=10, padx=20)
        self.offer_condition.grid(row=3, column=1, pady=10, padx=20)
        self.offer_dates.grid(row=4, column=1, pady=10, padx=20)
        self.offer_dates2.grid(row=5, column=1, pady=10, padx=20)
        self.offer_btn.grid(row=7, column=1, pady=10, padx=20)

        # image button
        self.offer_image = CTkButton(self.right_frame, width=200, text='Image', relief=SOLID, cursor='hand2',
                                     command=self.addfile, fg_color="#E0E0E0", hover_color="#33A8FF", border_width=3,
                                     text_font=("Roboto Medium", -18))
        self.offer_image.grid(row=7, column=0, pady=10, padx=20)

        self.message = CTkLabel(self.root, text_font=("Roboto Medium", -21), bg='white', text="")

        # widget placements
        self.right_frame.pack(pady=5)
        self.message.pack(pady=5)

    def addfile(self):
        """
        function adds images for room offer
        :return: None
        """

        # opening task window for choosing file
        self.root.attributes('-topmost', False)
        image_formats = (("PNG", "*.png"), ("JPG", "*.jpg"))
        file_path_list = askopenfilenames(filetypes=image_formats, initialdir="/",
                                          title='Please select a picture for the room')

        if not file_path_list:

            # handling errors
            self.filenames = None
            messagebox.showerror("Error", "You must choose an image")
            return

        # appending image paths to list
        self.image_names = []
        self.paths = []
        for file_path in file_path_list:
            self.image_names.append(file_path[file_path.rfind("/") + 1:])
            self.paths.append(file_path)

        # showing thank you message
        self.message.config(text="Thank you for the images", bg='#CCCCCC')
        self.root.attributes('-topmost', True)

    def insert_offers(self):
        """
        function inserts a new offer into the 'offers' table
        :return: None
        """

        # if user has already offered
        if self.already_offered >= 1:
            messagebox.showerror("Error", "You have already offered")
            return

        # sending images to server for it to broadcast
        # also sending the names of the images to save in directory
        image_bytes = []
        for path in self.paths:
            with open(path, "rb") as image:
                self.image_bytes = image.read()
                image_bytes.append(self.image_bytes)
                self.client.send(f"NAME {path}".encode())
                self.client.send(self.image_bytes)

        # saving the images offered on the directory of the map
        for index, filename in enumerate(self.image_names):
            with open(PATH + "\\map_images" + "\\" + filename, "wb") as f:
                f.write(image_bytes[index])

        # creating regex patterns to check the entries of the form
        # checking entries
        check_counter = 0
        price_regex = r"[1-9,]"
        location_regex = r"\d{2,},\d{2,}"
        time_regex = r"[\d]{1,2}/[\d]{1,2}/[\d]{4}"
        warn = ""
        if self.offer_price.get() == "":
            warn = "Price can't be empty"
        else:
            check_counter += 1

        if self.offer_location.get() == "":
            warn = "Location can't be empty"
        elif not re.search(price_regex, self.offer_price.get()):
            warn = "Not valid email"
        else:
            check_counter += 1

        if self.offer_name.get() == "":
            warn = "Room name can't be empty"
        else:
            check_counter += 1

        if self.offer_dates.get() == "":
            warn = "Date can't be empty"
        elif not re.search(time_regex, self.offer_dates.get()):
            warn = "not void date"
        else:
            check_counter += 1

        if self.offer_dates2.get() == "":
            warn = "Date can't be empty"
        elif not re.search(time_regex, self.offer_dates2.get()):
            warn = "not void date"
        else:
            check_counter += 1

        if self.offer_condition.get(1.0, END) == "":
            warn = "Conditions can't be empty"
        else:
            check_counter += 1

        if check_counter == 6:
            try:

                # creating id's for offer and room
                offer_id = rand.randint(1000000, 10000000)
                room_id = rand.randint(100, 1000)
                self.client.send(pickle.dumps(["#FETCH USER ID#", self.uemail]))
                self.wait_for_server_to_respond(self.user_data, 2)

                # inserting to database 'offers', then sending to server in order to show a new marker in the map
                insert = [offer_id, self.user_data[2], room_id, self.offer_price.get(),
                          f"{','.join([i for i in self.image_names])}",
                          f"{str(self.offer_dates.get_date()).replace('-', '/')} - {str(self.offer_dates2.get_date()).replace('-', '/')}",
                          self.offer_condition.get(1.0, END), self.offer_name.get(),
                          self.offer_location.get(), "0"]
                self.client.send(pickle.dumps(["#UPDATE DATA BASE# offers", insert]))
                self.client.send(pickle.dumps(["#ADD NEW POSITION#", self.offer_location.get(), self.offer_name.get()]))

                # if offer has saved, cleaning entries, showing pop up message
                messagebox.showinfo('confirmation', 'Offer Saved')
                self.clean_entries([self.offer_price, self.offer_name, self.offer_dates,
                                    self.offer_location, self.offer_dates2])
                self.offer_condition.delete(1.0, END)
                self.offer_name.delete(0, END)

                self.message.config(text="", bg="white")

                self.already_offered += 1

            except Exception as ep:

                # handling errors
                messagebox.showerror('', ep)
        else:
            messagebox.showerror('Error', warn)

    @staticmethod
    def clear_screen(root, menubar):
        """
        The function clears the screen out of any widget expect the menu
        """
        for widget in root.winfo_children():
            if widget is not menubar:
                widget.destroy()

    def wait_for_server_to_respond(self, lst, index):
        """
        function wait's till the server responds for a message
        :param lst: the lst of values
        :param index: the index in the list
        :return: None
        """

        while lst[index] is None:
            pass
        return

    def insert_record(self):
        """
        function inserts record and updates the database
        :return: None
        """

        # creating regex pattern for email, password
        # checking for all the entries
        check_counter = 0
        email_regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        password_regex = r'^[A-Za-z0-9@#$%^&+=]{5,}$'
        warn = ""
        if self.register_name.get() == "":
            warn = "Name can't be empty"
        else:
            check_counter += 1

        if self.register_email.get() == "":
            warn = "Email can't be empty"
        elif not re.search(email_regex, self.register_email.get()):
            warn = "Not valid email"
        else:
            check_counter += 1

        if self.register_mobile.get() == "":
            warn = "id be empty"
        elif len(self.register_mobile.get()) < 9 or any(i.isalpha() for i in self.register_mobile.get()):
            warn = "not valid id"
        else:
            check_counter += 1

        if self.variable.get() == "":
            warn = "Select Country"
        else:
            check_counter += 1

        if self.register_pwd.get() == "":
            warn = "Password can't be empty"
        elif not re.search(password_regex, self.register_pwd.get()):
            warn = "Password isn't valid"
        else:
            check_counter += 1

        if self.pwd_again.get() == "":
            warn = "Re-enter password can't be empty"
        else:
            check_counter += 1

        if self.register_pwd.get() != self.pwd_again.get():
            warn = "Passwords didn't match!"
        else:
            check_counter += 1

        if check_counter == 7:

            try:

                # if user already exists
                self.client.send(pickle.dumps(["#CHECK FOR USER#", self.register_mobile.get()]))
                self.wait_for_server_to_respond(self.user_data, 4)

                # if not, inserting a new record (user) to the database 'record'
                # clearing all the entries
                if not self.user_data[4]:
                    self.client.send(pickle.dumps(
                        ["#UPDATE DATA BASE# record", [int(self.register_mobile.get()), self.register_email.get(),
                                                       self.register_name.get(), self.variable.get(),
                                                       self.register_pwd.get(), "False"]]))
                    messagebox.showinfo('confirmation', 'Record Saved')
                    self.clean_entries([self.register_mobile, self.register_email, self.register_name,
                                        self.register_pwd, self.pwd_again])
                    self.var.set("")
                    self.variable.set("")
                else:
                    messagebox.showerror("Error", "user already exists")

                self.user_exists = None
                return

            except Exception as ep:

                # handling errors
                messagebox.showerror('', ep)
        else:
            messagebox.showerror('Error', warn)

    def clean_entries(self, entries):
        """
        function cleans entry's content from the screen
        :param entries: the entries to clean
        :return: None
        """
        for i in entries:
            i.delete(0, END)

    def login_response(self):
        """
        function checks for login request
        :return:
        """

        # creating a regex pattern for email
        email_regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

        # if user is already logged in
        if self.__logged_in:
            messagebox.showinfo("info", "You are already logged in", icon="info")
            return

        # sending login request
        self.client.send("#LOGIN REQUEST#".encode())
        self.wait_for_server_to_respond(self.user_data, 0)
        self.wait_for_server_to_respond(self.user_data, 1)

        # getting email and password
        self.uemail = self.email_tf.get()
        upwd = self.pwd_tf.get()
        self.email_tf.delete(0, END)
        self.pwd_tf.delete(0, END)

        # checking for the entries
        check_counter = 0
        if self.uemail == "":
            warn = "Username can't be empty"
        else:
            if not re.search(email_regex, self.uemail):
                warn = "Not valid email"
            else:
                check_counter += 1
        if upwd == "":
            warn = "Password can't be empty"
        else:
            check_counter += 1

        if check_counter == 2:

            # if user is in record table
            if self.uemail in self.user_data[0] and upwd in self.user_data[1]:

                # sending to check if admin
                self.client.send(pickle.dumps(["#ADMIN REQUEST#", self.uemail]))
                self.wait_for_server_to_respond(self.admin_data, 0)

                if self.admin_data[0]:

                    # congratulating, getting user's name and checking for any end of purchases
                    self.__logged_in = True
                    messagebox.showinfo('Login Status', 'Logged in Successfully!\n'
                                                        'You are now admin')

                    self.client.send(pickle.dumps(["#LOGGED IN#", self.uemail]))

                    # moving now admin user to the admin home screen
                    self.start_root()

                    self.client.send(pickle.dumps(["#FETCH NAME BY EMAIL#", self.uemail]))
                    self.wait_for_server_to_respond(self.user_data, 5)

                    self.client.send(pickle.dumps(["#CHECK FOR DATE#", self.uemail]))

                # handling errors
                else:
                    messagebox.showerror('Login Status', 'invalid username or password\n'
                                                         'you are not an admin (sorry)')
                    return

            else:
                messagebox.showerror('Login Status', 'invalid username or password')
                return
        else:

            # handling errors
            messagebox.showerror('Error', warn)
            return

        # starting admin root
        self.start_root()

    def clean_root(self):
        """
        The function clears the screen out of any widget
        :return: None
        """

        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login(self):
        """
        function shows login form
        :return: None
        """

        Client.clear_screen(self.root, self.menubar)

        # creating frame for image and labels of the form
        bigger_frame = Frame(self.root, width=700, height=700, bg="white")

        # creating the logo image for the login form
        CTkLabel(bigger_frame, text="Login", text_font=("Roboto Medium", -40), bg="white").pack(pady=30)
        img = ImageTk.PhotoImage(Image.open("airbnb_images//airbnb_sign_up2.png").resize((350, 290)))
        login_lable = Label(bigger_frame, image=img, borderwidth=0, bg='white')
        login_lable.image = img
        login_lable.pack(side="left", expand=1, fill=BOTH, padx=20)

        # creating the labels to design the login form
        login_frame = Frame(bigger_frame, bd=2, bg="#F5F5F5", relief=SOLID, padx=10, pady=10, height=300)
        CTkLabel(login_frame, text="Enter Email", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=0, column=0,
                                                                                                       sticky=W,
                                                                                                       pady=10)
        CTkLabel(login_frame, text="Enter Password", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=1,
                                                                                                          column=0,
                                                                                                          pady=10)

        # if user doesn't have an account, offering him/her to sign up
        CTkLabel(login_frame, text="Don't have an account? Sign Up!!", bg="#F5F5F5",
                 text_font=("Roboto Medium", -18)).grid(row=2,
                                                        columnspan=2,
                                                        pady=10,
                                                        padx=20)

        # binding label to 'show_registration' function
        w = Label(login_frame, text="Sign Up", font=f, fg="green")
        w.grid(row=3, columnspan=2, pady=10, padx=20)
        w.bind("<Button-1>", lambda e: self.show_registration())

        # creating the entries for the form
        self.email_tf = CTkEntry(login_frame, width=200, placeholder_text="Enter Email")
        self.pwd_tf = CTkEntry(login_frame, show='*', width=200, placeholder_text="Enter Password")
        self.login_btn = CTkButton(login_frame, width=200, text='Login', relief=SOLID, cursor='hand2',
                                   fg_color="#E0E0E0", hover_color="#33A8FF", border_width=3,
                                   text_font=("Roboto Medium", -18),
                                   command=self.login_response)

        # widgets placement
        self.email_tf.grid(row=0, column=1, pady=10, padx=20)
        self.pwd_tf.grid(row=1, column=1, pady=10, padx=20)
        self.login_btn.grid(row=4, pady=(20, 20), column=1)

        login_frame.pack(side="left", pady=70)
        bigger_frame.pack(padx=50, pady=50)

    def show_registration(self):
        """
        function shows registration form for the client
        :return: None
        """

        Client.clear_screen(self.root, self.menubar, self.on_closing)

        if not self.__logged_in:  # guest
            lbl = CTkLabel(self.root, text="Hello Guest", bg="white", text_font=("Roboto Medium", -30))
            lbl.pack(anchor='nw', padx=20, pady=20)

        bigger_frame = Frame(self.root, width=700, height=700, bg="white")

        self.var = StringVar()

        # creating variables for the form
        countries = []
        self.variable = StringVar()
        world = open('countries.txt', 'r')
        for country in world:
            country = country.rstrip('\n')
            countries.append(country)
        self.variable.set(countries[0])

        # creating the images for the form
        left_side_frame = Frame(bigger_frame, bg="#F5F5F5")
        left_side_frame.pack(side="left", padx=20)
        img = ImageTk.PhotoImage(Image.open("airbnb_images//airbnb_sign_up2.png").resize((390, 300)))
        login_lable = CTkLabel(left_side_frame, image=img, borderwidth=0, bg='white')
        login_lable.image = img
        login_lable.pack()
        CTkLabel(left_side_frame, text="Welcome to my airBnB website\n Here you can purchase any room\n"
                                       "Where ever you would like", text_font=("Roboto Medium", -20),
                 bg="#F5F5F5").pack(pady=(15, 0))

        # creating labels for the form
        self.right_frame = Frame(bigger_frame, bd=2, bg='#F5F5F5', relief=SOLID, padx=10, pady=7)
        CTkLabel(self.root, text="Registration", text_font=("Roboto Medium", -30), bg="white").pack(pady=30)
        CTkLabel(self.right_frame, text="Enter Name", bg='#F5F5F5', text_font=("Roboto Medium", -20)).grid(row=0,
                                                                                                           column=0,
                                                                                                           sticky=W,
                                                                                                           pady=10)
        CTkLabel(self.right_frame, text="Enter Email", bg='#F5F5F5', text_font=("Roboto Medium", -20)).grid(row=1,
                                                                                                            column=0,
                                                                                                            sticky=W,
                                                                                                            pady=10)
        CTkLabel(self.right_frame, text="Enter id", bg='#F5F5F5', text_font=("Roboto Medium", -20)).grid(row=2,
                                                                                                         column=0,
                                                                                                         sticky=W,
                                                                                                         pady=10)
        CTkLabel(self.right_frame, text="Select Country", bg='#F5F5F5', text_font=("Roboto Medium", -20)).grid(row=3,
                                                                                                               column=0,
                                                                                                               sticky=W,
                                                                                                               pady=10)
        CTkLabel(self.right_frame, text="Enter Password", bg='#F5F5F5', text_font=("Roboto Medium", -20)).grid(row=4,
                                                                                                               column=0,
                                                                                                               sticky=W,
                                                                                                               pady=10)
        CTkLabel(self.right_frame, text="Re-Enter Password", bg='#F5F5F5', text_font=("Roboto Medium", -20)).grid(row=5,
                                                                                                                  column=0,
                                                                                                                  sticky=W,
                                                                                                                  pady=10)
        # creating the entries for the form
        self.register_name = CTkEntry(self.right_frame, width=200, placeholder_text="Enter Name")
        self.register_email = CTkEntry(self.right_frame, width=200, placeholder_text="Enter Email")
        self.register_mobile = CTkEntry(self.right_frame, width=200, placeholder_text="Enter Id")
        self.credit = CTkEntry(self.right_frame, textvariable=self.var, width=200)
        self.register_country = OptionMenu(self.right_frame, self.variable, *countries)
        self.register_country.config(width=15, font=('Times', 12))
        self.register_pwd = CTkEntry(self.right_frame, show='*', width=200, placeholder_text="Enter Password")
        self.pwd_again = CTkEntry(self.right_frame, show='*', width=200, placeholder_text="Re-Enter Password")
        self.register_btn = CTkButton(self.right_frame, width=150, text='Register', text_font=("Roboto Medium", -20),
                                      relief=SOLID, cursor='hand2',
                                      fg_color="#E0E0E0", border_width=3,
                                      hover_color="#33A8FF",
                                      command=self.insert_record)
        self.register_btn.bind()

        # widgets placements
        self.register_name.grid(row=0, column=1, pady=10, padx=20)
        self.register_email.grid(row=1, column=1, pady=10, padx=20)
        self.register_mobile.grid(row=2, column=1, pady=10, padx=20)
        self.register_country.grid(row=3, column=1, pady=10, padx=20)
        self.register_pwd.grid(row=4, column=1, pady=10, padx=20)
        self.pwd_again.grid(row=5, column=1, pady=10, padx=20)
        self.register_btn.grid(row=6, column=1, pady=10, padx=20)
        CTkLabel(self.right_frame, text="Already have an account?", text_font=("Roboto Medium", -20)).grid(row=7,
                                                                                                           columnspan=2,
                                                                                                           padx=20,
                                                                                                           pady=10)

        # creating 'log_in' label and binding it to
        w = Label(self.right_frame, text="Log In", font=f, fg="green")
        w.grid(row=8, columnspan=2, padx=20, pady=10)
        w.bind("<Button-1>", lambda e: self.show_login())
        self.right_frame.pack(side="left")
        bigger_frame.pack(anchor="center")


if __name__ == "__main__":

    # starting the admin
    admin = Admin()
    admin.connect()
