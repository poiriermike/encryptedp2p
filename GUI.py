# A test Tkinter GUI

try: #python 2
    from Tkinter import *
except ImportError: #python 3
    from tkinter import *


IPList = []
ConnectionsList = []

selectedIP = NONE

def updateSelected():

    global selectedIP
    #TODO make this more robust etc
    selectedIP = ConnectionsList[1].get(ACTIVE)
    print("Selected IP = " + selectedIP)

def refreshAvailIP():
    global IPList


    #TODO populate the list of IP addresses here
    IPList = {"Robert" : "192.168.0.1", "Mike" : "100.42.16.45"}

    #clear all the old values from the list box
    ConnectionsList[0].delete(0, END)
    ConnectionsList[1].delete(0, END)
    for item in IPList.keys():
        ConnectionsList[0].insert(END, item)
        ConnectionsList[1].insert(END, IPList.get(item))

def connectToIP():

    global selectedIP
    updateSelected()

    if(selectedIP == NONE):
        print ("Unable to connect to IP")
        return False;

    #connect to selected IP here
    print("Attempting to connect to "+ selectedIP)

def closeProgram():

    root.quit()

def initialize():
    global ConnectionsList
    #set up the main window
    root = Tk()
    root.title("Encrypted P2P")

    mainFrame = Frame(root)
    mainFrame.pack()

    ConnectionsList.append(Listbox(mainFrame, selectmode=SINGLE))
    ConnectionsList.append(Listbox(mainFrame, selectmode=SINGLE))

    ConnectionsList[0].grid(row=0, column=0)
    ConnectionsList[1].grid(row=0, column=1)

    IPList = refreshAvailIP()





    refreshButton = Button(root, text="Refresh List", command=refreshAvailIP)
    refreshButton.pack(side=LEFT)

    exitButton = Button(root, text="Exit Program", command=closeProgram)
    exitButton.pack(side=RIGHT)

    connectButton = Button(root, text="Connect", command=connectToIP)
    connectButton.pack(side=RIGHT)



    #listB.pack()

    return root





root = initialize()
root.mainloop()

# create a fame which will hold all of the UI contents
#mainframe = ttk.Frame(root, padding = "5, 5, 5, 5")
# allow frame expansion when resizing
#mainframe.rowconfigure(0, Weight=1)
#mainframe.columnconfigure(0, Weight=1)