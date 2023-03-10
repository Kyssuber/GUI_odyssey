'''
GOAL: in a GUI, display and loop through all .fits files (if any) in user directory. 
Gnarly features: status label, forward/back buttons in order to browse images, entry bar to change color schemes. 
'''

#import various libraries
from tkinter import *
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.wcs import WCS
from tkinter import font as tkFont  # for convenience
from tkinter import messagebox # for convenience

homedir=os.getenv("HOME")

#set up main GUI window
root = Tk()
root.title('FITS Viewer')
root.geometry("1100x700")

#create a font preference
helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')

#create two frames, side-by-side.
frame_display = LabelFrame(root,text='Display',padx=5,pady=5)
frame_display.grid(row=0,column=0,rowspan=10)

frame_widgets = LabelFrame(root,text='Edit Color Scheme',padx=2,pady=2)
frame_widgets.grid(row=0,column=1)

#create a wittle section to print x,y coordinates of cursor position (when left-clicked)
frame_coord = LabelFrame(root,text='Image Coordinates & Value',padx=5,pady=5)
frame_coord.grid(row=5,column=1,sticky='se')

#lastly, a frame for a few buttons
frame_buttons = LabelFrame(root,text='Features',padx=5,pady=5)
frame_buttons.grid(row=2,column=1)

png_name = Entry(frame_buttons, width=35, borderwidth=2, bg='black',fg='lime green', font=('Arial 20'))
png_name.insert(0,'figurename.png')
png_name.grid(row=0,column=0)   

#add empty labels for displaying coords and px values
labelle = Label(frame_coord,text='(x_coord, y_coord)',font=helv20)
labelle.grid(row=0,column=0)

labelle3 = Label(frame_coord,text='(RA (deg), DEC(deg))',font=helv20)
labelle3.grid(row=2,column=0)

labelle2 = Label(frame_coord,text='Pixel Value:  ',font=helv20)
labelle2.grid(row=1,column=0)

textbox = "GOAL: display and loop through all .fits files (if any) in user directory. Gnarly features: status label, forward/back buttons in order to browse images, usw. In color scheme textbox, type a matplotlib color arg (e.g., rainbow, viridis, gray, cool), then click the button widget underneath. The user can do likewise with the save feature, replacing the entry text with the desired filename.png to save a .PNG of the current canvas display to the Desktop. Lastly, the canvas is click-interactive: left-click on an image pixel, and the output will modify the pixel's Cartesian coordinates, its RA and DEC coordinates, and its pixel value in the bottom-right frame."

#create command function to print info popup message
#Different message types: showinfo, showwarning, showerror, askquestion, askokcancel, askyesno
def popup():
    messagebox.showinfo('Unconventional README.md',textbox)

#create command function to extract coordinates aT ThE cLiCk Of A bUtToN
#filename should be file_title[index] --> if title is valid, then "try" will proceed as normal. if file is invalid, then "except" will appear.
def plotClick(event, filename):
    x = event.xdata
    y = event.ydata
    
    try:   #if x,y are within the plot bounds, then xdata and ydata will be floats; can round.
        x = np.round(x,2)
        y = np.round(y,2)

        image = fits.open(filename)
        #if im is .fits and not .fits.fz, use [0] instead of [1]
        if filename[-3:] == '.fz':
            header = image[1].header
        else:
            header = image[0].header
        w=WCS(header)

        RA, DEC = w.all_pix2world(x,y,0)

        RA = np.round(RA,3)
        DEC = np.round(DEC,3)
        
        labelle.config(text=f'({x}, {y})',font=helv20)
        labelle3.config(text=f'({RA}, {DEC})',font=helv20)
    
    except:   #if outside of plot bounds, then xdata and ydata are NoneTypes; cannot round.
        labelle.config(text=f'({x}, {y})',font=helv20)  
        labelle3.config(text=f'({None}, {None})',font=helv20)

#create command function to extract a pixel value aT ThE cLiCk Of A bUtToN
def plotValue(event,im_dat,length):
    x=event.xdata
    y=event.ydata
    
    try:
        x = int(x)
        y = int(y)
        value = im_dat[y][x]
    except:
        value = 'None'
    
    labelle2.config(text=f'Pixel Value: {round(value,4)}',font=helv20)

#command function to save a figure as shown, placed in (on?) Desktop.
def saveFig():
    plt.savefig(homedir+'/Desktop/'+str(png_name.get()),dpi=250)
###########

#grab current directory, generate list of strings representing item names in said directory
path_to_dir = os.getcwd()
filenames = os.listdir(path_to_dir)

#empty data list
data_list = []

#titles for plt.imshow; if a 2D image, then title will be same as filename.
file_titles = []

