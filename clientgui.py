__author__ = 'robert'

from twisted.internet import protocol, reactor, stdio, tksupport

try: #python 2
    from Tkinter import *
except ImportError: #python 3
    from tkinter import *

class client_gui:

    #class constructor
    def __init__(self, reactor, logger, server, contactlist):
        self.reactor = reactor
        self.log = logger
        self.server = server

        #Dictionary containing all contacts to display and their info
        self.Contacts = contactlist
        #textbox where user text is typed
        self.textEntry = NONE
        #textbox where all chat messages appear
        self.chatWindow = NONE
        # list boxes in GUI for displaying and selecting contact info
        self.ConnectionsList = []
        self.username = "Batwayne"

    def set_username(self, newusername):
        self.username = newusername

    # print givent text in the chat text window
    def chatWindowPrintText(self, text):
        self.chatWindow.config(state=NORMAL)
        self.chatWindow.insert(END, text)
        self.chatWindow.config(state=DISABLED)
        self.chatWindow.see(END)

    # Hopefully temp way to clean up the newline in the text box after sending messages
    def clearText(self, event):
        if event.keysym == 'Return':
            self.textEntry.delete('0.0', END)

    #Send a message through the GUI chat
    def sendChatMessage(self, event):

        if event.keysym == 'Return':
            selectedContact = self.updateSelectedContact()

            if(selectedContact == None):
                self.chatWindowPrintText("No Contact Selected\n")
                return False

            selectedIP = selectedContact['ip']
            selectedPort = selectedContact['port']

            if selectedIP is NONE or selectedPort is None:
                return False

            message = self.textEntry.get('0.0', END)
            self.textEntry.delete('0.0', END)

            message = message.lstrip()
            if message != "":
                self.chatWindowPrintText("Me: "+message)
                self.log.msg("Client Send: " + message)
                self.server.sendMessage(self.username + ": " + message, selectedIP, selectedPort)
                return True
        return False

    # Takes the result from the DHT and parses out the IP and port
    # TODO: This will have to be modified when we have to resolve multiple IP/PORT pairs for NAT etc.
    def get_contact_location(self, result, contact):
        if result is not None and result != []:
            contact['ip'] = result[0][0]
            contact['port'] = result[0][1]


    # Refreshes the IPs of all of the contacts. Because of async nature of Twisted, this may not show right away.
    def refreshAvailIP(self):
        self.log.msg("Refreshing Contact List automagically")
        for contact in self.Contacts:
            # This adds the get_ip function to the server callback list. Will do so for each contact
            #server.get(contact['key'] + contact['username']).addCallback(get_contact_location, contact)
            self.server.getContactInfo(contact['key'] + contact['username'], contact['key']).\
                addCallback(self.get_contact_location, contact)

        #clear the listboxes in the GUI of old values
        self.ConnectionsList[0].delete(0, END)
        self.ConnectionsList[1].delete(0, END)

        for contact in self.Contacts:
            contactName = contact['username']
            contactIP = contact['ip']
            if contactIP is "" or contactIP is None:
                contactIP = "Offline"

            # add the new values to the GUI
            self.ConnectionsList[0].insert(END, contactName)
            self.ConnectionsList[1].insert(END, contactIP)

    # update the global selected IP address
    def updateSelectedContact(self):

        selectedName = self.ConnectionsList[0].get(ACTIVE)
        selectedIP = self.ConnectionsList[1].get(ACTIVE)

        for contact in self.Contacts:
            if contact['ip'] == selectedIP and contact['username'] == selectedName:
                return contact
        return None

    #method is called by a ConnectionsList list box when the selection is changed. Updates other accordingly
    def syncListSelections(self, evt=None, listIndex=0):

        otherindex = (listIndex +1) % 2
        toset = self.ConnectionsList[listIndex].curselection()
        self.ConnectionsList[otherindex].activate(toset[0])

    def closeProgram(self):
        reactor.stop()

    #Set up the GUI and containers, frames, lists, etc. before running the program loop
    def initializeGUI(self):
        #set up the main window
        root = Tk()
        root.title("Encrypted P2P Chat GUI")
        root.protocol('WM_DELETE_WINDOW', self.closeProgram)

        mainFrame = Frame(root)
        mainFrame.pack()

        self.ConnectionsList.append(Listbox(mainFrame, selectmode=SINGLE))
        self.ConnectionsList.append(Listbox(mainFrame, selectmode=SINGLE))

        self.ConnectionsList[0].grid(row=0, column=0)
        self.ConnectionsList[1].grid(row=0, column=1)

        self.ConnectionsList[0].bind("<<ListboxSelect>>", lambda e:self.syncListSelections(e, listIndex=0))
        self.ConnectionsList[1].bind("<<ListboxSelect>>", lambda e:self.syncListSelections(e, listIndex=1))

        #set up chat window with scroll bar
        chatTextFrame = Frame(root)

        scrollbar = Scrollbar(chatTextFrame)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.chatWindow = Text(chatTextFrame, height=8, state=DISABLED)
        self.chatWindow.pack(side=LEFT, expand=YES, fill=BOTH)

        scrollbar.config(command=self.chatWindow.yview)
        self.chatWindow.config(yscrollcommand=scrollbar.set)

        chatTextFrame.pack(expand=YES, fill=BOTH)

        #set up user text field for input
        chatEntryFrame = Frame(root)

        scrollbar2 = Scrollbar(chatEntryFrame)
        scrollbar2.pack(side=RIGHT, fill=Y)

        self.textEntry = Text(chatEntryFrame, height=2)
        self.textEntry.pack(side=LEFT, expand=YES, fill=BOTH)

        scrollbar2.config(command=self.textEntry.yview)

        chatEntryFrame.pack(expand=YES, fill=BOTH)

        #Bind key events to method calls
        self.textEntry.bind("<Key>", self.sendChatMessage)
        self.textEntry.bind("<KeyRelease>", self.clearText)


        #set up buttons and their method calls
        refreshButton = Button(root, text="Refresh List", command=self.refreshAvailIP)
        refreshButton.pack(side=LEFT)

        exitButton = Button(root, text="Exit Program", command=self.closeProgram)
        exitButton.pack(side=RIGHT)

        tksupport.install(root)