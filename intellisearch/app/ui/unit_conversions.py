import os, sys
from datetime import datetime
from tkinter import ttk
from tkinter import font

# To override the basic Tk widgets, the import should follow the Tk import
from tkinter import *
from tkinter.ttk import *

sys.path.insert(0, os.path.abspath(".."))


class MetricToBritish:

    def __init__(self,root):
        root.title("Unit Conversion Fun")

        mainframe = ttk.Frame(root, padding=(3,3,12,12)) #left, top, right, bottom
        #mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        mainframe.grid(column=0, row=0)
        mainframe['borderwidth'] = 5
        mainframe['relief'] = 'ridge'
        

        self.from_value = DoubleVar()
        from_value_entry = ttk.Entry(mainframe, width=6, textvariable=self.from_value)
        from_value_entry.grid(column=2, row=1, sticky=(W,E))

        combo_vals = ['feet', 'meter(s)','yard(s)','mile(s)']
        self.combo_from_val = StringVar()
        self.combo_to_val = StringVar()

       
        from_unit_combo = ttk.Combobox(mainframe, width=10, values=combo_vals, textvariable=self.combo_from_val, state='readonly',)
        to_unit_combo = ttk.Combobox(mainframe, width=10, values=combo_vals, textvariable=self.combo_to_val,state='readonly', )
        
        from_unit_combo.current(0)
        to_unit_combo.current(1)

        self.to_value = StringVar()
        ttk.Label(mainframe, textvariable=self.to_value).grid(column=2, row=2, sticky=(W,E))

        ttk.Button(mainframe, text='Calculate', command=self.calculate).grid(column=3, row=3, sticky=W)

        self.to_unit_labl_var = StringVar()
        self.from_unit_labl_var = StringVar()

        self.to_unit_labl_var.set(self.combo_to_val.get())
        self.from_unit_labl_var.set(self.combo_from_val.get())


        ttk.Label(mainframe, textvariable=self.from_unit_labl_var).grid(column=3, row=1, sticky=W)
        ttk.Label(mainframe, textvariable=self.to_unit_labl_var).grid(column=3, row=2, sticky=W)
        ttk.Label(mainframe, text='is equivalent to').grid(column=1, row=2, sticky=E)

        ttk.Label(mainframe, text="FROM").grid(column=4, row=3, sticky=N)
        ttk.Label(mainframe, text="TO").grid(column=5, row=3, sticky=N)
        from_unit_combo.grid(column=4, row=4, sticky=(N))
        to_unit_combo.grid(column=5, row=4, sticky=(N))

        mainframe.columnconfigure(1, weight=2)
        mainframe.columnconfigure(2, weight=1)
        mainframe.columnconfigure(3, weight=1)
        mainframe.columnconfigure(4, weight=1)
        mainframe.rowconfigure(1, weight=2)
        mainframe.rowconfigure(2, weight=1)
        mainframe.rowconfigure(3, weight=1)
        mainframe.rowconfigure(4, weight=1)

        root.columnconfigure(0, weight=1)   
        root.rowconfigure(0, weight=1)

        for child in mainframe.winfo_children():
            child.grid_configure(padx=3, pady=3)

        from_value_entry.focus()

        #from_unit_combo.bind('<<ComboBoxSelected>>', self.calculate)
        #to_unit_combo.bind('<<ComboBoxSelected>>', self.calculate)

        root.bind("<Return>", self.calculate)

    

    def calculate(self, *args):
        try:
            foot_to_meter = 0.3048
            foot_to_yard = 3 # 3 feet/yard
            foot_to_mile = 5280 # 5280 ft /mile

            meter_to_yard = 1.094 # m x 1.094 = yrds
            meter_to_mile = 0.000621 # 1609 meters/mile

            yard_to_mile = 0.0005682 # y x 0.00056 = miles (1760 yards/mile)

            if self.from_value.get() == '':
                return
            
            from_unit_ = self.combo_from_val.get()
            to_unit_ = self.combo_to_val.get()

            val = float(self.from_value.get())

            self.to_unit_labl_var.set(to_unit_)
            self.from_unit_labl_var.set(from_unit_)
            
            #print(f"The FROM = [{from_val_}] and the to is = [{to_val_}]")
         
            if  from_unit_ == to_unit_:
                self.to_value.set(val)
            elif from_unit_ == 'feet' and to_unit_ == 'meter(s)':
                self.to_value.set(round(foot_to_meter*val, 4))
            elif from_unit_ == 'meter(s)' and to_unit_ == 'feet':
                self.to_value.set(round((1/foot_to_meter)*val, 4))
            elif from_unit_ == 'meter(s)' and to_unit_ == 'yard(s)':
                self.to_value.set(round(meter_to_yard*val, 4))
            elif from_unit_ == 'yard(s)' and to_unit_ == 'meter(s)':
                self.to_value.set(round((1/meter_to_yard)*val, 4))
            elif from_unit_ == 'feet' and to_unit_ == 'yard(s)':
                self.to_value.set(round((foot_to_yard)*val, 4))
            elif from_unit_ == 'yard(s)' and to_unit_ == 'feet':
                self.to_value.set(round(((1/foot_to_yard))*val, 4))
            elif from_unit_ == 'feet' and to_unit_ == 'mile(s)':
                self.to_value.set(round(((1/foot_to_mile))*val, 4))
            elif from_unit_ == 'mile(s)' and to_unit_ == 'feet':
                self.to_value.set(round((foot_to_mile)*val, 4))
            elif from_unit_ == 'meter(s)' and to_unit_ == 'mile(s)':
                self.to_value.set(round((meter_to_mile)*val, 4))
            elif from_unit_ == 'mile(s)' and to_unit_ == 'meter(s)':
                self.to_value.set(round(((1/meter_to_mile))*val, 4))
            elif from_unit_ == 'yard(s)' and to_unit_ == 'mile(s)':
                self.to_value.set(round((yard_to_mile)*val, 4))
            elif from_unit_ == 'mile(s)' and to_unit_ == 'yard(s)':
                self.to_value.set(round(((1/yard_to_mile))*val, 4))
                                  
            else:
                #print(f"The FROM = [{from_unit_}] and the to is = [{to_unit_}]")
                print("Laterz...")
            
        except ValueError as e:
            print(f'Really bad shit happened {e}')
            pass

def main():
    root = Tk()
    MetricToBritish(root)
    root.minsize(900, 500)
    root.mainloop()

## RUN ##
if __name__ == '__main__':
    main()
