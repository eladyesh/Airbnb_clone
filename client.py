# importing the required modules
import pickle
from socket import *
from threading import Thread
from tkinter import *
from tkinter import filedialog
from tkinter.filedialog import askopenfilenames
from tkinter.scrolledtext import ScrolledText
import geocoder
import imageio
from tkcalendar import *
import tkinter.font as tkFont
import ssl
import warnings
from maps.map import App
from PIL import ImageTk
from PIL import Image
import datetime
import random as rand
from data_base.manage_data_base import *
import re
import os.path
from tkinter import ttk
import maps.map as map
from customtkinter import *
from datetime import datetime
from contextlib import suppress
from tkvideo import tkvideo
import matplotlib.pyplot as plt
from skimage import data, io

# defining font and computer's path to the project
f = ('Open Sans', 16)
PATH = os.path.dirname(os.path.realpath(__file__))


class Client:
    """
    Client class connects to server server, and manages also tkinter
    involved with communicating with the server
    """

    def __init__(self):

        # ignoring deprecation warning
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # setting up client socket, wrapping with ssl
        self.client = ssl.wrap_socket(socket(AF_INET, SOCK_STREAM), server_side=False)
        self._BUFFER = 1024
        if len(gethostbyname_ex(gethostname())[-1]) > 1:
            self.__HOST = gethostbyname_ex(gethostname())[-1][0]
        else:
            self.__HOST = gethostbyname_ex(gethostname())[-1][-1]
        self.__HOST = "172.16.2.74"

        self._ADDR = (self.__HOST, 50002)

        # initiating important variables to avoid errors
        self.event_handler = Event()
        self.__logged_in = False
        self.map = None
        self.filenames = None
        self._save_image = b""
        self.start_image = False
        self.ratings = dict({})
        self.map_data = [None for i in range(10)]
        self.admin_data = [None]  # is admin
        self.already_offered, self.already_registered = 0, 0
        self.user_data = [None for i in range(
            10)]  # [self.login_users, self.login_passwords, self.user_id, self.login_purchases, self.user_exists, self.offers]
        self.room_data = [None for i in range(5)]  # [room name by offer_id, room average rating, room rating]
        self.name = None
        self.updated_offers = None
        self.user_id = None
        self.root = None
        self.attractions = []
        self.video_label = None
        self.server_time = datetime.now().strftime("%Y/%m/%d")
        self.paths = None
        self.disputed_id = []

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

                # excepting image bytes from server
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
                try:
                    pickle_data = pickle.loads(data)
                except (EOFError, ValueError, OverflowError, MemoryError):
                    raise

                # if the data received is type dictionary
                if type(pickle_data) == dict:

                    self.offers = pickle.loads(data)

                    if self.map is not None:
                        # updating markers on the map
                        self.updated_offers = pickle_data
                        self.map.update_markers(self.updated_offers)
                        continue

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

                    # if the room names were sent
                    elif pickle_data[0] == "#ROOM NAMES#":
                        self.map_data[0] = pickle_data[1]
                        continue

                    # if user is admin
                    elif pickle_data[0] == "#ADMIN ANSWER#":
                        self.admin_data[0] = pickle_data[1]

                    # if offers ordered by the price were sent
                    elif pickle_data[0] == "#OFFERS ORDERED BY PRICE#":
                        self.map_data[1] = pickle_data[1]

                    # if location the room names was sent
                    elif pickle_data[0] == "#LOCATION BY ROOM NAMES#":
                        self.map_data[2] = pickle_data[1]

                    # if data on the offer was sent
                    elif pickle_data[0] == "#INFORMATION ON OFFER#":
                        self.map_data[3] = pickle_data[1]

                    # if an offer by purchase id was sent
                    elif pickle_data[0] == "#OFFER BY PURCHASE ID#":
                        self.map_data[4] = pickle_data[1]

                    # if a purchase by offer id was sent
                    elif pickle_data[0] == "#PURCHASE BY OFFER ID#":
                        self.map_data[5] = pickle_data[1]

                    # if offers that are ordered by their rating were sent
                    elif pickle_data[0] == "#OFFERS ORDERED BY AVERAGE RATING#":
                        self.map_data[6] = pickle_data[1]

                    # if a room name by offer id was sent
                    elif pickle_data[0] == "#ROOM NAME BY OFFER ID#":
                        self.room_data[0] = pickle_data[1]

                    # if a new marker was sent
                    elif pickle_data[0] == "#NEW MARKER#" and self.map is not None:
                        self.map.add_marker(pickle_data[1], pickle_data[2], pickle_data[3])
                        continue

                    # if name by email in 'record' table was sent
                    elif pickle_data[0] == "#NAME BY EMAIL#":
                        self.user_data[5] = pickle_data[1]

                    # if time is up to date on a certain purchase
                    elif pickle_data[0] == "#TIME IS UP FOR PURCHASE#":
                        messagebox.showinfo("info", f"Your purchase duration was up for dates\n"
                                                    f"{pickle_data[1]}\nPlease rate")

                    # if an offer by user email was sent
                    elif pickle_data[0] == "#OFFER BY EMAIL#":
                        self.user_data[6] = pickle_data[1]

                    # if a rating was sent by offer id
                    elif pickle_data[0] == "#RATING BY OFFER ID#":
                        self.room_data[1] = pickle_data[1]

                    # if a review was sent by offer id
                    elif pickle_data[0] == "#REVIEW BY OFFER ID#":
                        self.room_data[2] = pickle_data[1]

                    # if a new attraction was sent, updating the map
                    elif pickle_data[0] == "#NEW ATTRACTION#":

                        if self.map is not None:
                            self.map.add_attraction(*pickle_data[1])
                        else:
                            self.attractions.append(pickle_data[1])

                    # if another user disputed an offer
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

            except pickle.UnpicklingError:

                # handling data that is doesn't need to be pickled
                try:
                    data = data.decode()
                except UnicodeDecodeError:
                    pass

                if data == "":
                    self.user_quit()

                # if admin changed the date
                try:
                    if data.find("/") != -1 and len(data) < 14:
                        self.server_time = data

                        # updating the server time
                        if self.map is not None:
                            self.map.update_server_time(self.server_time)

                except TypeError:
                    pass

                # if user already exists
                if data == "#USER ALREADY EXISTS#":
                    self.user_data[4] = True

                # if user doesn't exists
                elif data == "#USER DOESN'T EXISTS#":
                    self.user_data[4] = False

                # if client have already rated
                elif data == "#AlREADY RATED#":
                    messagebox.showerror("Error", "You have already rated")

                # if a client was made admin
                elif data == "#BECOME ADMIN#":
                    messagebox.showinfo("WOW!!!!", "Seems like you were promoted to be admin\n"
                                                   "You can now proceed to go to admin file", icon="info")

            except (EOFError, OSError, ssl.SSLEOFError):

                # if there is any connections problems with the server, making user exit
                self.user_quit()
                break

    def log_out(self):
        """
        function logs out of system
        :return: None
        """

        if self.__logged_in:
            self.__logged_in = False
            messagebox.showinfo("info", "You have logged out")
        else:
            messagebox.showerror("Error", "You are not logged in")

        self.user_data[5] = None
        self.show_home_screen()
        return

    def show_home_screen(self):
        """
        function shows the home screen for the client
        :return:
        """

        Client.clear_screen(self.root, self.menubar, self.on_closing)

        # creating a label and an image to begin the trivia
        self.begin = Label(self.root, text="Hello There!!!\n\nWelcome to my airBnB "
                                           "", font=self.lbl_font,
                           bg='white')
        self.begin.pack(expand="Yes", fill=BOTH, anchor=CENTER)
        self.name = StringVar()

        # showing video
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

    def connect(self):
        """
        function shows loading screen
        :return: None
        """

        # creating the root, with geometry and airbnb icon
        self.root = Tk()
        self.root.iconphoto(False, PhotoImage(file=PATH + r"\\airbnb_images\\airbnb_sign_up2.png"))
        self.root.title("AirBnb")
        self.root.minsize(1000, 800)
        self.root.config(bg='white')
        x = 1000
        y = 800
        self.root.geometry(
            f"{str(x)}x{str(y)}+{int(self.root.winfo_screenwidth() / 2 - x / 2)}+{int(self.root.winfo_screenheight() / 2 - y / 2)}")
        self.root.deiconify()

        # setting picture
        self.img = ImageTk.PhotoImage(Image.open(PATH + r"\\airbnb_images\\airbnb_sign_up2.png"))
        self.begin_lable = Label(self.root, image=self.img, borderwidth=0)
        self.begin_lable.image = self.img
        self.begin_lable.pack(pady=30)

        # setting loading screen, trying to connect to server
        CTkLabel(self.root, text="Connecting to the server now...", text_color="black",
                 text_font=("Open Suns", -30)).pack(pady=30)
        try:
            self.root.after(100, self.connect_to_server)
            self.root.mainloop()
        except TclError:
            pass

    def connect_to_server(self):
        """
        function connects to server socket
        :return: None
        """

        while 1:

            try:
                self.client.connect(self._ADDR)
                print("----Connected to server successfully----")
                break
            except (ConnectionRefusedError, TimeoutError):
                continue

        # starting the root
        self.start_root()

    def start_root(self):
        """
        function starts the tkinter root for the user
        :return:  None
        """

        # clearing screen, defining root
        Client.clear_screen(self.root, None, None)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # creating menu
        self.menubar = Menu(self.root)

        # creating the submenu for disputes
        self.sub_menu = Menu(self.menubar, tearoff=0)
        self.sub_menu.add_command(label='Dispute Purchases', command=self.show_cancel_purchases)
        self.sub_menu.add_command(label='Dispute Offers', command=self.show_cancel_offers)

        # creating the user menu
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Register", command=self.show_registration)
        self.filemenu.add_command(label="Home Page", command=self.show_home_screen)
        self.filemenu.add_command(label="Sign in", command=self.show_login)
        self.filemenu.add_command(label="See offers", command=self.open_map)
        self.filemenu.add_command(label="Offer Room", command=self.offer_room)
        self.filemenu.add_command(label="Rate Purchases", command=self.show_purchases)
        self.filemenu.add_command(label="Convert Address", command=self.convert_address_to_location)

        # creating submenu for disputes
        self.filemenu.add_separator()
        self.filemenu.add_cascade(
            label="Dispute",
            menu=self.sub_menu
        )
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_closing)
        self.menubar.add_cascade(label="User menu", menu=self.filemenu)

        self.root.config(menu=self.menubar)

        self.lbl_font = tkFont.Font(family="Sans-serif", size=20, weight=tkFont.BOLD)

        # creating the receive thread
        self.receive_thread = Thread(target=self.recieve)
        self.receive_thread.start()

        # showing the home screen
        self.show_home_screen()
        self.root.resizable(False, False)

        self.root.mainloop()

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
        function sends to server what to credential to change and the data on the user
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
        CTkLabel(bigger_frame, text="Change Password", text_font=("Roboto Medium", -40), bg="white").pack(pady=30)
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
        function shows form for change email
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

    def convert_address_to_location(self):
        """
        function converts address to location (x,y) for the user to enter when
        :return: None
        """

        # opening the root
        self.location_root = Toplevel(self.root)
        self.location_root.resizable(False, False)
        frame = Frame(self.location_root)

        # widgets and setting placements
        CTkLabel(self.location_root, text=f"Please enter an address\n\n", bg='#F5F5F5',
                 text_font=("Roboto Medium", -30)).pack(pady=10)

        # setting widgets
        self.loc = CTkEntry(frame, width=200, placeholder_text="Enter Address")
        self.loc.pack(side="left", padx=5)

        # calculate button
        self.w = CTkButton(frame, fg_color="#E0E0E0", hover_color="#33A8FF",
                           border_width=3, text_font=("Roboto Medium", -18), relief=SOLID, cursor='hand2',
                           text="Submit",
                           command=lambda: self.calculate_address(self.loc.get()))
        self.w.pack(side="left", padx=5)

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

    def on_closing(self):
        """
        function makes sure closing window goes without errors
        :return: None
        """

        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            try:
                self.root.destroy()
                self.client.close()
            except:
                pass

            messagebox.showinfo("Success", "Thank you for being with us", icon="info")

    def show_cancel_purchases(self):
        """
        function creates a table tree for purchases client has made
        :return: None
        """

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

        # showing note to user
        f = CTkFrame(self.root, corner_radius=0, border_width=3, bg="white")
        CTkLabel(f, text=f"Note\n\nThe purchases that are shown here are only the ones that\n"
                         f"their starting date is at least 2 days from today .\n"
                         f"Please take that into consideration 🙏🙏🙏🙏",
                 text_font=("Roboto Medium", -15)).pack(pady=3)
        f.pack(pady=3)

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

            d = datetime.strptime(i[2].split("-")[0][:-1], '%Y/%m/%d')
            if int(str(d - datetime.today())[0]) >= 2:
                # inserting the data in Treeview widget
                self.tree.insert('', 'end', values=(i[0], i[1],
                                                    i[2].split("-")[0], i[2].split("-")[1], i[3]))

        # binding each element to cancel_purchases function
        self.tree.bind("<Double-1>", lambda *args: self.cancel_purchases())

        self.tree.pack(pady=50, fill=X)

    def show_cancel_offers(self):
        """
        function creates a tree for offers client has made so that he/she can dispute any one of them
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
        function shows user his/her purchases for him/her to rate them
        :return:
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

        self.switch.pack(side="left", padx=50)

        btn_frame.pack(side="bottom", pady=10)

    def update_rating(self, data, var, rating_root, item_chosen, review, is_anonymous):
        """
        function updates 'ratings' data base
        :param data: data on purchase
        :param var:
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

        if self.updated_offers is not None:
            self.map.update_markers(self.updated_offers)

        # events of the map
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
        function sends to server that purchase id that he/she has purchased from the map
        :return: None
        """
        self.client.send(pickle.dumps(["#PURCHASE ID#", self.map.purchase_id]))

    def offer_room(self):
        """
        function shows form for offer form
        :return: None
        """

        # if user not logged in
        if not self.__logged_in:
            messagebox.showerror("Error", "You are not logged in yet")
            self.show_home_screen()
            return

        Client.clear_screen(self.root, self.menubar)

        self.var = StringVar()
        self.variable = StringVar()

        # widgets of the form
        self.right_frame = Frame(self.root, bd=2, bg='#F5F5F5', relief=SOLID, padx=10, pady=7, width=300, height=400)
        self.right_frame.columnconfigure(0, weight=10)

        # creating labels for form
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

        # creating entries
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

        # widgets placements
        self.offer_price.grid(row=0, column=1, pady=10, padx=20)
        self.offer_location.grid(row=1, column=1, pady=10, padx=20)
        self.offer_name.grid(row=2, column=1, pady=10, padx=20)
        self.offer_condition.grid(row=3, column=1, pady=10, padx=20)
        self.offer_dates.grid(row=4, column=1, pady=10, padx=20)
        self.offer_dates2.grid(row=5, column=1, pady=10, padx=20)
        self.offer_btn.grid(row=7, column=1, pady=10, padx=20)

        # packing widgets, creating button for submit
        self.offer_image = CTkButton(self.right_frame, width=200, text='Image', relief=SOLID, cursor='hand2',
                                     command=self.addfile, fg_color="#E0E0E0", hover_color="#33A8FF", border_width=3,
                                     text_font=("Roboto Medium", -18))
        self.offer_image.grid(row=7, column=0, pady=10, padx=20)

        self.message = CTkLabel(self.root, text_font=("Roboto Medium", -21), bg='white', text="")

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
            self.filenames = None
            messagebox.showerror("Error", "You must choose an image")
            return

        # appending image paths to list
        self.image_names = []
        self.paths = []
        for file_path in file_path_list:
            self.image_names.append(file_path[file_path.rfind("/") + 1:])
            self.paths.append(file_path)

        # showing 'thank you' message
        self.message.config(text="Thank you for the images", bg='#CCCCCC')
        self.root.attributes('-topmost', True)

    def insert_offers(self):
        """
        function inserts offer into database and updates the relevant places
        (for instance, sending and saving pictures in the relevant directory)
        :return: None
        """

        # if user has already offered
        if self.already_offered >= 1:
            messagebox.showerror("Error", "You have already offered")
            return

        if self.paths is None:
            messagebox.showwarning("Error", "You must choose images", icon="warning")
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

        # creating regex patterns for price, location, time
        # checking for all the entries
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
            warn = "Not valid price"
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

                # setting id's for offer, room
                offer_id = rand.randint(1000000, 10000000)
                room_id = rand.randint(100, 1000)
                self.client.send(pickle.dumps(["#FETCH USER ID#", self.uemail]))
                self.wait_for_server_to_respond(self.user_data, 2)

                # inserting to database 'offers', then sending to server in order to show a new marker in the map
                insert = [offer_id, self.user_data[2], room_id, self.offer_price.get(),
                          f"{','.join([i for i in self.image_names])}",
                          f"{str(self.offer_dates.get_date()).replace('-', '/')} - {str(self.offer_dates2.get_date()).replace('-', '/')}",
                          self.offer_condition.get(1.0, END), self.offer_name.get(),
                          self.offer_location.get()]
                self.client.send(pickle.dumps(["#UPDATE DATA BASE# offers", insert]))
                self.client.send(
                    pickle.dumps(["#ADD NEW POSITION#", self.offer_location.get(), self.offer_name.get(), offer_id]))

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
    def clear_screen(root, menubar=None, func=None):
        """
        The function clears the screen out of any widget expect the menu
        """

        if menubar is None:
            for widget in root.winfo_children():
                widget.destroy()

        else:
            for widget in root.winfo_children():
                if widget is not menubar:
                    widget.destroy()

        if func is not None:
            root.protocol("WM_DELETE_WINDOW", func)

    def wait_for_server_to_respond(self, lst, index):
        """
        function waits till the server responds for a message
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

                # if not, inserting a new record
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

        # if user is already logged in
        if self.__logged_in:
            messagebox.showinfo("info", "You are already logged in")
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
            check_counter += 1
        if upwd == "":
            warn = "Password can't be empty"
        else:
            check_counter += 1

        if check_counter == 2:

            # if user is in the 'record' table
            if self.uemail in self.user_data[0] and upwd in self.user_data[1]:

                # making user logged in
                # if admin, showing to user
                self.__logged_in = True

                self.client.send(pickle.dumps(["#ADMIN REQUEST#", self.uemail]))
                self.wait_for_server_to_respond(self.admin_data, 0)

                if self.admin_data[0]:
                    messagebox.showinfo('Login Status', 'Wow!\n'
                                                        'Seems to me like you are admin\n'
                                                        'You can login to admin file with\n'
                                                        f'Email: {self.uemail}\n'
                                                        f'Password: {upwd}', icon="info")

                else:
                    messagebox.showinfo('Login Status', 'Logged in Successfully!')

                # adding log out option in menu
                self.filemenu.add_command(label="Log out", command=self.log_out)
                self.client.send(pickle.dumps(["#LOGGED IN#", self.uemail]))

                # getting the name of user
                self.client.send(pickle.dumps(["#FETCH NAME BY EMAIL#", self.uemail]))
                self.wait_for_server_to_respond(self.user_data, 5)
                self.client.send(pickle.dumps(["#CHECK FOR DATE#", self.uemail]))

                # adding option to change credentials
                self.change_menu = Menu(self.menubar, tearoff=0)
                self.change_menu.add_command(label="Change Email", command=self.change_email)
                self.change_menu.add_command(label="Change Password", command=self.change_password)
                self.change_menu.add_command(label="Change Name", command=self.change_name)
                self.menubar.add_cascade(label="Change Credentials", menu=self.change_menu)
                self.show_home_screen()
                return

            else:
                messagebox.showerror('Login Status', 'invalid username or password')
        else:

            # handling errors
            messagebox.showerror('Error', warn)

    def show_login(self):
        """
        function shows login form for the client
        :return: None
        """

        Client.clear_screen(self.root, self.menubar, self.on_closing)

        bigger_frame = Frame(self.root, width=700, height=700, bg="white")

        # setting images and widgets
        CTkLabel(bigger_frame, text="Login", text_font=("Roboto Medium", -40), bg="white").pack(pady=30)
        img = ImageTk.PhotoImage(Image.open("airbnb_images//airbnb_sign_up2.png").resize((350, 290)))
        login_lable = Label(bigger_frame, image=img, borderwidth=0, bg='white')
        login_lable.image = img
        login_lable.pack(side="left", expand=1, fill=BOTH, padx=20)

        # crating labels for form
        login_frame = Frame(bigger_frame, bd=2, bg="#F5F5F5", relief=SOLID, padx=10, pady=10, height=300)
        CTkLabel(login_frame, text="Enter Email", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=0, column=0,
                                                                                                       sticky=W,
                                                                                                       pady=10)
        CTkLabel(login_frame, text="Enter Password", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=1,
                                                                                                          column=0,
                                                                                                          pady=10)

        CTkLabel(login_frame, text="Don't have an account? Sign Up!!", bg="#F5F5F5",
                 text_font=("Roboto Medium", -18)).grid(row=2,
                                                        columnspan=2,
                                                        pady=10,
                                                        padx=20)

        w = Label(login_frame, text="Sign Up", font=f, fg="green")
        w.grid(row=3, columnspan=2, pady=10, padx=20)
        w.bind("<Button-1>", lambda e: self.show_registration())

        # creating login entries
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

        # packing and creating labels for the form
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

        # packing more widgets
        w = Label(self.right_frame, text="Log In", font=f, fg="green")
        w.grid(row=8, columnspan=2, padx=20, pady=10)
        w.bind("<Button-1>", lambda e: self.show_login())
        self.right_frame.pack(side="left")
        bigger_frame.pack(anchor="center")


if __name__ == "__main__":

    # starting the client
    c = Client()
    c.connect()
