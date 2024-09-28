import pandas as pd


''' This file is used to create the CLI that we are using to get user input and display the progress of the script
    while it is running. This could eventually be replaced with a GUI to make things a little bit cleaner. '''


# Gets the target establishment as an input
def get_est(est_data):
    choice = input("Enter Establishment Number: ")
    if int(choice) in est_data:
        print("")
        return choice
    else:
        print("Invalid EST")
        get_est(est_data)


# Narrows down the mod group to only display some of the mods. Also used to set the item list in the db
def get_mod_group():
    while True:
        print("1: Cheeses")
        print("2: Dressings")
        print("3: Meats")
        print("4: Toppings")
        group_choice = input("Select a mod group: ")
        if group_choice == "1":
            print("Cheeses")
            return "Cheeses"
        elif group_choice == "2":
            print("Dressings")
            return "Dressings"
        elif group_choice == "3":
            print("Meats")
            return "Meats"
        elif group_choice == "4":
            print("Toppings")
            return "Toppings"
        else:
            print("\nInvalid Selection\n")


# Gets the mod selection from the user to see which items are going to need to be patched
def get_mod(mod_group):
    # Setting the modifier dataframe to the mod map file
    mdf = pd.read_excel("ModMap.xlsx", sheet_name=mod_group)
    # While true (or essentially until the function returns a valid selection)...
    while True:
        print("\nSelect a Mod: ")
        # Printing the modifier dataframe as a string without indexing for readability
        print(mdf.to_string(index=False))
        # Get user input and store in the selection variable
        selection = input("Selection: ")
        # Convert the selection from a string to an int and check if it exists in dataframe values
        if int(selection) in mdf.values:
            # If true, locate in the dataframe where the number matches the selection, and get the name of the mod.
            mod_choice = mdf.loc[mdf['Number'].eq(int(selection))]['Name'].to_list()
            # Print the selected modifier
            print(mod_choice)
            return selection
        else:
            print("\nInvalid Selection")
