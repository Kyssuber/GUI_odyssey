from tkinter import *

root = Tk()

#change title of GUI
root.title('Simple Calculator')

#entry widget...to enter data.
e = Entry(root, width=20, borderwidth=5, bg='black',fg='lime green', font=('Arial 24'))
#columnspan dictates the...column span of the text box.
e.grid(row=0,column=0, columnspan=3, padx=10, pady=10)

def button_click(number):
    current = e.get()
    e.delete(0,END)
    e.insert(0,str(current)+str(number))
    return

def button_clear():
    e.delete(0,END)
    
def button_add():
    current_number = e.get()
    
    #can now call f_num outside of the function
    global f_num
    global math
    math="addition"
    f_num = int(current_number)
    e.delete(0,END)
    
def button_subtract():
    current_number = e.get()
    global f_num
    global math
    math="subtraction"
    f_num = int(current_number)
    e.delete(0,END)
    
def button_multiply():
    current_number = e.get()
    global f_num
    global math
    math="multiplication"
    f_num = int(current_number)
    e.delete(0,END)
    
def button_divide():
    current_number = e.get()
    
    #can now call f_num outside of the function
    global f_num
    global math
    math="division"
    f_num = int(current_number)
    e.delete(0,END)
    
def button_equal():
    
    dictionary={"addition":"+", "subtraction":"-", "multiplication":"*", "division":"/"}
    
    current_number=e.get()
    result = eval(str(f_num)+dictionary[math]+current_number)
    
    e.delete(0,END)
    e.insert(0,str(result))
        
#define buttons
button_1 = Button(root, text='1', font=('Arial 24'), padx=30, pady=15, command=lambda: button_click(1))
button_2 = Button(root, text='2', font=('Arial 24'), padx=30, pady=15, command=lambda: button_click(2))
button_3 = Button(root, text='3', font=('Arial 24'), padx=30, pady=18, command=lambda: button_click(3))
button_4 = Button(root, text='4', font=('Arial 24'), padx=30, pady=15, command=lambda: button_click(4))
button_5 = Button(root, text='5', font=('Arial 24'), padx=30, pady=15, command=lambda: button_click(5))
button_6 = Button(root, text='6', font=('Arial 24'), padx=30, pady=15, command=lambda: button_click(6))
button_7 = Button(root, text='7', font=('Arial 24'), padx=30, pady=15, command=lambda: button_click(7))
button_8 = Button(root, text='8', font=('Arial 24'), padx=30, pady=15, command=lambda: button_click(8))
button_9 = Button(root, text='9', font=('Arial 24'), padx=30, pady=15, command=lambda: button_click(9))
button_0 = Button(root, text='0', font=('Arial 24'), padx=30, pady=15, command=lambda: button_click(0))
button_add = Button(root, text='+', font=('Arial 24'), padx=30, pady=15, command=button_add)
button_eq = Button(root, text='=', font=('Arial 24'), padx=86, pady=15, command=button_equal)
button_c = Button(root, text='Clear', font=('Arial 24'), padx=65, pady=15, command=button_clear)

button_sub = Button(root, text='-', font=('Arial 24'), padx=30, pady=15, command=button_subtract)
button_mult = Button(root, text='*', font=('Arial 24'), padx=30, pady=15, command=button_multiply)
button_div = Button(root, text='/', font=('Arial 24'), padx=30, pady=15, command=button_divide)

#place buttons on the window
button_1.grid(row=3, column=0)
button_2.grid(row=3, column=1)
button_3.grid(row=3, column=2)

button_4.grid(row=2, column=0)
button_5.grid(row=2, column=1)
button_6.grid(row=2, column=2)

button_7.grid(row=1, column=0)
button_8.grid(row=1, column=1)
button_9.grid(row=1, column=2)

button_0.grid(row=4, column=0)

button_add.grid(row=4,column=1)
button_sub.grid(row=4,column=2)

button_mult.grid(row=5,column=0)
button_div.grid(row=6,column=0)

button_eq.grid(row=6,column=1, columnspan=2)

button_c.grid(row=5,column=1, columnspan=2)

root.mainloop()