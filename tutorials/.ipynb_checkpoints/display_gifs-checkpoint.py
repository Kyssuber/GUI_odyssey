from tkinter import *
from PIL import ImageTk, Image
import os
homedir = os.getenv("HOME")

root = Tk()
root.title('Garlic Knots')
pathname='/Users/k215c316/Downloads/dhelm.gif'
pathname2='/Users/k215c316/Desktop/images/budget_cut_grond.gif'
pathname3='/Users/k215c316/Desktop/images/lurking_redstar.gif'

#currently using .gif image because its dimensions are less unwieldy than with the .png image.
im = ImageTk.PhotoImage(Image.open(pathname))
im2 = ImageTk.PhotoImage(Image.open(pathname2))
im3 = ImageTk.PhotoImage(Image.open(pathname3))

im_list = [im,im2,im3]

label = Label(image=im)
label.grid(row=0,column=0,columnspan=3)


def forward(image_index):
    
    #call variables
    global label
    global button_forward
    global button_back
    
    label.grid_forget()   #erases image from screen
    label = Label(image=im_list[image_index])
    button_forward = Button(root, text='>>', command=lambda: forward(image_index+1))
    button_back = Button(root, text='<<', command=lambda: back(image_index-1))
    
    if image_index == len(im_list)-1:
        button_forward = Button(root, text='>>', state=DISABLED)
    
    label.grid(row=0,column=0,columnspan=3)
    button_back.grid(row=1,column=0)
    button_forward.grid(row=1,column=2)
    

def back(image_index):
    
    global label
    global button_forward
    global button_back
    
    label.grid_forget()   #erases image from screen
    label = Label(image=im_list[image_index])
    button_forward = Button(root, text='>>', command=lambda: forward(image_index+1))
    button_back = Button(root, text='<<', command=lambda: back(image_index-1))
    
    if image_index == 0:
        button_back = Button(root, text='<<', state=DISABLED)

    label.grid(row=0,column=0,columnspan=3)
    button_back.grid(row=1,column=0)
    button_forward.grid(row=1,column=2)


button_back = Button(root, text='<<',command=lambda: back(0), state=DISABLED)
button_forward = Button(root, text='>>',command=lambda: forward(1))
button_quit = Button(root, text='Terminate', padx=20, pady=10, command=root.quit)

button_back.grid(row=1,column=0)
button_quit.grid(row=1,column=1)
button_forward.grid(row=1,column=2)


root.mainloop()