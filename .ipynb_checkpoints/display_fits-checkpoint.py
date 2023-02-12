from tkinter import *
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from astropy.io import fits
from tkinter import font as tkFont  # for convenience

homedir = os.getenv("HOME")

root = Tk()
root.title('FITS Viewer')

#set up font preference
helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')

path_to_dir = homedir+'/UGC06711/'
filenames = os.listdir(path_to_dir)
os.chdir(path_to_dir)

data_list = []

for index in range(len(filenames)):
    data=fits.getdata(filenames[index])
    data_list.append(data)

plt.figure(figsize=(3,3))
im = plt.imshow(data_list[0],origin='lower')
plt.title(filenames[index],fontsize=10)
canvas = FigureCanvasTkAgg(plt.gcf(), master=root)

#entry widget...to enter data.
e = Entry(root, width=35, borderwidth=5, bg='black',fg='lime green', font=('Arial 20'))
e.grid(row=0,column=4)

#command to change colormap of the cutout pixels
change_colormap_manual = lambda: (im.set_cmap(e.get()), canvas.draw())

label = canvas.get_tk_widget()
label.grid(row=0,column=0,columnspan=3,rowspan=3)

def forward(image_index):
    #call variables
    global label
    global button_forward
    global button_back
    
    label.delete('all')
    plt.close()
    
    plt.figure(figsize=(3,3))
    im = plt.imshow(data_list[image_index],origin='lower')
    plt.title(filenames[image_index],fontsize=10)
    
    canvas = FigureCanvasTkAgg(plt.gcf(), master=root)
    label = canvas.get_tk_widget()
    button_forward = Button(root, text='>>', font=helv20, fg='magenta', command=lambda: forward(image_index+1))
    button_back = Button(root, text='<<', font=helv20, fg='magenta', command=lambda: back(image_index-1))
    
    if image_index == len(data_list)-1:
        button_forward = Button(root, text='>>', state=DISABLED)
    
    change_colormap_manual = lambda: (im.set_cmap(e.get()), canvas.draw())
    color_button = Button(root, text='Set Manual Color Scheme', font=helv20, command=change_colormap_manual)
    color_button.grid(row=1,column=4)
    
    label.grid(row=0,column=0,columnspan=3,rowspan=3)
    button_back.grid(row=3,column=0)
    button_forward.grid(row=3,column=2)
    
def back(image_index):
    global label
    global button_forward
    global button_back
    
    label.delete('all')
    plt.close()
    
    plt.figure(figsize=(3,3))
    im = plt.imshow(data_list[image_index],origin='lower')
    plt.title(filenames[image_index],fontsize=10)
    
    canvas = FigureCanvasTkAgg(plt.gcf(), master=root)
    label = canvas.get_tk_widget()
    button_forward = Button(root, text='>>', font=helv20, fg='magenta', command=lambda: forward(image_index+1))
    button_back = Button(root, text='<<', font=helv20, fg='magenta', command=lambda: back(image_index-1))
    
    if image_index == 0:
        button_back = Button(root, text='<<', font=helv20, state=DISABLED)
    
    change_colormap_manual = lambda: (im.set_cmap(e.get()), canvas.draw())
    color_button = Button(root, text='Set Manual Color Scheme', font=helv20, command=change_colormap_manual)
    color_button.grid(row=1,column=4)
    
    label.grid(row=0,column=0,columnspan=3,rowspan=3)
    button_back.grid(row=3,column=0)
    button_forward.grid(row=3,column=2)

color_button = Button(root,text='Set Manual Color Scheme', font=helv20, command=change_colormap_manual)
button_back = Button(root, text='<<', font=helv20, fg='magenta', command=lambda: back(0), state=DISABLED)
button_forward = Button(root, text='>>', font=helv20, fg='magenta', command=lambda: forward(1))
button_quit = Button(root, text='Terminate', padx=20, pady=10, font=helv20, command=root.quit)

color_button.grid(row=1,column=4) 
button_back.grid(row=3,column=0)
button_quit.grid(row=3,column=1)
button_forward.grid(row=3,column=2)

#control dynamic resizing of widgets
for i in range(5):
    root.grid_columnconfigure(i,weight=1)
    root.grid_rowconfigure(i,weight=1)

root.mainloop()