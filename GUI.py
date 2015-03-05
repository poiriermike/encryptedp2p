# A test Tkinter GUI

try: #python 2
    from Tkinter import *
except ImportError: #python 3
    from tkinter import *


IPList = []
ConnectionsList = []

selectedIP = NONE
chatWindow = NONE

def chatWindowPrintText(text):
    chatWindow.config(state=NORMAL)
    chatWindow.insert(END, text)
    chatWindow.config(state=DISABLED)
    chatWindow.see(END)

def updateSelected():

    global selectedIP
    #TODO make this more robust/usefull etc
    selectedIP = ConnectionsList[1].get(ACTIVE)

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

    #TODO failure cases for ip addresses go here
    if(selectedIP == NONE or selectedIP == ""):
        chatWindowPrintText("Unable to connect to IP\n")
        return False;

    #TODO connect to selected IP here
    chatWindowPrintText("Attempting to connect to "+ selectedIP+"\n")
    return True

def closeProgram():
    root.quit()

def initialize():
    global ConnectionsList
    global chatWindow
    #set up the main window
    root = Tk()
    root.title("Encrypted P2P")

    mainFrame = Frame(root)
    mainFrame.pack()

    ConnectionsList.append(Listbox(mainFrame, selectmode=SINGLE))
    ConnectionsList.append(Listbox(mainFrame, selectmode=SINGLE))

    ConnectionsList[0].grid(row=0, column=0)
    ConnectionsList[1].grid(row=0, column=1)

    #set up chat window with scroll bar
    chatTextFrame = Frame(root)
    chatTextFrame.pack()

    scrollbar = Scrollbar(chatTextFrame)
    scrollbar.pack(side=RIGHT, fill=Y)

    chatWindow = Text(chatTextFrame, height=5, state=DISABLED)
    chatWindow.pack(side=LEFT, fill=BOTH)

    scrollbar.config(command=chatWindow.yview)
    chatWindow.config(yscrollcommand=scrollbar.set)

    #set up user text field for input
    textEntry = Text(root, height=1)
    textEntry.pack()


    #set up buttons and their method calls
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