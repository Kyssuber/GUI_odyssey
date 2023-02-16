from tkinter import *
from PIL import ImageTk, Image

root = Tk()
root.title("Cabbage")

#frame --> box with a border; helpful for visual organization of widgets and such.

frame = LabelFrame(root, text='This is my Frame...', padx=5, pady=5)
frame.pack(padx=10,pady=10)

b=Button(frame, text='button')
b2 = Button(frame,text='or here')

#even though frame is packed, within the frame can be a grid system!
b.grid(row=0,column=0)
b2.grid(row=1,column=1)

root.mainloop()