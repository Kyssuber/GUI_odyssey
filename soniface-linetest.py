'''
Class layout adapted from 
https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter/7557028#7557028
'''

from midiutil import MIDIFile
from audiolazy import str2midi
from pygame import mixer                    #this library is what causes the loading delay methinks

import tkinter as tk
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#from matplotlib import pyplot as plt      #don't use, since closing GUI doesn't close pyplot!
                                           #this does add a bit more clunkiness to the code, however.
                                           #I did not create the rules. do not sue me.

from matplotlib import figure              #see self.fig, self.ax.

import matplotlib                          #I need this for matplotlib.use. sowwee.
matplotlib.use('TkAgg')                    #strange error messages will appear otherwise.

from scipy.stats import scoreatpercentile
from astropy.visualization import simple_norm
from astropy.io import fits
from astropy.wcs import WCS
from tkinter import font as tkFont
from tkinter import messagebox
from tkinter import filedialog
import glob

import sys
from io import BytesIO

from scipy.stats import scoreatpercentile
from astropy.visualization import simple_norm

homedir = os.getenv('HOME')

#create main window container, into which the first page will be placed.
class App(tk.Tk):
    
    def __init__(self, *args, **kwargs):          #INITIALIZE; will always run when App class is called.
        tk.Tk.__init__(self, *args, **kwargs)     #initialize tkinter; args are parameter arguments, kwargs can be dictionary arguments
        
        self.title('VirgoSoni: Sonification of Nearby Galaxies')
        self.geometry('1000x700')
        self.resizable(True,True)
        self.rowspan=10
        
        #will be filled with heaps of frames and frames of heaps. 
        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)     #fills entire container space
        container.grid_rowconfigure(0,weight=1)
        container.grid_columnconfigure(0,weight=1)

        ## Initialize Frames
        self.frames = {}     #empty dictionary
        frame = MainPage(container, self)   #define frame  
        self.frames[MainPage] = frame     #assign new dictionary entry {MainPage: frame}
        frame.grid(row=0,column=0,sticky='nsew')   #define where to place frame within the container...CENTER!
        for i in range(self.rowspan):
            frame.columnconfigure(i, weight=1)
            frame.rowconfigure(i, weight=1)
        
        self.show_frame(MainPage)  #a method to be defined below (see MainPage class)
    
    def show_frame(self, cont):     #'cont' represents the controller, enables switching between frames/windows...I think.
        frame = self.frames[cont]
        frame.tkraise()   #will raise window/frame to the 'front;' if there is more than one frame, quite handy.
        
        