#filters out directory items that are not fits files; adds fits data from correct files to data_list.
for file in np.asarray(filenames):
    if ('.fits' not in file):
        filenames.remove(file)
    else:
        data_list.append(fits.getdata(file))

#if there are no relevant fits files, then errors abound.
if filenames==0:
    print('No FITS files are in cwd. You may encounter errors when compiling the GUI.')

#entry widget...to enter colorbar data.
e = Entry(frame_widgets, width=35, borderwidth=5, bg='black',fg='lime green', font=('Arial 20'))
e.grid(row=0,column=0)     

#some .fits files in the directory may not be 2D images; in this case, I simply plot a 200x200 matrix of noise,
#since python dislikes trying to plt.imshow a data table. 
plt.figure(figsize=(3,3))

try:
    dat = data_list[0]
    im = plt.imshow(dat,origin='lower')
    plt.title(filenames[0],fontsize=10)
    file_titles.append(filenames[0])
    
except:
    dat=np.random.random((200,200))
    im = plt.imshow(dat,origin='lower')
    plt.title(filenames[0]+' not a 2D image.',fontsize=6)   
    file_titles.append(filenames[0]+'.')

im_length = len(dat)

#set up canvas
canvas = FigureCanvasTkAgg(plt.gcf(), master=frame_display) 
#binds left-click to extract the plot's x,y pixel coordinates, and the value at these coordinates
canvas.mpl_connect('button_press_event', lambda event: plotClick(event, file_titles[0]))
canvas.mpl_connect('button_press_event',lambda event: plotValue(event, dat, im_length))
    
#create a label instance for the canvas window
label = canvas.get_tk_widget()
#label.config(width=800, height=800)
label.grid(row=0,column=0,columnspan=3,rowspan=4)
    
#command to change colormap of the cutout pixels
change_colormap_manual = lambda: (im.set_cmap(e.get()), canvas.draw())

#add status bar
n_images = str(len(filenames))
status = Label(frame_display, text="Image 1 of {}".format(n_images), bd=1, relief=SUNKEN)

#define the 'forward button widget'
def forward(image_index):
    
    #call variables
    global label
    global button_forward
    global button_back
    global n_images
    
    #eliminate the current canvas object, then close the plot. I add plt.close() for memory/performance purposes
    label.delete('all')
    plt.close()
    
    #some .fits files in the directory may not be 2D images; in this case, I simply plot a 200x200 matrix of noise,
    #since python dislikes trying to plt.imshow a data table. 
    plt.figure(figsize=(3,3))
    try:
        dat = data_list[image_index]
        im = plt.imshow(dat,origin='lower')
        plt.title(filenames[image_index],fontsize=10)        
        file_titles.append(filenames[image_index])
    except:
        dat=np.random.random((200,200))
        im = plt.imshow(dat,origin='lower')
        plt.title(filenames[image_index]+' not a 2D image.',fontsize=6)
        file_titles.append(filenames[image_index]+'.')
    
    im_length = len(dat)
    
    canvas = FigureCanvasTkAgg(plt.gcf(), master=frame_display)
    #binds left-click to extract the plot's x,y pixel coordinates, and the pixel value at these coordinates
    canvas.mpl_connect('button_press_event',lambda event: plotClick(event, file_titles[image_index]))
    canvas.mpl_connect('button_press_event',lambda event: plotValue(event,dat,im_length))
    
    #create a label instance for the canvas window
    label = canvas.get_tk_widget()

    #forward button will bring user to the next, next image (image_index+1). sort of neat how you can call the function within the function. Likewise with the back button.
    button_forward = Button(frame_display, text='>>', font=helv20, fg='magenta', command=lambda: forward(image_index+1))
    button_back = Button(frame_display, text='<<', font=helv20, fg='magenta', command=lambda: back(image_index-1))
    
    #if user has arrived at the last image, then disable the forward button.
    if image_index == len(filenames)-1:
        button_forward = Button(frame_display, text='>>', font=helv20, state=DISABLED)
    
    #new image; new colorbar command. I *could* create a function for this line, but I can't be bothered.
    change_colormap_manual = lambda: (im.set_cmap(e.get()), canvas.draw())
    
    #add color button
    color_button = Button(frame_widgets, text='Set Manual Color Scheme', font=helv20, command=change_colormap_manual)
    color_button.grid(row=1,column=0)
    
    #update status label
    status = Label(frame_display, text="Image {} of ".format(str(image_index+1))+n_images, bd=1, relief=SUNKEN)
    
    #re-insert the info button...
    info_button = Button(frame_display, text='Click for Info',padx=15,pady=5,font='Ariel 10', command=popup)
    
    #add status and...every other button.
    label.grid(row=0,column=0,columnspan=3,rowspan=4)
    button_back.grid(row=4,column=0)
    button_forward.grid(row=4,column=2)
    status.grid(row=5,column=0,columnspan=3,sticky=W+E)
    info_button.grid(row=5,column=2,sticky='ne')
    
