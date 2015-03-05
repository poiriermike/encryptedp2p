# A test Tkinter GUI

try: #python 2
    from Tkinter import *
except ImportError: #python 3
    from tkinter import *



def refreshAvailIP():

    #populate the list of IP addresses here
    ipList = {"192.168.0.1", "0.0.0.0"}
    return ipList


def initialize():
    #set up the main window
    root = Tk()
    root.title("Encrypted P2P")


    IPList = refreshAvailIP()
    listB = Listbox(root)

    for item in IPList:
        listB.insert(0, item)

    listB.pack()

    return root





root = initialize()
root.mainloop()

# create a fame which will hold all of the UI contents
#mainframe = ttk.Frame(root, padding = "5, 5, 5, 5")
# allow frame expansion when resizing
#mainframe.rowconfigure(0, Weight=1)
#mainframe.columnconfigure(0, Weight=1)