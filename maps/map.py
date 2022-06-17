from tkinter import *
import _tkinter
from tkintermapview import TkinterMapView
from data_base.manage_data_base import *
from PIL import ImageTk
from PIL import Image
import random
from Event import Event
import threading
from tkcalendar import *
from datetime import datetime, timedelta
import sys
import pickle
import math
from threading import Thread
import time
from customtkinter import *
import re
import matplotlib.pyplot as plt
from skimage import io
from tkinter import ttk
import geocoder
from collections import Counter

f = ("Times", 14)
PATH = os.path.dirname(os.path.realpath(__file__))


def get_recent_orders():
    return App.recent_orders


class App:
    """
    Class opens the map for both user and admin, and shows the markers representing the offers
    """
    recent_orders = []

    def __init__(self, root, menubar, offers: dict, logged: bool, client, data: list, room_data: list, attractions: list,
                 server_time: str,
                 client_email=None, is_admin=None, admin_data=None):
        """
        function starts that map class
        :param root: root of the app
        :param menubar: menu bar of the app
        :param offers: the starting offers for the map
        :param logged: is user logged in
        :param client: the client opening the map
        :param data: the data of the map
        :param room_data: the data of the room
        :param attractions: the attrations of the
        :param server_time: the time of the server
        :param client_email: the email of the client
        :param is_admin: is the client admin
        :param admin_data: the admin data
        """

        # setting important variables of the map
        self.is_admin = is_admin
        self.room_data = room_data
        self.attractions = attractions
        self.admin_data = admin_data
        self.server_time = datetime.strptime(server_time, '%Y/%m/%d')

        self.m_data = data

        self.__logged_in = logged
        self.client_email = client_email
        self.client = client
        self.open_top_level = None

        self.selected_marker_position = None

        App.clear_screen(root, menubar)

        # creating dictionaries of the offers
        self.positions = [i[7] for i in offers.values()]
        self.room_position = {i[6]: i[7] for i in offers.values()}
        self.offer_id_position = {key: i[7] for key, i in offers.items()}
        self.offer_id_room_name = {key: i[6] for key, i in offers.items()}

        # setting the root attributes of map
        self.root = root
        self.menubar = menubar

        self.WIDTH = 690
        self.HEIGHT = 750

        self.marker_list = []

        # self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind("<Return>", self.search)

        if sys.platform == "darwin":
            self.root.bind("<Command-q>", self.on_closing)
            self.root.bind("<Command-w>", self.on_closing)

        # setting grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_columnconfigure(2, weight=0)
        self.root.grid_rowconfigure(1, weight=1)

        # setting search bar for the map
        self.search_bar = Entry(self.root, width=50)
        self.search_bar.grid(row=0, column=0, pady=10, padx=10, sticky="we")
        self.search_bar.focus()

        self.search_bar_button = Button(master=self.root, width=8, text="Search", command=self.search)
        self.search_bar_button.grid(row=0, column=1, pady=10, padx=10)

        self.search_bar_clear = Button(master=self.root, width=8, text="Clear", command=self.clear)
        self.search_bar_clear.grid(row=0, column=2, pady=1, padx=(0, 10))

        # setting the map
        self.map_widget = TkinterMapView(width=self.WIDTH, height=600, corner_radius=0)
        self.map_widget.grid(row=1, column=0, sticky="nsew")

        # setting option menu to sort by the offers
        self.variable = StringVar()
        self.variable.set("SORT BY")
        self.order = OptionMenu(self.root, self.variable, *["Price", "Proximity", "Average Rating"],
                                command=self.option_menu)

        if self.is_admin:

            # if user is admin, creating widgets for him to search up dates
            fr = Frame(self.root, bg="white")

            # creating date entries for the admin to search rooms that are taken these dates
            self.d1 = DateEntry(fr, font=f, locale='en_US', date_pattern='dd/mm/yyyy',
                                mindate=datetime.now())
            self.d1.grid(row=0, column=1, sticky="new")

            self.d2 = DateEntry(fr, font=f, locale='en_US', date_pattern='dd/mm/yyyy',
                                mindate=datetime.now())
            self.d2.grid(row=0, column=2, sticky="new", padx=5)

            # search button
            CTkButton(fr, width=30, text='Search', relief=SOLID, cursor='hand2',
                      fg_color="#32CD32", hover_color="#33A8FF",
                      command=lambda: self.update_admin_markers(self.d1.get_date(), self.d2.get_date())).grid(row=1,
                                                                                                              column=1,
                                                                                                              columnspan=2,
                                                                                                              padx=5,
                                                                                                              sticky="new",
                                                                                                              pady=30)

            # widgets placements
            self.order = OptionMenu(fr, self.variable, *["Price", "Proximity", "Average Rating"],
                                    command=self.option_menu)
            self.order.config(width=15, font=("Roboto Medium", 12))
            self.order.grid(row=2, column=1, columnspan=2, sticky="new")

            self.marker_list_box = Listbox(fr, height=30, font="Roboto 14")
            self.marker_list_box.grid(row=2, column=1, columnspan=2, sticky="nsew", pady=(36, 0))
            self.marker_list_box.configure(background="#87CEEB", foreground="white")
            fr.grid(row=1, column=1, columnspan=2, sticky="new")

            # showing all the offers
            self.show_admin_markers()

            messagebox.showinfo("Admin", "You are admin\n"
                                         "Enter two dates and the rooms that are purchased for these day will appear orange",
                                icon="info")
        else:

            # widget placements
            self.order.config(width=15, font=("Roboto Medium", 12))
            self.order.grid(row=1, column=1, columnspan=2, sticky="new")

            # creating the listbox of all the offers
            self.marker_list_box = Listbox(self.root, height=8, font="Roboto 14")
            self.marker_list_box.grid(row=1, column=1, columnspan=2, sticky="nsew", pady=(36, 0))
            self.marker_list_box.configure(background="#87CEEB", foreground="white")

        # setting map address on New York City for starters
        self.map_widget.set_address("NYC")

        self.marker_path = None

        # setting dictionaries and variables, to keep track of user data
        self.search_marker = None
        self.search_in_progress = False

        self.marker_colors = dict({})
        self.image_loc = dict({})

        # setting up two important events of the map. marker_event --> will send once a marker was clicked
        # purchase_event --> will send the purchase id to the server
        self.marker_event = Event()
        self.purchase_event = Event()
        self.review_root = None

        if self.is_admin is None:
            self.show_markers()

        # if needed to add attraction
        if self.attractions != None:

            for attraction in self.attractions:
                self.add_attraction(*attraction)

        # getting the room names, entering them to list for the user to search
        self.client.send("#GET ROOM NAMES#".encode())
        self.wait_for_server_to_respond(self.m_data, 0)

        # inserting all the room names of the offers into the listbox
        if type(self.m_data[0][0]) == tuple:
            self.m_data[0] = [i[0] for i in self.m_data[0]]
        for i in self.m_data[0]:
            self.marker_list_box.insert(END, i)

        # binding listbox to zoom into the marker
        self.marker_list_box.bind("<<ListboxSelect>>", lambda e: self.on_event())

        # setting thread for the 'set_proximity' function
        thread = Thread(target=self.set_proximity)
        thread.daemon = True
        thread.start()

    def update_server_time(self, time):
        """
        function updates the server time
        :param time: the updated server time
        :return: None
        """
        self.server_time = str(datetime.strptime(time, '%Y/%m/%d')).replace("-", "/")
        self.server_time = self.server_time[:self.server_time.find(" ")]
        self.server_time = datetime.strptime(self.server_time, '%Y/%m/%d')

    def set_proximity(self):
        """
        function sorts the markers in the listbox by how close the user is in the map
        :return: None
        """

        while 1:

            try:

                if self.variable.get() == "Proximity":

                    # getting the position in which the user is in the map
                    pos = self.map_widget.get_position()
                    self.sort_by_position = {}

                    for key, value in self.room_position.items():
                        self.sort_by_position[key] = self.calculate_distance(pos[0], pos[1], float(value.split(",")[0]),
                                                                             float(value.split(",")[1][1:]))
                    # sorting by how close the user is to the marker
                    lst_sorted = list(
                        {k: v for k, v in sorted(self.sort_by_position.items(), key=lambda item: item[1])})

                    self.marker_list_box.delete(0, END)

                    # entering to listbox
                    for i in lst_sorted:
                        self.marker_list_box.insert(END, i)

                time.sleep(0.7)

            except RuntimeError:
                pass

    def calculate_distance(self, x1, y1, x2, y2):
        """
        function calculates distance between two points of coordinates
        :param x1: x of point1
        :param y1: y of point1
        :param x2: x of point2
        :param y2: y of point2
        :return: distance (as int)
        """
        return math.sqrt(math.pow((x1 - x2), 2) + math.pow((y1 - y2), 2))

    def wait_for_server_to_respond(self, lst, index):
        """
        function waits till server responds on a message
        :param lst: the list with data
        :param index: the index of the item in the list
        :return: None
        """

        while lst[index] is None:
            pass
        return

    def option_menu(self, event=None):
        """
        function sorts offers by a certain characteristic (Price, Proximity, Average Rating)
        :param event:
        :return: None
        """

        if self.variable.get() == "Price":

            # getting the offers ordered by their price
            self.client.send("#ORDER OFFERS BY PRICE#".encode())
            self.wait_for_server_to_respond(self.m_data, 1)
            self.marker_list_box.delete(0, END)

            # entering to listbox
            for i in self.m_data[1]:
                self.marker_list_box.insert(END, i[0])

        elif self.variable.get() == "Average Rating":

            # ordering offers by their average rating in 'ratings' table
            self.client.send("#ORDER OFFERS BY AVERAGE RATING#".encode())
            self.wait_for_server_to_respond(self.m_data, 6)
            ratings = self.m_data[6]
            ratings = [{int(i[0]): float(i[1])} for i in ratings]

            # using Counter to get the total rating of an offer
            c = Counter()
            for d in ratings:
                c.update(d)
            self.room_name_rating = dict(c)

            # sorting by the average rating
            for key, value in self.offer_id_room_name.items():
                if key not in self.room_name_rating.keys():
                    self.room_name_rating[key] = 0
            self.room_name_rating = {self.offer_id_room_name[key]: value for key, value in
                                     self.room_name_rating.items()}
            self.room_name_rating = {key: value for key, value in
                                     sorted(self.room_name_rating.items(), key=lambda item: item[1], reverse=True)}

            # entering to listbox
            self.marker_list_box.delete(0, END)
            for key in self.room_name_rating.keys():
                self.marker_list_box.insert(END, key)

    def on_mousewheel(self, event, canvas):
        """
        function scrolls in scrollbar
        :param event:
        :param canvas: the canvas which contains the scrollbar
        :return: None
        """
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    @staticmethod
    def clear_screen(root, menubar):
        """
        The function clears the screen out of any widget expect the menu
        """
        for widget in root.winfo_children():
            if widget is not menubar:
                widget.destroy()

    def search(self, event=None):
        """
        function searches a location and zooms on it in the map
        :param event:
        :return: None
        """

        if not self.search_in_progress:
            self.search_in_progress = True
            if self.search_marker not in self.marker_list:
                self.map_widget.delete(self.search_marker)
            address = self.search_bar.get()
            self.search_marker = self.map_widget.set_address(address)
            self.map_widget.set_zoom(12)

            if self.search_marker is False:

                # address was invalid (return value is False)
                self.search_marker = None
            self.search_in_progress = False

    def get_marker_colors(self):
        return self.marker_colors

    def __getmarkers__(self):
        return self.marker_colors

    def __get_recent_orders__(self):
        return self.recent_orders

    def show_markers(self):
        """
        function shows markers for starters on the map
        :return: None
        """

        for index, i in enumerate(self.positions):

            # getting the location of each marker, then creating it green colored on the map
            x = float(i.split(",")[0].strip())
            y = float(i.split(",")[1].strip())
            marker = self.create_marker(x, y, "green", lambda m: self.marker_clicked(index, m))
            self.marker_colors[marker.position] = "green"
            self.marker_list.append(marker)

    def create_marker(self, x, y, color, command):
        """
        function creates marker and puts it on the map
        :param x: x coordinate
        :param y: y coordinate
        :param color: color of the marker
        :param command: marker command once it's clicked
        :return: None
        """

        return self.map_widget.set_marker(float(x), float(y),
                                          marker_color_circle=color,
                                          text=list(self.room_position.keys())[
                                              list(self.room_position.values()).index(str(x) + ", " + str(y))],
                                          command=command,
                                          marker_color_outside="black")

    def on_event(self):
        """
        function zooms into a specific offer by it's room name in the listbox presented in the map
        :return: None
        """

        index = self.marker_list_box.curselection()

        if index:

            # getting the room name
            selection = self.marker_list_box.curselection()[0]
            seltext = self.marker_list_box.get(selection)

            # getting location by room names
            self.client.send(pickle.dumps(["#GET LOCATION BY ROOM NAMES#", seltext]))
            self.wait_for_server_to_respond(self.m_data, 2)

            # getting position
            pos = self.m_data[2]
            x = pos.split(",")[0]
            y = pos.split(",")[1][1:]

            # getting the marker in that position and zooming in to it
            m = \
            [marker for marker in self.marker_list if x == str(marker.position[0]) and y == str(marker.position[1])][0]

            self.map_widget.set_position(m.position[0], m.position[1])
            self.map_widget.set_zoom(10)

    def update_clock(self, marker, index, timer, root, c):
        """
        function updates the clock on the room window
        :param marker: marker on the map
        :param index: the index of the marker in the marker_list
        :param timer: timer object
        :param root: the root timer is presented in
        :param c: the count for the seconds
        :return: None
        """

        # if time is bigger the 0, config the text and change time presented
        flag = True
        if c >= 0:
            try:
                timer.config(text=c)
            except:
                flag = False
        else:

            # if time is up, releasing the marker, destroying the purchase root
            root.destroy()
            self.selected_marker_position = None

            new_marker = self.create_marker(*marker.position, "green",
                                            lambda m: self.marker_clicked(index, m))
            marker.delete()
            marker = new_marker
            self.marker_colors[marker.position] = "green"
            self.marker_list[index] = marker

            self.open_top_level.destroy()
            self.open_top_level = None
            self.root.protocol("WM_DELETE_WINDOW", lambda: self.on_closing())

            self.marker_event()

            flag = False

        if flag:

            # after one second, update the second
            root.after(1000, lambda: self.update_clock(marker, index, timer, root, c - 1))

    def add_marker(self, location, room_name, offer_id):
        """
        function adds marker to the map by location and also the room name
        :param location: the marker's location
        :param room_name: the name of the room
        :return: None
        """

        # adding to all the lists and dictionaries of markers the new marker
        self.positions.append(location)
        self.room_position[room_name] = location
        self.offer_id_position[offer_id] = location
        x, y = location.split(",")[0], location.split(",")[1][1:]
        marker = self.create_marker(x, y, "green", lambda m: self.marker_clicked(len(self.positions) - 1, m))
        self.marker_colors[marker.position] = "green"
        self.marker_list.append(marker)

        self.m_data[0].append(room_name)
        self.marker_list_box.insert(END, room_name)
        messagebox.showinfo("info", f"Someone added a new room!\n"
                                    f"{room_name}")

    def delete_marker(self, location, room_name, offer_id):
        """
        function deletes marker from map
        :param location: marker's location on the map
        :param room_name: the room name
        :return: None
        """

        # deleting from all the lists and dictionaries of markers the marker specified
        del self.positions[self.positions.index(location)]
        self.offer_id_position.pop(offer_id)
        self.room_position = {key: value for key, value in self.room_position.items() if value != location}
        x, y = location.split(",")[0], location.split(",")[1][1:]
        del self.marker_colors[(float(x), float(y))]
        self.m_data[0].remove(room_name)
        index = self.marker_list_box.get(0, END).index(room_name)
        self.marker_list_box.delete(index)
        marker = [i for i in self.marker_list if i.position == (float(x), float(y))][0]
        self.marker_list.remove(marker)
        marker.delete()
        messagebox.showinfo("Dispution", f"room {room_name} was disputed", icon="info")

    def add_attraction(self, location, attraction_name, image_name):
        """
        function adds attraction marker on the screen
        :param location: attraction's location
        :param attraction_name: attraction's name
        :param image_name: the image's name
        :return: None
        """

        # opening image, setting to show image by click on the marker
        img = ImageTk.PhotoImage(
            Image.open(PATH.replace("\\maps", "") + "\\map_images" + "\\" + image_name).resize((300, 200)))
        x, y = float(location.split(",")[0]), float(location.split(",")[1][1:])
        marker = self.map_widget.set_marker(x, y, image=img,
                                            image_zoom_visibility=(0, float("inf")),
                                            marker_color_outside="black", marker_color_circle="yellow",
                                            text=attraction_name, command=self.attraction_clicked)
        marker.hide_image(True)

    def attraction_clicked(self, marker):
        """
        checks if attraction marker is clicked
        :param marker: marker on the map
        :return: None
        """

        # if image is shown, deleting image
        # if not, showing image
        if marker.image_hidden is True:
            marker.hide_image(False)
        else:
            marker.hide_image(True)

    def marker_clicked(self, index, marker):
        """
        function is called every time marker is clicked, and shows all the details of the offer
        :param index: index of the marker in marker_list
        :param marker: marker on the map
        :return:
        """

        self.root.protocol("WM_DELETE_WINDOW", lambda marker=marker, index=index: self.on_closing(marker, index))

        # if marker is already taken
        if marker.marker_color_circle == "red" and not self.selected_marker_position and not marker.position == self.selected_marker_position:
            messagebox.showerror("Error", "this window is already taken")
            return

        # if first time clicking a marker
        if not marker.position == self.selected_marker_position:

            if not self.selected_marker_position:

                self.selected_marker_position = marker.position

                # opening a new window for purchase, change marker to orange
                self.marker_colors[marker.position] = "orange"
                self.open_top_level = Toplevel(self.root, height=150, width=300)
                self.open_top_level.resizable(False, False)
                new_marker = self.create_marker(*marker.position, "orange",
                                                lambda m: self.marker_clicked(index, m))
                marker.delete()
                marker = new_marker
                self.marker_list[index] = marker
                x, y = marker.position

                # getting data on this offer from the server
                self.client.send(pickle.dumps(["#GET INFORMATION ON OFFER#", x, y]))
                self.wait_for_server_to_respond(self.m_data, 3)

                # getting all the information on the offer
                self.offer_id = self.m_data[3][0]
                price = self.m_data[3][3]
                check_in, check_out = self.m_data[3][5].split("-")[0][:-1], self.m_data[3][5].split("-")[1][1:]
                date_check_in, date_check_out = datetime.strptime(check_in, '%Y/%m/%d'), datetime.strptime(check_out,
                                                                                                           '%Y/%m/%d')
                conditions = self.m_data[3][6]
                self.is_bought = self.m_data[3][-1]

                # setting frames in order to design the details of the offer form
                bigger_frame = Frame(self.open_top_level)
                left_frame = Frame(bigger_frame)
                right_frame = Frame(bigger_frame)

                # building the window from the information from the server
                CTkLabel(left_frame, text="images of the room", bg="#F5F5F5",
                         text_font=("Roboto Medium", -20)).pack(padx=10, pady=10)
                timer = Label(self.open_top_level, width=2, bg='black', fg='white')
                timer.pack(side='right', anchor='ne', padx=20, pady=20)
                t = threading.Thread(target=self.update_clock, args=(marker, index, timer, self.open_top_level, 60,))
                t.daemon = True
                t.start()

                # displaying images of the room
                images = self.m_data[3][4].split(",")
                images = ["map_images//" + str(i) for i in images]
                img = ImageTk.PhotoImage(Image.open(images[0]).resize((650, 450)))
                w = Label(left_frame, image=img, borderwidth=0)
                w.image = img
                w.pack(padx=10, pady=7)

                # offering an option to show more images of the room
                btn_frame = Frame(left_frame)
                CTkButton(btn_frame, width=100, text='Show more', relief=SOLID, cursor='hand2',
                          fg_color="#32CD32", hover_color="#33A8FF",
                          command=lambda: self.show_images(images)).pack(side="right", padx=10)

                # getting the ratings on this room
                self.client.send(pickle.dumps(["#GET RATING BY OFFER ID#", self.offer_id]))
                self.wait_for_server_to_respond(self.room_data, 1)

                # getting the reviews on this room
                self.client.send(pickle.dumps(["#GET REVIEW BY OFFER ID#", self.offer_id]))
                self.wait_for_server_to_respond(self.room_data, 2)
                reviews_anonymous = {}
                for i in self.room_data[2]:
                    is_anonymous = True if i[5] == "1" else False
                    reviews_anonymous[i[4]] = is_anonymous

                # offering option to see reviews on this room
                CTkButton(btn_frame, width=100, text='Show Reviews On This Room', relief=SOLID, cursor='hand2',
                          fg_color="#32CD32", hover_color="#33A8FF",
                          command=lambda: self.show_review(reviews_anonymous, self.room_data[2])).pack(side="left",
                                                                                                       padx=10)

                btn_frame.pack(pady=5)

                # creating labels for the window
                offer_frame = Frame(right_frame)
                CTkLabel(offer_frame, text="Price Per Night (₪)", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(
                    row=0, column=0, sticky=W,
                    pady=10)
                CTkLabel(offer_frame, text="Check In", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=1,
                                                                                                            column=0,
                                                                                                            sticky=W,
                                                                                                            pady=7)
                CTkLabel(offer_frame, text="Check Out", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=2,
                                                                                                             column=0,
                                                                                                             sticky=W,
                                                                                                             pady=7)
                CTkLabel(offer_frame, text="Conditions", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=3,
                                                                                                              column=0,
                                                                                                              sticky=W,
                                                                                                              pady=7)
                CTkLabel(offer_frame, text="Near", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=4, column=0,
                                                                                                        sticky=W,
                                                                                                        pady=7)
                CTkLabel(offer_frame, text="Location", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=5,
                                                                                                            column=0,
                                                                                                            sticky=W,
                                                                                                            pady=7)

                CTkLabel(offer_frame, text="Average rating of room", bg="#F5F5F5",
                         text_font=("Roboto Medium", -18)).grid(row=6, column=0,
                                                                sticky=W,
                                                                pady=7)

                CTkLabel(offer_frame, text=price, bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=0, column=1,
                                                                                                       sticky=W,
                                                                                                       pady=7,
                                                                                                       padx=20)

                # creating the date entries so that the user can decide when he/she wants to enter into the room
                self.offer_dates1 = DateEntry(offer_frame, font=f, locale='en_US', date_pattern='dd/mm/yyyy',
                                              mindate=date_check_in, maxdate=date_check_out)
                self.offer_dates1.grid(row=1, column=1,
                                       sticky=W, pady=7,
                                       padx=20)
                self.offer_dates2 = DateEntry(offer_frame, font=f, locale='en_US', date_pattern='dd/mm/yyyy',
                                              mindate=date_check_in, maxdate=date_check_out)
                self.offer_dates2.grid(row=2, column=1,
                                       sticky=W, pady=7,
                                       padx=20)
                CTkLabel(offer_frame, text=conditions, bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=3,
                                                                                                            column=1,
                                                                                                            sticky=W,
                                                                                                            pady=7,
                                                                                                            padx=20)

                # getting the near places of the offer using the geocoder
                b_n = "\n"
                near_places = str(geocoder.osm([x, y], method='reverse'))
                near_places = near_places[near_places.find("Reverse") + 9: near_places.rfind("]")].split(",")

                CTkLabel(offer_frame, text=f"{b_n.join([i.strip() for i in near_places])}", bg="#F5F5F5",
                         text_font=("Roboto Medium", -18)).grid(row=4, column=1,
                                                                sticky=W,
                                                                pady=10,
                                                                padx=20)
                CTkLabel(offer_frame, text=f"'({x}, {y})'", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=5,
                                                                                                                 column=1,
                                                                                                                 sticky=W,
                                                                                                                 pady=10,
                                                                                                                 padx=20)
                if self.room_data[1] != 0:

                    # if there is rating for the room, present it
                    CTkLabel(offer_frame, text=f"{self.room_data[1]} / 10", bg="#F5F5F5",
                             text_font=("Roboto Medium", -18)).grid(
                        row=6, column=1,
                        sticky=W,
                        pady=7,
                        padx=20)
                else:
                    CTkLabel(offer_frame, text="No rating so far", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(
                        row=6, column=1,
                        sticky=W,
                        pady=7,
                        padx=20)

                CTkButton(left_frame, width=200, text='Proceed', relief=SOLID, cursor='hand2',
                          fg_color="#32CD32", hover_color="#33A8FF",
                          command=lambda *args: self.show_payment(self.m_data[3], self.offer_id,
                                                                  self.offer_dates1.get_date(),
                                                                  self.offer_dates2.get_date(), marker, index)).pack(
                    side="bottom",
                    anchor="center",
                    pady=7)

                # widget placements
                offer_frame.pack()
                left_frame.pack(side="left", padx=10)
                right_frame.pack(side="left", padx=10)
                bigger_frame.pack(pady=10)

                # generating marker event (update markers)
                self.marker_event()

            else:

                # if user is trying to open more than one window
                messagebox.showerror("Error", "you can't open more than one window")

        else:

            # if user has clicked again on marker, make it green and available
            self.selected_marker_position = None

            new_marker = self.create_marker(*marker.position, "green",
                                            lambda m: self.marker_clicked(index, m))
            marker.delete()
            marker = new_marker
            self.marker_colors[marker.position] = "green"
            self.marker_list[index] = marker

            self.open_top_level.destroy()
            self.open_top_level = None

            self.root.protocol("WM_DELETE_WINDOW", lambda: self.on_closing())
            if self.review_root is not None:
                self.review_root.destroy()
            self.m_data[3] = None
            self.marker_event()

    def show_admin_markers(self):
        """
        function shows markers for admin
        :return: None
        """

        for index, i in enumerate(self.positions):

            # getting the location of each marker, then creating it green colored on the map
            x = float(i.split(",")[0].strip())
            y = float(i.split(",")[1].strip())
            marker = self.create_marker(x, y, "green", lambda m: self.admin_marker_clicked(index, m))
            self.marker_list.append(marker)

    def admin_marker_clicked(self, index, marker):
        """
        function is summoned every time marker is clicked,
        :param index: marker's index in marker_list
        :param marker: the marker on the map
        :return:
        """

        # opening a new window for purchase, change marker to orange
        self.marker_colors[marker.position] = "orange"
        self.open_top_level = Toplevel(self.root, height=150, width=300)
        self.open_top_level.resizable(False, False)
        x, y = marker.position

        # getting data on this offer from the server
        self.client.send(pickle.dumps(["#GET INFORMATION ON OFFER#", x, y]))
        self.wait_for_server_to_respond(self.m_data, 3)
        self.offer_id = self.m_data[3][0]
        price = self.m_data[3][3]
        check_in, check_out = self.m_data[3][5].split("-")[0][:-1], self.m_data[3][5].split("-")[1][1:]
        date_check_in, date_check_out = datetime.strptime(check_in, '%Y/%m/%d'), datetime.strptime(check_out,
                                                                                                   '%Y/%m/%d')
        conditions = self.m_data[3][6]

        # setting frames in order to design the details of the offer form
        bigger_frame = Frame(self.open_top_level)
        left_frame = Frame(bigger_frame)
        right_frame = Frame(bigger_frame)

        # building the window from the information from the server
        CTkLabel(left_frame, text="images of the room", bg="#F5F5F5",
                 text_font=("Roboto Medium", -20)).pack(padx=10, pady=10)

        # displaying images of the room
        images = self.m_data[3][4].split(",")
        images = ["map_images//" + str(i) for i in images]
        img = ImageTk.PhotoImage(Image.open(images[0]).resize((650, 450)))
        w = Label(left_frame, image=img, borderwidth=0)
        w.image = img
        w.pack(padx=10, pady=7)
        btn_frame = Frame(left_frame)
        CTkButton(btn_frame, width=100, text='Show more', relief=SOLID, cursor='hand2',
                  fg_color="#32CD32", hover_color="#33A8FF",
                  command=lambda: self.show_images(images)).pack(side="right", padx=10)

        # getting the ratings on this room
        self.client.send(pickle.dumps(["#GET RATING BY OFFER ID#", self.offer_id]))
        self.wait_for_server_to_respond(self.room_data, 1)

        # getting reviews of the room
        self.client.send(pickle.dumps(["#GET REVIEW BY OFFER ID#", self.offer_id]))
        self.wait_for_server_to_respond(self.room_data, 2)

        reviews_anonymous = {}
        for i in self.room_data[2]:
            is_anonymous = True if i[5] == "1" else False
            reviews_anonymous[i[4]] = is_anonymous

        # offering option too see reviews of the room
        CTkButton(btn_frame, width=100, text='Show Reviews On This Room', relief=SOLID, cursor='hand2',
                  fg_color="#32CD32", hover_color="#33A8FF",
                  command=lambda: self.show_review(reviews_anonymous, self.room_data[2])).pack(side="left",
                                                                                               padx=10)

        btn_frame.pack(pady=5)

        # creating labels for the window
        offer_frame = Frame(right_frame)
        CTkLabel(offer_frame, text="Price Per Night (₪)", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(
            row=0, column=0, sticky=W,
            pady=10)
        CTkLabel(offer_frame, text="Check In", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=1,
                                                                                                    column=0,
                                                                                                    sticky=W,
                                                                                                    pady=7)
        CTkLabel(offer_frame, text="Check Out", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=2,
                                                                                                     column=0,
                                                                                                     sticky=W,
                                                                                                     pady=7)
        CTkLabel(offer_frame, text="Conditions", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=3,
                                                                                                      column=0,
                                                                                                      sticky=W,
                                                                                                      pady=7)
        CTkLabel(offer_frame, text="Near", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=4, column=0,
                                                                                                sticky=W,
                                                                                                pady=7)
        CTkLabel(offer_frame, text="Location", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=5, column=0,
                                                                                                    sticky=W,
                                                                                                    pady=7)
        CTkLabel(offer_frame, text="Average rating of room", bg="#F5F5F5",
                 text_font=("Roboto Medium", -18)).grid(row=6, column=0,
                                                        sticky=W,
                                                        pady=7)
        CTkLabel(offer_frame, text=price, bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=0, column=1,
                                                                                               sticky=W,
                                                                                               pady=7,
                                                                                               padx=20)

        # creating the date entries so that the user can decide when he/she wants to enter into the room
        self.offer_dates1 = DateEntry(offer_frame, font=f, locale='en_US', date_pattern='dd/mm/yyyy',
                                      mindate=date_check_in, maxdate=date_check_out)
        self.offer_dates1.grid(row=1, column=1,
                               sticky=W, pady=7,
                               padx=20)
        self.offer_dates2 = DateEntry(offer_frame, font=f, locale='en_US', date_pattern='dd/mm/yyyy',
                                      mindate=date_check_in, maxdate=date_check_out)
        self.offer_dates2.grid(row=2, column=1,
                               sticky=W, pady=7,
                               padx=20)
        CTkLabel(offer_frame, text=conditions, bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=3,
                                                                                                    column=1,
                                                                                                    sticky=W,
                                                                                                    pady=7,
                                                                                                    padx=20)
        # getting the near places of the offer using the geocoder
        b_n = "\n"
        near_places = str(geocoder.osm([x, y], method='reverse'))
        near_places = near_places[near_places.find("Reverse") + 9: near_places.rfind("]")].split(",")
        CTkLabel(offer_frame, text=f"{b_n.join([i.strip() for i in near_places])}", bg="#F5F5F5",
                 text_font=("Roboto Medium", -18)).grid(row=4, column=1,
                                                        sticky=W,
                                                        pady=10,
                                                        padx=20)
        CTkLabel(offer_frame, text=f"'({x}, {y})'", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(row=5,
                                                                                                         column=1,
                                                                                                         sticky=W,
                                                                                                         pady=10,
                                                                                                         padx=20)
        if self.room_data[1] != 0:

            # if there is rating for the room, presenting it
            CTkLabel(offer_frame, text=f"{self.room_data[1]} / 10", bg="#F5F5F5",
                     text_font=("Roboto Medium", -18)).grid(
                row=6, column=1,
                sticky=W,
                pady=7,
                padx=20)
        else:
            CTkLabel(offer_frame, text="No rating so far", bg="#F5F5F5", text_font=("Roboto Medium", -18)).grid(
                row=6, column=1,
                sticky=W,
                pady=7,
                padx=20)

        # disabling 'proceed' button
        # in this map the admin can only see if the room are taken (beside their details)
        CTkButton(left_frame, width=200, text='Proceed', relief=SOLID, cursor='hand2',
                  fg_color="#32CD32", hover_color="#33A8FF", state=DISABLED,
                  command=lambda *args: self.show_payment(self.m_data[3], self.offer_id,
                                                          self.offer_dates1.get_date(),
                                                          self.offer_dates2.get_date(), marker, index)).pack(
            side="bottom",
            anchor="center",
            pady=7)

        # widget placements
        offer_frame.pack()
        left_frame.pack(side="left", padx=10)
        right_frame.pack(side="left", padx=10)
        bigger_frame.pack(pady=10)
        self.m_data[3] = None

    def update_admin_markers(self, date1, date2):
        """
        function checks and updates the markers (offers) that are taken between the dates date1 and date2
        :param date1: the start date
        :param date2: the end
        :return: None
        """

        # turning all the markers to green
        for marker in self.marker_list:
            new_marker = self.create_marker(*marker.position, "green", lambda m: self.admin_marker_clicked(index, m))
            marker.delete()
            marker = new_marker

        selected_date_range = App.date_range(datetime.strptime(str(date1).replace("-", "/"), '%Y/%m/%d'),
                                             datetime.strptime(str(date2).replace("-", "/"), '%Y/%m/%d'))

        self.client.send("#GET ADMIN PURCHASES#".encode())
        self.wait_for_server_to_respond(self.admin_data, 3)

        # iterating over all the purchases
        for value in self.admin_data[3].values():

            check_in, check_out = value[1].split("-")[0][:-1], value[1].split("-")[1][1:]
            date_check_in, date_check_out = datetime.strptime(check_in, '%Y/%m/%d'), datetime.strptime(check_out,
                                                                                                       '%Y/%m/%d')
            search_date_range = App.date_range(date_check_in, date_check_out)

            # checking if any of the dates admin has chose are relevant
            if any(i in selected_date_range for i in search_date_range):
                x, y = self.offer_id_position[int(value[0])].split(",")[0], \
                       self.offer_id_position[int(value[0])].split(",")[1][1:]
                index = list(self.offer_id_position.values()).index(x + ", " + y)
                marker = self.marker_list[index]

                # if the room is taken, creating a new purple marker
                new_marker = self.marker_list[self.marker_list.index(
                    [i for i in self.marker_list if i.position == (float(x), float(y))][0])] = self.create_marker(x, y,
                                                                                                                  "purple",
                                                                                                                  lambda
                                                                                                                      m: self.admin_marker_clicked(
                                                                                                                      index,
                                                                                                                      m))
                marker.delete()
                marker = new_marker

        self.admin_data[3] = None

    def show_review(self, review_anonymous, room_data):
        """
        function presents reviews on a certain room
        :param review_anonymous: the review as key, is the reviewer anonymous as value
        :param room_data: the data on the room
        :return: None
        """

        self.room_data[2] = None

        if not review_anonymous:

            # handling errors
            messagebox.showinfo("Sorry", "There are no reviews so far on this room", icon="info")
            return

        self.review_root = Toplevel(self.root)

        # creating a main
        main_frame = Frame(self.review_root)
        main_frame.pack(fill=BOTH, expand=1)

        # creating a canvas
        my_canvas = Canvas(main_frame)
        my_canvas.pack(side=RIGHT, fill=BOTH, expand=1)

        # adding a scrollbar
        my_scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=my_canvas.yview)
        my_scrollbar.pack(side=LEFT, fill=Y)

        # configuring the canvas
        my_canvas.configure(yscrollcommand=my_scrollbar.set)
        my_canvas.bind('<Configure>', lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))

        # creating another frame
        second_frame = Frame(my_canvas)

        # Add that New frame To a Window In The Canvas
        my_canvas.create_window((0, 0), window=second_frame, anchor="nw")

        if room_data is not None:
            for index, data in enumerate(room_data):

                # creating frames
                f = CTkFrame(second_frame, border_width=3, border_color="green", bg_color=None, width=1000, height=100)
                if bool(int(data[5])):
                    CTkLabel(master=f, text=f"Anonymous is saying:", text_font=("Roboto Medium", -17)).pack(anchor="sw",
                                                                                                            padx=10,
                                                                                                            pady=10)
                    w = CTkLabel(master=f, text=f"{data[4]}", text_font=("Roboto Medium", -14), bg_color=None)
                    w.pack(pady=5, padx=5)
                else:
                    CTkLabel(master=f, text=f"{data[2]} is saying:", text_font=("Roboto Medium", -17)).pack(anchor="sw",
                                                                                                            padx=10,
                                                                                                            pady=10)
                    w = CTkLabel(master=f, text=f"{data[4]}", text_font=("Roboto Medium", -14))
                    w.pack(pady=5)

                f.grid(row=index, column=0, sticky="nwe", pady=20, padx=10)

    def show_images(self, images: list) -> None:
        """
        function shows images on the room
        :param images: images of the room
        :return: None
        """
        try:
            n: int = len(images)
            f = plt.figure("Images")
            f.suptitle('Images of the room', fontsize=16)
            for i, image in enumerate(images):
                img = io.imread(image)

                # Debug, plot figure
                f.add_subplot(1, n, i + 1)
                plt.axis('off')
                plt.imshow(img)

            plt.show(block=True)
        except:

            # handling errors
            messagebox.showinfo("Sorry", "Seems like we can't upload the pictures for you", icon="info")

    def update_markers(self, updated):
        """
        function updates the markers on the map
        :param updated: the updated offers
        :return: None
        """

        # getting the current markers
        current_markers = self.marker_list[:]

        # deleting all the markers
        try:
            for marker in current_markers:
                marker.delete()
        except _tkinter.TclError:
            pass

        for key, value in updated.items():  # key,value --> marker, color

            index = list(updated.keys()).index(key)
            try:

                # if a user has placed a marker, deleting that marker,
                # showing a new red marker that cannot be pressed
                if value == "orange" and not self.selected_marker_position == key:
                    new_marker = self.create_marker(*key, "red",
                                                    lambda m: self.marker_clicked(index, m))
                    marker = new_marker
                    self.marker_colors[marker.position] = value
                    self.marker_list[index] = marker

                else:
                    new_marker = self.create_marker(*key, value,
                                                    lambda m: self.marker_clicked(index, m))
                    marker = new_marker
                    self.marker_colors[marker.position] = value
                    self.marker_list[index] = marker
            except TypeError:
                self.show_markers()

    def show_payment(self, data, offer_id, date1, date2, marker, index):
        """
        function shows payment window for the user
        :param data: offer data
        :param offer_id: the offer id
        :param date1: check in
        :param date2: check out
        :return: None
        """

        # starting the toplevel root for buying the room
        self.payment_root = Toplevel(self.root)
        payment_frame = CTkFrame(master=self.payment_root, width=180, corner_radius=0)
        payment_frame.pack(expand=1, fill=BOTH)

        # creating labels for the payment form
        self.label_1 = CTkLabel(master=payment_frame,
                                text="Total cost of the room (₪)",
                                text_font=("Roboto Medium", -16))

        self.label_1.grid(row=0, column=0, padx=5, pady=10)

        self.label_2 = CTkLabel(master=payment_frame,
                                text=int(self.m_data[3][3].replace(",", "")) * len(App.date_range(date1, date2)),
                                text_font=("Roboto Medium", -16))

        self.label_2 = CTkLabel(master=payment_frame,
                                text=int(self.m_data[3][3].replace(",", "")) * len(App.date_range(date1, date2)),
                                text_font=("Roboto Medium", -16))

        self.label_2.grid(row=0, column=1, padx=5, pady=10)

        self.label_3 = CTkLabel(master=payment_frame,
                                text="Enter Credit",
                                text_font=("Roboto Medium", -16))

        self.label_3.grid(row=1, column=0, padx=5, pady=10)

        self.credit_variable = StringVar()
        self.credit_entry = CTkEntry(master=payment_frame, textvariable=self.credit_variable,
                                     width=120,
                                     placeholder_text="Enter Credit")

        self.credit_entry.grid(row=1, column=1, padx=5, pady=10)

        # if user is not logged in, he/she must insert an email
        if not self.__logged_in:
            self.label_4 = CTkLabel(master=payment_frame,
                                    text="Enter email",
                                    text_font=("Roboto Medium", -16))

            self.label_4.grid(row=2, column=0, padx=5, pady=10)

            self.entry_variable = StringVar()
            self.email_entry = CTkEntry(master=payment_frame, textvariable=self.entry_variable,
                                        width=120,
                                        placeholder_text="Enter Email")
            self.email_entry.grid(row=2, column=1, padx=5, pady=10)

        # creating proceed button
        CTkButton(payment_frame, width=100, text='Proceed', relief=SOLID, cursor='hand2',
                  fg_color="#A9A9A9", hover_color="#33A8FF",
                  command=lambda *args: self.insert_payment(self.m_data[3], self.offer_id,
                                                            self.offer_dates1.get_date(),
                                                            self.offer_dates2.get_date(), marker, index)).grid(row=3,
                                                                                                               columnspan=2,
                                                                                                               pady=10)

    def clear(self):
        """
        function clears the search bar
        :return: None
        """

        self.search_bar.delete(0, last=END)
        self.map_widget.delete(self.search_marker)

    @staticmethod
    def date_range(start, end):
        """
        function gives date range between two datetime objects
        :param start: starting date
        :param end: ending date
        :return:
        """
        delta = end - start  # as timedelta
        days = [start + timedelta(days=i) for i in range(delta.days + 1)]
        return days

    def insert_payment(self, data, offer_id, date1, date2, marker, index):
        """
        :param data: data on the purchase
        :param offer_id: the offer id
        :param date1: the check in date
        :param date2: the check out date
        :param marker: the marker on the map
        :param index: the index of the marker in marker_list
        :return: None
        """

        # creating regex email pattern for
        self.email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        # if user hasn't entered credit card or it isn't valid
        if self.credit_variable.get() == "":
            messagebox.showerror("Error", "Credit card number cannot be empty")
            return

        elif len(self.credit_variable.get()) and any(i.isalpha() for i in self.credit_variable.get()):
            messagebox.showerror("Error", "Credit card number isn't valid")
            return

        # if user isn't logged in, he/she must enter an email
        if not self.__logged_in:

            if self.entry_variable.get() != "":

                # if email doesn't match regex
                if not bool(re.fullmatch(self.email_regex, self.entry_variable.get())):
                    messagebox.showerror("Error", "Not valid email")
                    return

                self.client_email = self.entry_variable.get()
                self.entry_variable.set("")

            else:

                # handling errors
                messagebox.showerror("Error", "Email cannot be empty")
                return

        selected_date1, selected_date2 = str(date1).replace("-", "/"), str(date2).replace("-", "/")
        selected_date_check_in, selected_date_check_out = datetime.strptime(selected_date1,
                                                                            '%Y/%m/%d'), datetime.strptime(
            selected_date2,
            '%Y/%m/%d')

        first_date_range = App.date_range(selected_date_check_in, selected_date_check_out)

        # if admin has sped up time, checking the current dates of purchase
        # if one of dates user wants to purchase isn't valid anymore, showing message
        #for i in first_date_range:
        #    if self.server_time > i:
        #        messagebox.showinfo("Sorry", "An Admin has sped up the time\n"
        #                                     "You must only purchase rooms that offer a room after the date\n"
        #                                     f"{self.server_time.strftime('%Y/%m/%d')}", icon='info')
        #        return

        # getting all purchases by that id
        self.client.send(pickle.dumps(["#GET PURCHASE BY OFFER ID#", offer_id]))
        self.wait_for_server_to_respond(self.m_data, 5)

        # checking if a date user has chosen is already taken
        for row in self.m_data[5]:
            not_availiabe1, not_availiabe2 = row[2].split("-")[0][:-1], row[2].split("-")[1][1:]
            selected_not_availiabe1, selected_not_availiabe2 = datetime.strptime(not_availiabe1,
                                                                                 '%Y/%m/%d'), datetime.strptime(
                not_availiabe2,
                '%Y/%m/%d')
            selected_date_range = App.date_range(selected_not_availiabe1, selected_not_availiabe2)

            for j in first_date_range:
                if j in selected_date_range:

                    # if room is taken, showing message
                    messagebox.showerror("Error", f"{selected_date1} - {selected_date2} is taken.\n"
                                                  f"please choose different dates")
                    self.payment_root.destroy()
                    self.m_data[5] = None
                    return

        # creating new purchase id
        self.purchase_id = random.randint(1000000, 10000000)
        self.client.send(pickle.dumps(["#UPDATE OFFERS#", self.offer_id]))

        # sending a request to insert the new purchase
        self.client.send(pickle.dumps(["#INSERT TO PURCHASES#",
                                       [self.purchase_id, data[0], f"{selected_date1} - {selected_date2}",
                                        self.client_email, self.credit_variable.get(),
                                        str(self.__logged_in)]]))

        self.payment_root.destroy()
        self.selected_marker_position = None

        # releasing the marker that was taken for the purchase
        # returning marker to default state
        new_marker = self.create_marker(*marker.position, "green",
                                        lambda m: self.marker_clicked(index, m))
        marker.delete()
        marker = new_marker
        self.marker_colors[marker.position] = "green"
        self.marker_list[index] = marker

        self.open_top_level.destroy()
        self.open_top_level = None
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.on_closing())

        self.marker_event()

        self.client.send(pickle.dumps(["#GET OFFER BY PURCHASE ID#", self.purchase_id]))
        self.wait_for_server_to_respond(self.m_data, 4)
        App.recent_orders.append(self.m_data[4])
        messagebox.showinfo("Success", "Your purchase has been saved")

        # generating the purchase event
        self.purchase_event()

    def on_closing(self, marker=None, index=None, event=None):
        """
        function makes sure closing window goes without errors
        :param marker: marker on the map
        :param index: index in marker_list of the marker
        :param event: None
        :return: None
        """

        try:

            # if user wants to quit
            if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):

                try:

                    # if a marker is clicked, release the window and the markers
                    # setting marker to default state
                    if marker is not None and index is not None:
                        self.selected_marker_position = None

                        new_marker = self.create_marker(*marker.position, "green",
                                                        lambda m: self.marker_clicked(index, m))
                        marker.delete()
                        marker = new_marker
                        self.marker_colors[marker.position] = "green"
                        self.marker_list[index] = marker

                        self.open_top_level.destroy()
                        self.open_top_level = None

                        self.marker_event()

                    self.root.destroy()
                    self.client.close()

                except _tkinter.TclError:
                    pass


        except AttributeError:
            pass

    def start(self):
        """
        function starts the root
        :return: None
        """
        self.root.mainloop()


if __name__ == "__main__":
    app = App()
    app.start()