#define the 'back button' widget (see above for notes)    
def back(image_index):
    global label
    global button_forward
    global button_back
    global n_images
    
    label.delete('all')
    plt.close()
    
    #some .fits files in the directory may not be 2D images; in this case, I simply plot a 200x200 matrix of noise,
    #since python dislikes trying to plt.imshow a data table. 
    plt.figure(figsize=(3,3))
    try:
        dat = data_list[image_index]
        im = plt.imshow(dat,origin='lower')
        plt.title(filenames[image_index],fontsize=10)
        file_titles.append(filenames[image_index])
    except:
        dat=np.random.random((200,200))
        im = plt.imshow(dat,origin='lower')
        plt.title(filenames[image_index]+' not a 2D image.',fontsize=6)
        file_titles.append(filenames[image_index]+'.')
    
    im_length = len(dat)
    
    canvas = FigureCanvasTkAgg(plt.gcf(), master=frame_display)
    #binds left-click to extract the plot's x,y pixel coordinates, and the pixel value at these coordinates
    canvas.mpl_connect('button_press_event',lambda event: plotClick(event, file_titles[image_index]))
    canvas.mpl_connect('button_press_event',lambda event: plotValue(event,dat,im_length))
    
    label = canvas.get_tk_widget()
    
    button_forward = Button(frame_display, text='>>', font=helv20, fg='magenta', command=lambda: forward(image_index+1))
    button_back = Button(frame_display, text='<<', font=helv20, fg='magenta', command=lambda: back(image_index-1))
    
    if image_index == 0:
        button_back = Button(frame_display, text='<<', font=helv20, state=DISABLED)
    
    change_colormap_manual = lambda: (im.set_cmap(e.get()), canvas.draw())
    color_button = Button(frame_widgets, text='Set Manual Color Scheme', font=helv20, command=change_colormap_manual)
    color_button.grid(row=1,column=0)
    
    status = Label(frame_display, text="Image {} of ".format(str(image_index+1))+n_images, bd=1, relief=SUNKEN)
    
    info_button = Button(frame_display, text='Click for Info',padx=15,pady=5,font='Ariel 10', command=popup)
    
    label.grid(row=0,column=0,columnspan=3,rowspan=4)
    button_back.grid(row=4,column=0)
    button_forward.grid(row=4,column=2)
    status.grid(row=5,column=0,columnspan=3,sticky=W+E)
    info_button.grid(row=5,column=2,sticky='ne')

#in the initial frames, define and add the buttons! And the status! 
color_button = Button(frame_widgets,text='Set Manual Color Scheme', font=helv20, command=change_colormap_manual)
button_back = Button(frame_display, text='<<', font=helv20, fg='magenta', command=lambda: back(0), state=DISABLED)
button_forward = Button(frame_display, text='>>', font=helv20, fg='magenta', command=lambda: forward(1))
button_quit = Button(frame_display, text='Terminate', padx=20, pady=10, font=helv20, command=root.quit)
save_button = Button(frame_buttons,text='Save .png',padx=20,pady=10,font=helv20,command=saveFig)
info_button = Button(frame_display, text='Click for Info',padx=5,pady=5,font='Ariel 10', command=popup)

color_button.grid(row=1,column=0) 
button_back.grid(row=4,column=0)
button_quit.grid(row=4,column=1)
button_forward.grid(row=4,column=2)
save_button.grid(row=1,column=0)
info_button.grid(row=5,column=2,sticky='ne')

status.grid(row=5,column=0,columnspan=3,sticky=W+E)

#control dynamic resizing of widgets
for i in range(5):
    frame_display.grid_columnconfigure(i,weight=1)
    frame_display.grid_rowconfigure(i,weight=1)
    frame_widgets.grid_columnconfigure(i,weight=1)
    frame_widgets.grid_rowconfigure(i,weight=1)
    frame_coord.grid_columnconfigure(i,weight=1)
    frame_coord.grid_rowconfigure(i,weight=1)
    frame_buttons.grid_columnconfigure(i,weight=1)
    frame_buttons.grid_rowconfigure(i,weight=1)
    
    root.grid_columnconfigure(i,weight=1)
    root.grid_rowconfigure(i,weight=1)

#annnnnnnnd, activate.
if __name__ == '__main__':
    root.mainloop()
    root.destroy()