# A test Tkinter GUI

try: #python 2
    from Tkinter import *
except ImportError: #python 3
    from tkinter import *


#set up the main window
root = Tk()
root.title("Encrypted P2P")


iPList = {"192.168.0.1", "0.0.0.0"}
listB = Listbox(root)

for item in iPList:
    listB.insert(0, item)

listB.pack()
root.mainloop()

# create a fame which will hold all of the UI contents
#mainframe = ttk.Frame(root, padding = "5, 5, 5, 5")
# allow frame expansion when resizing
#mainframe.rowconfigure(0, Weight=1)
#mainframe.columnconfigure(0, Weight=1)