from tkinter import *
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt
import sys
import time

#adapted from 
#https://stackoverflow.com/questions/65008468/how-to-draw-a-square-on-canvas-when-he-user-clicks-2-locations-with-tkinter
#if the user has not previously clicked a spot on the canvas, then assign x1,y1 to w.coords. if w.coords is already populated, then those coordinates are the 'first' coords and the second set of x1, y1 will pair with this first pair in order to form the rectangle. then, clear coords so that the next click will set up the first point of the rectangle.

def create_rectangle(x_one,x_two,y_one,y_two):
    
    global data
    
    line_one = plt.plot([x_one,x_one],[y_one,y_two],color='crimson')
    line_two = plt.plot([x_one,x_two],[y_one,y_one],color='crimson')
    line_three = plt.plot([x_two,x_two],[y_one,y_two],color='crimson')
    line_four = plt.plot([x_one,x_two],[y_two,y_two],color='crimson')
    
    try:
        x_values=np.sort(np.array([x_one,x_two]))
        y_values=np.sort(np.array([y_one,y_two]))
        
        px_in_sq = data[int(x_values[0]):int(x_values[1]), int(y_values[0]):int(y_values[1])]
        print(f'Mean pixel value within rectangle: {np.round(np.mean(px_in_sq),3)}')
    except TypeError:
        pass
    
    return line_one,line_two,line_three,line_four
    
coords=None
bound_check=None

def pointOne(event, canvas, data):
    
    global coords
    global bound_check
    
    x1 = event.xdata
    y1 = event.ydata
    
    if coords == None:
        coords = [x1,y1]
        if event.inaxes:
            bound_check=True
            dot = plt.scatter(x1,y1,color='crimson',s=10)
            canvas.draw()
            dot.remove()
            
    else:
        line_one,line_two,line_three,line_four=create_rectangle(coords[0],x1,coords[1],y1)
        canvas.draw()
        
        #reset parameters
        coords = None  
        bound_check = None
        
        #canvas.get_tk_widget().pack_forget()
        #canvas._tkcanvas.destroy()
        #print(canvas.get_tk_widget().find_all())
        for line in [line_one,line_two,line_three,line_four]:
            line_to_remove = line.pop(0)
            line_to_remove.remove()
        
        
#set up main GUI window
root = Tk()
root.title('Art Canvas')
root.geometry("700x700")

frame_display = LabelFrame(root,text='Display',padx=2,pady=2)
frame_display.pack()

plt.figure(figsize=(3,3))
plt.axis('off')
plt.title('Click me (twice, in two different locations)!',fontsize=8)

data = np.random.rand(200,200)
im = plt.imshow(data,origin='lower')

#set up canvas
canvas = FigureCanvasTkAgg(plt.gcf(), master=frame_display) 
#binds left-click
canvas.mpl_connect('button_press_event', lambda event: pointOne(event, canvas, data))

#create a label instance for the canvas window
display = canvas.get_tk_widget()
display.pack()

for i in range(5):
    frame_display.grid_columnconfigure(i,weight=1)
    frame_display.grid_rowconfigure(i,weight=1)

    root.grid_columnconfigure(i,weight=1)
    root.grid_rowconfigure(i,weight=1)


if __name__ == '__main__':
    root.mainloop()
    root.destroy()