import tkinter as tk

def create_gui():
    window = tk.Tk()
    window.title("MapGen")

    # Labels
    label_title = tk.Label(window, text="MapGen")
    label_disclaimer = tk.Label(window, text="This program is strictly for use with Missouri Climate Center products and research.")
    label_product = tk.Label(window, text="Select a product:")
    label_timescale = tk.Label(window, text="Select a timescale:")
    label_axis_title_font = tk.Label(window, text="Axis Title Font Size:")
    label_title_font = tk.Label(window, text="Title Font Size:")
    label_axis_tick_font = tk.Label(window, text="Axis Tick Font Size:")

    # Comboboxes
    product_options = ["Graduated SPI", "Categorical SPI", 
                        "Onset Seasonality", "Relief Seasonality", "Average Duration", 
                        "Cumulative Duration", "Longest Duration", "Shortest Duration"]
    product_var = tk.StringVar(window)
    product_var.set(product_options[0])
    product_dropdown = tk.OptionMenu(window, product_var, *product_options)

    timescale_options = ["01M", "03M", "06M", "12M"]
    timescale_var = tk.StringVar(window)
    timescale_var.set(timescale_options[0])
    timescale_dropdown = tk.OptionMenu(window, timescale_var, *timescale_options)

    # Entry fields
    entry_axis_title_font = tk.Entry(window)
    entry_axis_title_font.insert(0, "12")
    entry_title_font = tk.Entry(window)
    entry_title_font.insert(0, "16")
    entry_axis_tick_font = tk.Entry(window)
    entry_axis_tick_font.insert(0, "10")

    # Checkbox and custom title elements
    custom_title_var = tk.BooleanVar()
    checkbox_custom_title = tk.Checkbutton(window, text="Custom Title", variable=custom_title_var)
    label_custom_title_text = tk.Label(window, text="Custom Title:", state=tk.DISABLED)
    entry_custom_title = tk.Entry(window, state=tk.DISABLED)

    # Button
    button_ok = tk.Button(window, text="Ok", command=lambda: print(f"Selected product: {product_var.get()}, Timescale: {timescale_var.get()}, Axis Title Font: {entry_axis_title_font.get()}, Title Font: {entry_title_font.get()}, Axis Tick Font: {entry_axis_tick_font.get()}, Custom Title: {entry_custom_title.get() if custom_title_var.get() else None}, Show Plot: {show_plot_var.get()}"))    
    button_cancel = tk.Button(window, text="Cancel", command=window.quit)

    # Checkbox for showing or saving plot
    show_plot_var = tk.BooleanVar()
    show_plot_checkbox = tk.Checkbutton(window, text="Show Plot", variable=show_plot_var)
    label_show_plot_text = tk.Label(window, text="SPI Key:", state=tk.DISABLED)
    entry_spi_key = tk.Entry(window, state=tk.DISABLED)

    # Grid layout
    label_title.grid(row=0, columnspan=2)
    label_disclaimer.grid(row=1, columnspan=2)
    label_product.grid(row=2, column=0)
    product_dropdown.grid(row=2, column=1)
    label_timescale.grid(row=3, column=0)
    timescale_dropdown.grid(row=3, column=1)
    label_axis_title_font.grid(row=4, column=0)
    entry_axis_title_font.grid(row=4, column=1)
    label_title_font.grid(row=5, column=0)
    entry_title_font.grid(row=5, column=1)
    label_axis_tick_font.grid(row=6, column=0)
    entry_axis_tick_font.grid(row=6, column=1)
    checkbox_custom_title.grid(row=7, columnspan=2)
    label_custom_title_text.grid(row=8, column=0)
    entry_custom_title.grid(row=8, column=1)
    checkbox_custom_title.grid(row=7, columnspan=2)
    show_plot_checkbox.grid(row=9, columnspan=2)
    label_show_plot_text.grid(row=10, column=0)
    entry_spi_key.grid(row=10, column=1)
    button_ok.grid(row=11, column=0)
    button_cancel.grid(row=11, column=1)

    def toggle_custom_title():
        label_custom_title_text.config(state=tk.NORMAL if custom_title_var.get() else tk.DISABLED)
        entry_custom_title.config(state=tk.NORMAL if custom_title_var.get() else tk.DISABLED)

    checkbox_custom_title.config(command=toggle_custom_title)


    def toggle_show_plot():
        label_show_plot_text.config(state=tk.NORMAL if show_plot_var.get() else tk.DISABLED)
        entry_spi_key.config(state=tk.NORMAL if show_plot_var.get() else tk.DISABLED)

    show_plot_checkbox.config(command=toggle_show_plot)


    window.mainloop()

create_gui()