#inherits all from tk.Frame; will be on first window
class MainPage(tk.Frame):    
    
    def __init__(self, parent, controller):
        
        #these variables will apply to the self.drawSq function, if the user desires to use it.
        self.bound_check=None
        self.x1=None
        self.x2=None
        self.y1=None
        self.y2=None
        self.angle=0
        
        #defines the number of rows/columns to resize when resizing the entire window.
        self.rowspan=10
        
        #define a font
        self.helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')
        
        self.textbox="GOAL: Generate and interact with a 2D sonified galaxy cutout. \n \n GENERAL INSTRUCTIONS: \n \n (1) Enter filepath into the top entry box click 'Browse' in order to search your local machine's good ol' inventory. Then click 'Enter'. \n \n (2) Clicking 'Sonify' will create consecutive vertical strips of pixels, calculate the mean value of each band, and map the resulting array of means to a MIDI note which is ultimately translated into a piano key. [Presently, the only chord available is D-major.] The full sonification will play automatically upon clicking the button, using the default y scale (scales the mean pixel data, ydata**yscale), min and max velocities (the min and max volume, respectively, ranging from 0 to 127), the BPM (beats per minute -- higher BPM begets a speedier tune), and the min and max xrange. The user can edit these values to manipulate the sound, clicking 'Sonify' once more to audibly harvest the outcome of their fiddling. \n \n (3) Left-clicking the image will allow the user to visualize an individual column of sonified pixels (red bar), as well as simultaneously hear the MIDI note corresponding to the mean pixel value of that column. The bottom-right widget of the GUI handily displays this mean value if the user is so inclined to know. \n \n (4) If the user wishes to view another galaxy, they may click 'Browse' to find a second FITS file and go wild. I certainly cannot thwart their efforts, for I am a simple text box."
        
        #first frame...
        tk.Frame.__init__(self,parent)
        
        #NOTE: columnconfigure and rowconfigure below enable minimization and maximization of window to also affect widget size
        
        #create display frame, which will hold the canvas and a few button widgets underneath.
        self.frame_display=tk.LabelFrame(self,text='Display',
                                         font='Vendana 15',padx=5,pady=5)
        self.frame_display.grid(row=0,column=0,rowspan=8)
        for i in range(self.rowspan):
            self.frame_display.columnconfigure(i, weight=1)
            self.frame_display.rowconfigure(i, weight=1)
        
        #create buttons frame, which currently only holds the 'save' button, 'browse' button, and entry box.
        self.frame_buttons=tk.LabelFrame(self,text='File Browser',padx=5,pady=5)
        self.frame_buttons.grid(row=2,column=1,columnspan=2)
        for i in range(self.rowspan):
            self.frame_buttons.columnconfigure(i, weight=1)
            self.frame_buttons.rowconfigure(i, weight=1)
            
        #create soni frame, which holds the event button for converting data into sound (midifile).
        #there are also heaps of text boxes with which the user can manipulate the sound conversion parameters
        self.frame_soni=tk.LabelFrame(self,text='Soni Parameters (Click "Sonify" to play)',padx=5,pady=5)
        self.frame_soni.grid(row=6,column=2,sticky='se')
        for i in range(self.rowspan):
            self.frame_soni.columnconfigure(i, weight=1)
            self.frame_soni.rowconfigure(i, weight=1)
        
        #create value frame, which holds the event labels for the mean pixel value.
        self.frame_value=tk.LabelFrame(self,padx=5,pady=5)
        self.frame_value.grid(row=4,column=2,sticky='se')
        for i in range(self.rowspan):
            self.frame_value.columnconfigure(i, weight=1)
            self.frame_value.rowconfigure(i, weight=1)
        
        #create box frame --> check boxes for lines vs. squares when interacting with the figure canvas
        self.frame_box = tk.LabelFrame(self,text='Change Rectangle Angle',padx=5,pady=5)
        self.frame_box.grid(row=6,column=1,sticky='s')
        for i in range(self.rowspan):
            self.frame_box.columnconfigure(i, weight=1)
            self.frame_box.rowconfigure(i, weight=1)
        
        self.galaxy_to_display()
        '''
        INSERT FUNCTIONS TO RUN HERE.
        '''
        self.initiate_vals()
        self.add_info_button()
        self.populate_soni_widget()
        self.populate_box_widget()
        self.init_display_size()
    
    def populate_box_widget(self):
        self.var = tk.IntVar()
        self.angle_box = tk.Entry(self.frame_box, width=15, borderwidth=2, bg='black', fg='lime green',
                                  font='Arial 20')
        self.angle_box.insert(0,'angle (0-360)')
        self.angle_box.grid(row=0,column=0,columnspan=5)
        self.add_angle_buttons()
    
    def initiate_vals(self):
        self.val = tk.Label(self.frame_value,text='Pixel Value: ',font='Arial 20')
        self.val.grid(row=1,column=0)
        self.line_check = tk.Checkbutton(self.frame_value,text='Switch to Lines',
                                         onvalue=1,offvalue=0,command=self.change_canvas_event,
                                         variable=self.var,font='Arial 20')
        self.line_check.grid(row=0,column=0)
    
    def galaxy_to_display(self):
        self.path_to_im = tk.Entry(self.frame_buttons, width=35, borderwidth=2, bg='black', fg='lime green', 
                                   font='Arial 20')
        self.path_to_im.insert(0,'Type path/to/image.fits or click "Browse"')
        self.path_to_im.grid(row=0,column=0,columnspan=2)
        self.add_browse_button()
        self.add_enter_button()
        
    def populate_soni_widget(self):
        
        self.add_midi_button()
        
        #create all entry textboxes (with labels and initial values), midi button
        
        ylab = tk.Label(self.frame_soni,text='yscale').grid(row=0,column=0)
        self.y_scale_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.y_scale_entry.insert(0,'0.5')
        self.y_scale_entry.grid(row=0,column=1,columnspan=1)
        
        vmin_lab = tk.Label(self.frame_soni,text='Min Velocity').grid(row=1,column=0)
        self.vel_min_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.vel_min_entry.insert(0,'10')
        self.vel_min_entry.grid(row=1,column=1,columnspan=1)
        
        vmax_lab = tk.Label(self.frame_soni,text='Max Velocity').grid(row=2,column=0)
        self.vel_max_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.vel_max_entry.insert(0,'100')
        self.vel_max_entry.grid(row=2,column=1,columnspan=1)
        
        bpm_lab = tk.Label(self.frame_soni,text='BPM').grid(row=3,column=0)
        self.bpm_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                  font='Arial 15')
        self.bpm_entry.insert(0,'35')
        self.bpm_entry.grid(row=3,column=1,columnspan=1)
        
        xminmax_lab = tk.Label(self.frame_soni,text='xmin, xmax').grid(row=4,column=0)
        self.xminmax_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green',
                                      font='Arial 15')
        self.xminmax_entry.insert(0,'x1, x2')
        self.xminmax_entry.grid(row=4,column=1,columnspan=1)
        
        yminmax_lab = tk.Label(self.frame_soni,text='ymin, ymax').grid(row=5,column=0)
        self.yminmax_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.yminmax_entry.insert(0,'y1, y2')
        self.yminmax_entry.grid(row=5,column=1,columnspan=1)
        
        program_lab = tk.Label(self.frame_soni,text='Instrument (0-127)').grid(row=6,column=0)
        self.program_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.program_entry.insert(0,'0')
        self.program_entry.grid(row=6,column=1,columnspan=1)
        
        duration_lab = tk.Label(self.frame_soni,text='Duration (sec)').grid(row=7,column=0)
        self.duration_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                       font='Arial 15')
        self.duration_entry.insert(0,'1')
        self.duration_entry.grid(row=7,column=1,columnspan=1)
    
    def init_display_size(self):
        #aim --> match display frame size with that once the canvas is added
        #the idea is for consistent aestheticsTM
        self.fig = figure.Figure(figsize=(5,5))
        self.ax = self.fig.add_subplot()
        self.im = self.ax.imshow(np.zeros(100).reshape(10,10))
        self.ax.set_title('Blank Canvas',fontsize=15)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_display) 
        
        #activate the draw square/rectangle/quadrilateral/four-sided polygon event
        self.connect_event=self.canvas.mpl_connect('button_press_event',self.drawSqRec)
        
        #add canvas 'frame'
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=3,rowspan=6)
    
    def add_info_button(self):
        self.info_button = tk.Button(self.frame_display, text='Click for Info', padx=15, pady=10, font='Ariel 20', command=self.popup)
        self.info_button.grid(row=8,column=1)
    
    def add_browse_button(self):
        self.button_explore = tk.Button(self.frame_buttons ,text="Browse", padx=20, pady=10, font=self.helv20, 
                                        command=self.browseFiles)
        self.button_explore.grid(row=1,column=0)
        
    def add_enter_button(self):
        self.path_button = tk.Button(self.frame_buttons, text='Enter', padx=20, pady=10, font=self.helv20, 
                                     command=self.initiate_canvas)
        self.path_button.grid(row=1,column=1)
    
    def add_midi_button(self):
        self.midi_button = tk.Button(self.frame_soni, text='Sonify', padx=20, pady=10, font=self.helv20, 
                                     command=self.midi_setup_bar)
        self.midi_button.grid(row=8,column=0,columnspan=2)
    
    #def add_angle_buttons(self):
    #    self.angle_button = tk.Button(self.frame_box, text='Rotate',padx=20,pady=10,font=self.helv20,
    #                                  command=self.create_rectangle)
    #    self.angle_button.grid(row=2,column=0,columnspan=3)
    
    def add_angle_buttons(self):
        self.angle_button = tk.Button(self.frame_box, text='Rotate',padx=5,pady=10,font=self.helv20,
                                      command=self.create_rectangle)
        self.angle_button.grid(row=2,column=1,columnspan=3)
        self.incarrow = tk.Button(self.frame_box, text='+1',padx=1,pady=10,font='Ariel 14',
                                  command=self.increment)
        self.incarrow.grid(row=2,column=4,columnspan=1)                          
        self.decarrow = tk.Button(self.frame_box, text='-1',padx=1,pady=10,font='Ariel 14',
                                  command=self.decrement)
        self.decarrow.grid(row=2,column=0,columnspan=1)
    
    def increment(self):
        self.angle += 1
        self.angle_box.delete(0,tk.END)
        self.angle_box.insert(0,str(self.angle))
    
    def decrement(self):
        self.angle -= 1
        self.angle_box.delete(0,tk.END)
        self.angle_box.insert(0,str(self.angle))
    
    def initiate_canvas(self):
        
        #delete any and all miscellany (galaxy image, figure) from the canvas (created using 
        #self.init_display_size())
        self.label.delete('all')
        self.ax.remove()
        
        self.dat = fits.getdata(str(self.path_to_im.get()))
        
        #many cutouts, especially those in the r-band, have pesky foreground stars and other artifacts, which will invariably dominate the display of the image stretch. one option is that I can grab the corresponding mask image for the galaxy and create a 'mask bool' of 0s and 1s, then multiply this by the image in order to dictate v1, v2, and the normalization *strictly* on the central galaxy pixel values. 
        
        full_filepath = str(self.path_to_im.get()).split('/')
        full_filename = full_filepath[-1]
        split_filename = full_filename.replace('.','-').split('-')   #replace .fits with -fits, then split all
        galaxyname = split_filename[0]
        galaxyband = split_filename[3]
        try:
            if str(galaxyband)=='r':
                mask_path = glob.glob('/Users/k215c316/vf_html_mask/all_input_fits/'+galaxyname+'*'+'r-mask.fits')[0]
            if galaxyband=='W3':
                mask_path = glob.glob('/Users/k215c316/vf_html_mask/all_input_fits/'+galaxyname+'*'+'wise-mask.fits')[0]
            mask_image = fits.getdata(mask_path)
            self.mask_bool = ~(mask_image>0)
        
        except:
            self.mask_bool = np.zeros((len(self.dat),len(self.dat)))+1
            print('Mask image not found; proceeded with default v1, v2, and normalization values.')
        
        v1 = scoreatpercentile(self.dat*self.mask_bool,0.5)
        v2 = scoreatpercentile(self.dat*self.mask_bool,99.9)
        norm_im = simple_norm(self.dat*self.mask_bool,'asinh', min_percent=0.5, max_percent=99.9,
                              min_cut=v1, max_cut=v2)  #'beautify' the image
        
        #self.fig = figure.Figure(figsize=(5,5))
        self.ax = self.fig.add_subplot()
        self.im = self.ax.imshow(self.dat,origin='lower',norm=norm_im)
        self.ax.set_xlim(0,len(self.dat)-1)
        self.ax.set_ylim(0,len(self.dat)-1)
        
        #trying to extract a meaningful figure title from the path information
        filename=self.path_to_im.get().split('/')[-1]  #split str into list, let delimiter=/, isolate filename
        galaxy_name=filename.split('-')[0]  #galaxy name is first item in filename split list
        band=filename.split('-')[-1].split('.')[0]  #last item in filename list is band.fits; split into two components, isolate the first
        
        self.ax.set_title(f'{galaxy_name} ({band})',fontsize=15)

        self.im_length = np.shape(self.dat)[0]
        self.y_min = int(self.im_length/2-(0.20*self.im_length))
        self.y_max = int(self.im_length/2+(0.20*self.im_length))
        self.x=self.im_length/2
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_display)    
        
        #activate the draw square/rectangle/quadrilateral/four-sided polygon event
        self.connect_event=self.canvas.mpl_connect('button_press_event',self.drawSqRec)
        
        #add canvas 'frame'
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=3,rowspan=6)
        
        
    def change_canvas_event(self):
        
        if self.var==0:
            self.canvas.mpl_disconnect(self.connect_event)
            self.connect_event = self.canvas.mpl_connect('button_press_event',self.drawSqRec)
        if self.var==1:
            self.canvas.mpl_disconnect(self.connect_event)
            self.connect_event = self.canvas.mpl_connect('button_press_event',self.placeBar)
         
    #create command function to print info popup message
    def popup(self):
        messagebox.showinfo('Unconventional README.md',self.textbox)
    
    def placeBar(self, event):  
        self.x=int(event.xdata)
        #if user clicks outside the image bounds, then x is NoneType. y cannot be None, by design. only need to check x.
        if event.inaxes:
            #re-plot bar
            line_x = np.zeros(150)+self.x
            line_y = np.linspace(self.y_min,self.y_max,150)       
            self.current_bar.remove()
            self.current_bar = self.ax.scatter(line_x,line_y,s=3,color='red')
            
            #extract the mean pixel value from this bar
            value_list = np.zeros(100)
            for index in range(100):
                y_coord = line_y[index]
                px_value = self.dat[int(y_coord)][self.x]   #x will be the same...again, by design.
                value_list[index] = px_value
            mean_px = round(np.mean(value_list),3)
            
            self.val.config(text=f'Pixel Value: {mean_px}',font='Ariel 16')
            self.canvas.draw()
            
        else:
            print('Keep inside of the image!')
            self.val.config(text='Pixel Value: None', font='Ariel 16')
    
    
    ###FOR RECTANGLES --> CLICK TWICE, DICTATE INCLINATION###
    
    def func(self,x,m,b):
        return m*x+b
    
    #from https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
    def rotate(self, point_to_be_rotated, center_point = (0,0)):
        angle_rad = self.angle*np.pi/180
        xnew = np.cos(angle_rad)*(point_to_be_rotated[0] - center_point[0]) - np.sin(angle_rad)*(point_to_be_rotated[1] - center_point[1]) + center_point[0]
        ynew = np.sin(angle_rad)*(point_to_be_rotated[0] - center_point[0]) + np.cos(angle_rad)*(point_to_be_rotated[1] - center_point[1]) + center_point[1]

        return (round(xnew,2),round(ynew,2))
    
    #extract x and y vertex coordinates, and the slope of the lines connecting these points
    #this function "returns" lists of (x,y) vertices, and the slopes of the rectangle perimeter lines
    #NOTE: I choose np.max(x)-np.min(x) as the number of elements comprising each equation. seems fine.
    def get_xym(self):
        
        #self.event_bounds contains the list [self.x1,self.y1,self.x2,self.y2]
        self.p1 = [self.event_bounds[0],self.event_bounds[1]]   #coordinates of first click event
        self.p2 = [self.event_bounds[2],self.event_bounds[3]]   #coordinates of second click event
        
        if self.angle%90 != 0:      #if angle is not divisible by 90, can rotate using this algorithm. 
            
            n_spaces = int(np.abs(self.p1[0] - self.p2[0]))   #number of 'pixels' between x coordinates
            
            (xc,yc) = ((self.p1[0]+self.p2[0])/2, (self.p1[1]+self.p2[1])/2)
            one_rot = self.rotate(point_to_be_rotated = self.p1, center_point = (xc,yc))
            two_rot = self.rotate(point_to_be_rotated = self.p2, center_point = (xc,yc))
            three_rot = self.rotate(point_to_be_rotated = (self.p1[0],self.p2[1]), center_point = (xc,yc))
            four_rot = self.rotate(point_to_be_rotated = (self.p2[0],self.p1[1]), center_point = (xc,yc))

            x1 = np.linspace(one_rot[0],three_rot[0],n_spaces)
            m1 = (one_rot[1] - three_rot[1])/(one_rot[0] - three_rot[0])
            y1 = three_rot[1] + m1*(x1 - three_rot[0])

            x2 = np.linspace(one_rot[0],four_rot[0],n_spaces)
            m2 = (one_rot[1] - four_rot[1])/(one_rot[0] - four_rot[0])
            y2 = four_rot[1] + m2*(x2 - four_rot[0])

            x3 = np.linspace(two_rot[0],three_rot[0],n_spaces)
            m3 = (two_rot[1] - three_rot[1])/(two_rot[0] - three_rot[0])
            y3 = two_rot[1] + m3*(x3 - two_rot[0])

            x4 = np.linspace(two_rot[0],four_rot[0],n_spaces)
            m4 = (two_rot[1] - four_rot[1])/(two_rot[0] - four_rot[0])
            y4 = two_rot[1] + m4*(x4 - two_rot[0])

            self.x_rot = [x1,x2,x3,x4]
            self.y_rot = [y1,y2,y3,y4]
            self.m_rot = [m1,m2,m3,m4]
            self.n_spaces = n_spaces
            
            self.one_rot = one_rot
            self.two_rot = two_rot
            self.three_rot = three_rot
            self.four_rot = four_rot

        elif (self.angle/90)%2 == 0:  #if angle is divisible by 90 but is 0, 180, 360, ..., no change to rectangle
            
            n_spaces = int(np.abs(self.p1[0] - self.p2[0]))   #number of 'pixels' between x coordinates
            
            x1 = np.zeros(50)+self.p1[0]
            y1 = np.linspace(self.p2[1],self.p1[1],n_spaces)

            x2 = np.linspace(self.p1[0],self.p2[0],n_spaces)
            y2 = np.zeros(50)+self.p2[1]

            x3 = np.linspace(self.p2[0],self.p1[0],n_spaces)
            y3 = np.zeros(50)+self.p1[1]

            x4 = np.zeros(50)+self.p2[0]
            y4 = np.linspace(self.p1[1],self.p2[1],n_spaces)

            self.x_rot = [x1,x2,x3,x4]
            self.y_rot = [y1,y2,y3,y4]
            self.m_rot = [0,0,0,0]
            self.n_spaces = n_spaces
            
            self.one_rot = self.p1
            self.two_rot = self.p2
            self.three_rot = (self.p1[0],self.p2[1])
            self.four_rot = (self.p2[0],self.p1[1])
            

        else:                   #if angle is divisible by 90 but is 90, 270, ..., rectangle perpendicular
                                #to the original
            
            n_spaces = int(np.abs(self.p1[1] - self.p2[1]))   #rectangle 'length' now the y values
            
            (xc,yc) = ((self.p1[0]+self.p2[0])/2, (self.p1[1]+self.p2[1])/2)
            one_rot = self.rotate(point_to_be_rotated = self.p1, center_point = (xc,yc))
            two_rot = self.rotate(point_to_be_rotated = self.p2, center_point = (xc,yc))
            three_rot = self.rotate(point_to_be_rotated = (self.p1[0],self.p2[1]), center_point = (xc,yc))
            four_rot = self.rotate(point_to_be_rotated = (self.p2[0],self.p1[1]), center_point = (xc,yc))
            
            y1 = np.zeros(50)+self.p1[0]
            x1 = np.linspace(self.p2[1],self.p1[1],n_spaces)

            y2 = np.linspace(self.p1[0],self.p2[0],n_spaces)
            x2 = np.zeros(50)+self.p2[1]

            y3 = np.linspace(self.p2[0],self.p1[0],n_spaces)
            x3 = np.zeros(50)+self.p1[1]

            y4 = np.zeros(50)+self.p2[0]
            x4 = np.linspace(self.p1[1],self.p2[1],n_spaces)

            self.x_rot = [x1,x2,x3,x4]
            self.y_rot = [y1,y2,y3,y4]
            self.m_rot = [0,0,0,0]
            self.n_spaces = n_spaces
            
            self.one_rot = one_rot
            self.two_rot = two_rot
            self.three_rot = three_rot
            self.four_rot = four_rot
            
    def RecRot(self):
    
        self.get_xym()   #defines and initiates self.x_rot, self.y_rot, self.m_rot
                
        #create lists
        list_to_mean = []
        self.mean_list = []   #only need to initialize once
        
        #note --> self.all_bars contains all pixel values underneath the superimposed bars!
        #         that is...at each y-coordinate, what is the mean pixel value of the column?
        #         (or whatever the rotated variant of a column is.)
        
        for i in range(self.n_spaces):  #for the entire n_spaces extent: 
                                        #find x range of between same-index points on opposing sides of the 
                                        #rectangle, determine the equation variables to 
                                        #connect these elements within this desired x range, 
                                        #then find this line's mean pixel value. 
                                        #proceed to next set of elements, etc.

            #points from either x4,y4 (index=3) or x1,y1 (index=0)
            #any angle which is NOT 0,90,180,270,360,etc.
            if self.angle%90 != 0:
                self.all_bars = np.zeros(self.n_spaces**2).reshape(self.n_spaces,self.n_spaces)
                xpoints = np.linspace(self.x_rot[3][i],self.x_rot[0][-(i+1)],self.n_spaces)
                b = self.y_rot[0][-(i+1)] - (self.m_rot[2]*self.x_rot[0][-(i+1)])
                ypoints = self.func(xpoints,self.m_rot[2],b)
                #self.ax.scatter(xpoints,ypoints,s=1)

                for n in range(len(ypoints)):
                    #from the full data grid x, isolate all of values occupying the rows (xpoints) in 
                    #the column ypoints[n]
                    list_to_mean.append(self.dat[int(round(ypoints[n],3))][int(xpoints[n])])

                self.all_bars[i][0:self.n_spaces] = np.asarray(list_to_mean)
                self.mean_list.append(np.mean(list_to_mean))
                list_to_mean = []
            
            #0,180,360,etc.
            if (self.angle/90)%2 == 0:
                self.all_bars = np.zeros(self.n_spaces**2).reshape(self.n_spaces,self.n_spaces)
                xpoints = np.linspace(self.x_rot[3][i],self.x_rot[0][-(i+1)],self.n_spaces)
                b =self.y_rot[0][-(i+1)] - (self.m_rot[2]*self.x_rot[0][-(i+1)])
                ypoints = self.func(xpoints,self.m_rot[2],b)
                #self.ax.scatter(xpoints,ypoints,s=1)

                for n in range(len(ypoints)):
                    #from the full data grid x, isolate all of values occupying the rows (xpoints) in 
                    #the column ypoints[n]
                    list_to_mean.append(self.dat[int(round(ypoints[n],5))][int(xpoints[n])])

                self.all_bars[i][0:self.n_spaces] = np.asarray(list_to_mean)
                self.mean_list.append(np.mean(list_to_mean))
                list_to_mean = []

        #90,270,etc.
        #troubles abound here, though I am unsure why. must fix.
        if ((self.angle/90)%2 != 0) & (self.angle%90 == 0):
            #y_val start and end are the same at every index for this case
            ypoints = np.linspace(self.y_rot[3][0],self.y_rot[0][-1],self.n_spaces)    
            list_to_mean = []
            mean_list = []
            all_bars = np.zeros((np.abs(self.p1[1]-self.p2[1]),self.n_spaces))
            

            for i in range(np.abs(int(self.p1[1]-self.p2[1]))):
                xpoints = self.x_rot[1]+i        
                #self.ax.scatter(xpoints,ypoints,s=1)

                for n in range(len(ypoints)):
                    #from the full data grid x, isolate all of values occupying the rows (xpoints) in 
                    #the column ypoints[n]
                    list_to_mean.append(self.dat[int(round(ypoints[n],3))][int(xpoints[n])])

                self.all_bars[i][0:self.n_spaces] = np.asarray(list_to_mean)
                self.mean_list.append(np.mean(list_to_mean))
                list_to_mean = []

    def create_rectangle(self,x_one=None,x_two=None,y_one=None,y_two=None):
        
        try:
            self.angle = float(self.angle_box.get())

        except:
            self.angle = 0
            print('Angle defaulting to 0. Please enter integer angle into box, if desired.')
        
        try:
            for line in [self.line_eins,self.line_zwei,self.line_drei,self.line_vier]:
                line_to_remove = line.pop(0)
                line_to_remove.remove()
        except:
            pass
        
        if (self.angle==0)|(isinstance(self.angle,str)):
            if x_one is not None:    
                         
                self.line_one = self.ax.plot([x_one,x_one],[y_one,y_two],color='crimson')
                self.line_two = self.ax.plot([x_one,x_two],[y_one,y_one],color='crimson')
                self.line_three = self.ax.plot([x_two,x_two],[y_one,y_two],color='crimson')
                self.line_four = self.ax.plot([x_one,x_two],[y_two,y_two],color='crimson')
                
            else:
            
                self.get_xym()   #defines and initiates self.x_rot, self.y_rot, self.m_rot

                x1,x2,x3,x4=self.one_rot[0],self.two_rot[0],self.three_rot[0],self.four_rot[0]
                y1,y2,y3,y4=self.one_rot[1],self.two_rot[1],self.three_rot[1],self.four_rot[1]

                self.line_eins = self.ax.plot([x1,x3],[y1,y3],color='crimson')   #1--3
                self.line_zwei = self.ax.plot([x1,x4],[y1,y4],color='crimson')   #1--4
                self.line_drei = self.ax.plot([x2,x3],[y2,y3],color='crimson')   #2--3
                self.line_vier = self.ax.plot([x2,x4],[y2,y4],color='crimson')   #2--4

                self.canvas.draw()

        if self.angle!=0:
            
            #a nonzero angle means the user has already created the unaltered rectangle
            #that is, the coordinates already exist in self.event_bounds (x1,x2,y1,y2)
            #these are called in get_xym
            
            self.get_xym()   #defines and initiates self.x_rot, self.y_rot, self.m_rot

            x1,x2,x3,x4=self.one_rot[0],self.two_rot[0],self.three_rot[0],self.four_rot[0]
            y1,y2,y3,y4=self.one_rot[1],self.two_rot[1],self.three_rot[1],self.four_rot[1]
                        
            self.line_eins = self.ax.plot([x1,x3],[y1,y3],color='crimson')   #1--3
            self.line_zwei = self.ax.plot([x1,x4],[y1,y4],color='crimson')   #1--4
            self.line_drei = self.ax.plot([x2,x3],[y2,y3],color='crimson')   #2--3
            self.line_vier = self.ax.plot([x2,x4],[y2,y4],color='crimson')   #2--4

            self.canvas.draw()
            
    def drawSqRec(self, event):
        
        try:
            self.angle = float(self.angle_box.get())
        except:
            self.angle = 0
            print('Angle defaulting to 0. Please enter integer angle into box, if desired.')
        
        #collect the x and y coordinates of the click event
        #if first click event already done, then just define x2, y2. otherwise, define x1, y1.
        if (self.x1 is not None) & (self.y1 is not None):
            self.x2 = event.xdata
            self.y2 = event.ydata
        else:
            self.x1 = event.xdata
            self.y1 = event.ydata
            first_time=True
        
        #the user has clicked only the 'first' rectangle corner...
        if (self.x1 is not None) & (self.x2 is None):
            #if the corner is within the canvas, plot a dot to mark this 'first' corner
            if event.inaxes:
                self.bound_check=True
                dot = self.ax.scatter(self.x1,self.y1,color='crimson',s=10,marker='*')
                self.sq_mean_value = self.dat[int(self.x1),int(self.y1)]
                self.canvas.draw()
                #for whatever reason, placing dot.remove() here will delete the dot after the second click
                dot.remove()
        
        #if the 'first' corner is already set, then plot the rectangle and print the output mean pixel value
        #within this rectangle
        if (self.x2 is not None):
            
            #assign all event coordinates to an array
            self.event_bounds = [self.x1.copy(),self.y1.copy(),self.x2.copy(),self.y2.copy()]
            
            if event.inaxes:
                if (self.bound_check):
                    self.create_rectangle(x_one=self.x1,x_two=self.x2,y_one=self.y1,y_two=self.y2)
                    self.canvas.draw()
                    
            #reset parameters for next iteration
            self.bound_check = None
            self.x1=None
            self.x2=None
            self.y1=None
            self.y2=None
            
            #similar phenomenon as dot.remove() above.
            try:
                for line in [self.line_one,self.line_two,self.line_three,self.line_four]:
                    line_to_remove = line.pop(0)
                    line_to_remove.remove()
            except:
                pass
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # Function for opening the file explorer window
    def browseFiles(self):
        filename = filedialog.askopenfilename(initialdir = "/Users/k215c316/vf_html_mask/all_input_fits/", title = "Select a File", filetypes = ([("FITS Files", ".fits")]))
        self.path_to_im.delete(0,tk.END)
        self.path_to_im.insert(0,filename)        
    
