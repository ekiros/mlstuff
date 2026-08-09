import tkinter as tk

class FlyoverMenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flyover Menu Demo")
        
        # Create a button to hover over
        self.my_button = tk.Button(root, text="Hover for Menu", padx=20, pady=10)
        self.my_button.pack(pady=50)

        # Create the menu, but don't display it yet
        self.flyover_menu = tk.Menu(root, tearoff=False)
        self.flyover_menu.add_command(label="Option 1", command=lambda: self.on_select("Option 1"))
        self.flyover_menu.add_command(label="Option 2", command=lambda: self.on_select("Option 2"))
        self.flyover_menu.add_command(label="Exit", command=root.quit)

        # Bind the mouse-enter event to show the menu
        self.my_button.bind("<Enter>", self.show_menu)
        # Bind the mouse-leave event to hide the menu
        self.my_button.bind("<Leave>", self.hide_menu)

        # To prevent the menu from disappearing when the cursor moves from the button to the menu,
        # we also bind the <Leave> event on the menu itself.
        self.flyover_menu.bind("<Leave>", self.hide_menu)
    
    def show_menu(self, event):
        """Displays the menu at the cursor's position."""
        x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
        self.flyover_menu.post(x, y)

    def hide_menu(self, event):
        """Hides the menu."""
        # Unpost the menu if the mouse leaves the button and the menu
        if not (self.my_button.winfo_containing(event.x_root, event.y_root) == self.flyover_menu):
            self.flyover_menu.unpost()

    def on_select(self, option):
        """A sample command for a menu item."""
        print(f"Selected: {option}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FlyoverMenuApp(root)
    root.mainloop()