##########
#the sonification-specific functions...
##########

    #typical sonification mapping function; maps value(s) from one range to another range; returns floats
    def map_value(self, value, min_value, max_value, min_result, max_result):
        result = min_result + (value - min_value)/(max_value - min_value)*(max_result - min_result)
        return result
    
    def midi_setup_bar(self):
        
        #define various quantities required for midi file generation
        self.y_scale = float(self.y_scale_entry.get())
        self.strips_per_beat = 15
        self.vel_min = int(self.vel_min_entry.get())
        self.vel_max = int(self.vel_max_entry.get())
        self.bpm = int(self.bpm_entry.get())
        self.program = int(self.program_entry.get())
        self.duration = float(self.duration_entry.get())
        try:
            self.angle = float(self.angle_box.get())
        except:
            self.angle = 0
            print('Angle defaulting to 0. Please enter integer angle into box, if desired.')
        
        self.note_names = 'D2-E2-F#2-G2-A2-B2-C#2-D3-E3-F#3-G3-A3-B3-C#3-D4-E4-F#4-G4-A4-B4-C#4-D5-E5-F#5-G5-A5-B5-C#5-D6'   #D-major
        self.note_names = self.note_names.split("-")   #converts self.note_names into a proper list of note strings
        self.soundfont = '/opt/anaconda3/share/soundfonts/SM64SF_V2.sf2'
        
        if self.angle == 0:
        
            #use user-drawn rectangle in order to define xmin, xmax; ymin, ymax. if no rectangle drawn, then default to image dimensions (for x parameters) and galaxy optical D25 (for y parameters)
            try:
                self.xmin = int(self.event_bounds[2]) if (self.event_bounds[0]>self.event_bounds[2]) else int(self.event_bounds[0])
                self.xmax = int(self.event_bounds[0]) if (self.event_bounds[0]>self.event_bounds[2]) else int(self.event_bounds[2])
            except:
                print('Defaulting to image parameters for xmin, xmax; ymin, ymax.')
                self.xmin=0
                self.xmax=self.im_length

            try:
                self.ymin = int(self.event_bounds[3]) if (self.event_bounds[1]>self.event_bounds[3]) else int(self.event_bounds[1])
                self.ymax = int(self.event_bounds[1]) if (self.event_bounds[1]>self.event_bounds[3]) else int(self.event_bounds[3])
            except:
                self.ymin = int(self.im_length/2-(0.20*self.im_length))
                self.ymax = int(self.im_length/2+(0.20*self.im_length))

            self.xminmax_entry.delete(0,tk.END)
            self.xminmax_entry.insert(0,f'{self.xmin}, {self.xmax}')
            self.yminmax_entry.delete(0,tk.END)
            self.yminmax_entry.insert(0,f'{self.ymin}, {self.ymax}')

            band = self.dat[:,self.y_min:self.y_max]   #isolates pixels within horizontal band across the image from y_min to y_max
            strips = []   #create empty array for 1px strips
            mean_strip_values = np.zeros(self.xmax-self.xmin)
            for i in range(self.xmin,self.xmax):
                strips.append(band[i,:])   #individual vertical strips
                mean_strip_values[i-self.xmin] = np.mean(strips[i-self.xmin])   #the 'ydata'; self.xmin-i for correct indices
    
        if self.angle != 0:
            self.RecRot()
            mean_strip_values = self.mean_list
    
        #rescale strip number to beats
        self.t_data = np.arange(0,len(mean_strip_values),1) / self.strips_per_beat   #convert to 'time' steps
        duration_beats=np.max(self.t_data)   #duration is end of the t_data list, or the max value in this list
        #print('Duration:',duration_beats, 'beats')
        #one beat = one quarter note
        
        y_data = self.map_value(mean_strip_values,min(mean_strip_values),max(mean_strip_values),0,1)   #normalizes values
        y_data_scaled = y_data**self.y_scale
        
        note_midis = [str2midi(n) for n in self.note_names]  #list of midi note numbers
        n_notes = len(note_midis)
        #print('Resolution:',n_notes,'notes')

        #MAPPING DATA TO MIDIS!
        self.midi_data = []
        #for every data point, map y_data_scaled values such that smallest/largest px is lowest/highest note
        for i in range(len(self.t_data)):   #assigns midi note number to whichever y_data_scaled[i] is nearest
            note_index = round(self.map_value(y_data_scaled[i],0,1,0,len(note_midis)-1))
            self.midi_data.append(note_midis[note_index])
    
        #map data to note velocities (equivalent to the sound volume)
        self.vel_data = []
        for i in range(len(y_data_scaled)):
            note_velocity = round(self.map_value(y_data_scaled[i],0,1,self.vel_min,self.vel_max)) #larger values, heavier sound
            self.vel_data.append(note_velocity)
        
        self.midi_allnotes() 
        
    def midi_allnotes(self):
        #create midi file object, add tempo
        self.memfile = BytesIO()   #create working memory file (allows me to play the note without saving the file...yay!)
        midi_file = MIDIFile(1) #one track
        midi_file.addTempo(track=0,time=0,tempo=self.bpm) #only one track, so track=0th track; begin at time=0, tempo is bpm
        midi_file.addProgramChange(tracknum=0, channel=0, time=0, program=self.program)
        #add midi notes to file
        for i in range(len(self.t_data)):
            midi_file.addNote(track=0, channel=0, pitch=self.midi_data[i], time=self.t_data[i], duration=self.duration, volume=self.vel_data[i])
        midi_file.writeFile(self.memfile)
        
        mixer.init()
        self.memfile.seek(0)
        mixer.music.load(self.memfile)
        mixer.music.play()
    
    def midi_square(self,event):

        sq_data = self.map_value(float(self.sq_mean_value),np.min(self.dat),np.max(self.dat),0,1)
        print(f'Note: max pixel value is {np.max(self.dat)}, located at {np.where(self.dat==np.max(self.dat))}')
        sq_data_scaled = sq_data**self.y_scale

        note_midis = [str2midi(n) for n in self.note_names]  #list of midi note numbers

        #MAP DATA TO MIDI NOTE
        #assigns midi note number to whichever sq_data_scaled is nearest
        if sq_data<0:
            note_index=0
        else:
            note_index = round(self.map_value(sq_data_scaled,0,1,0,len(note_midis)-1))
        self.midi_data = note_midis[note_index]

        self.memfile = BytesIO()

        midi_file = MIDIFile(1)
        midi_file.addTempo(track=0, time=0, tempo=self.bpm)
        midi_file.addProgramChange(tracknum=0, channel=0, time=0, program=self.program)


        midi_file.addNote(track=0, channel=0, pitch=int(note_midis[note_index]), time=0, duration=1, volume=90)
        midi_file.writeFile(self.memfile)
        #with open(homedir+'/Desktop/test.mid',"wb") as f:
        #    self.midi_file.writeFile(f)

        mixer.init()
        self.memfile.seek(0)   #for whatever reason, have to manually 'rewind' the track in order for mixer to play
        mixer.music.load(self.memfile)
        mixer.music.play()
        
    def midi_singlenote(self,event):
        #the setup for playing *just* one note...using the bar technique. :-)
        self.memfile = BytesIO()   #create working memory file (allows me to play the note without saving the file...yay!)
        
        midi_file = MIDIFile(1) #one track
        midi_file.addTrackName(0,0,'Note')
        midi_file.addTempo(track=0, time=0, tempo=self.bpm)
        midi_file.addProgramChange(tracknum=0, channel=0, time=0, program=self.program)
        
        #when "trimming" the midi file, the index of the notes does not necessarily correspond to the xclick event (e.g., initial note is 0 but the range is from xmin=30 to xmax=50, so if xclick=0 the note played will be for xmin=30). one solution is to "cushion" the midi notes between arrays of zeros to artificially raise the index numbers. If xmin=0 and xmax=np.max(image), then there will be no such cushioning. The floor will be solid af.
        cushion_left = np.zeros(self.xmin)
        cushion_right = np.zeros(self.xmax - (self.xmin+len(self.midi_data)))
        midi_edited = np.ndarray.tolist(np.concatenate([cushion_left,self.midi_data,cushion_right]))
        vel_edited = np.ndarray.tolist(np.concatenate([cushion_left,self.vel_data,cushion_right]))

        midi_file.addNote(track=0, channel=0, pitch=int(midi_edited[self.x]), time=self.t_data[1], duration=1, volume=int(vel_edited[self.x]))   #isolate the one note corresponding to the click event, add to midi file
        
        midi_file.writeFile(self.memfile)
        #with open(homedir+'/Desktop/test.mid',"wb") as f:
        #    self.midi_file.writeFile(f)
        
        mixer.init()
        self.memfile.seek(0)   #for whatever reason, have to manually 'rewind' the track in order for mixer to play
        mixer.music.load(self.memfile)
        mixer.music.play()       
        
        
if __name__ == "__main__":
    app = App()
    app.mainloop()
    app.destroy()    
    
    
    #create save button which saves most recent sonification file as well as a companion text file listing the galaxy VFID and parameter values.
    #change midi note scales (D major, etc.)
    #I should also update the "Click for Info" instructions to reflect the square funtionalities
    #I should ALSO record a video tutorial on how to operate this doohickey.
    #also also also...animations. maybe.