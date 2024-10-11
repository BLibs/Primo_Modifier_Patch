import math
import threading
import time
from cli import *
from config import *
from get_data import get_est_data
from patch_mods import patch_main


''' This project is designed to automatically update modifier groups at scale for Primo. If the price of a modifier 
    changes, this has a ripple effect on the free variable that would be attached to the mod group. This group says 
    that the mods have certain values, and the sum of those values is 'free' on the item, which would allow customers 
    to sub default mods for others while maintaining the cost value of the mods that come on the hoagie. 

    This field is not dynamic however, requiring that each mod group that uses one of the mods be patched after an 
    update. 

    The first part of this project is a database file in the form of an .xlsx file linking the relationship between all 
    items and the mods that they come with by default. The only constant between the items on the JSON level is the SKU
    that they are using across all establishments. 

    Once the user selects the mod that they updated (tagged with an integer value in ModMap.xlsx), we find all items
    in PrimoDB.xlsx that would be impacted. These items have their SKUs kept in a list, which will then be run 
    through the various functions that make up this process. 

    Groups will have the default modifiers evaluated and summed, checking for discrepancies between the value of the
    mods and the free variable value on the modifier group level. If they are not the same value, we overwrite the value
    of the free variable and PATCH the modifier group through the API.

    Process is currently conducted by selecting a single establishment and a single mod that would have been updated.
    '''


# Takes the number from the mod in find_mod_number and locates all items tagged to mod in PrimoDB. Returns SKU list
def get_sku_from_mod_id(name):
    item_list = []

    for i in range(1, 6):
        items = df.loc[df[f'Mod{i}'].eq(name)]['SKU'].to_list()
        item_list = item_list + items

    return item_list


# Split the list of returned SKUs to be patched into smaller lists for concurrent processing
def split_list(item_data):
    length = len(item_data)
    length = length / NUM_LISTS
    length = math.ceil(length)
    chunks = [item_data[x:x + length] for x in range(0, len(item_data), length)]

    return chunks


# Function that the threads are pointing back to. Used for taking the SKU of each item and passing to patch_main
def thread_function(thread_est, thread_item_list):
    for sku in thread_item_list:
        patch_main(thread_est, sku)


# Main function. Sets DBs, creates threads, and passes items through to the main patch function
def main():
    print("Getting establishment data....\n")

    # Get establishment data from the API
    data = get_est_data()
    # Get the establishment number
    est = get_est(data)
    # Display a choice list to get the mod group
    mod_group = get_mod_group()
    # Declaring the dataframe objects as global, so they can be accessed from other functions
    global df
    global mdf
    # Set the dataframes based on the mod group that was selected
    df = pd.read_excel("data_files/PrimoDB.xlsx", sheet_name=mod_group)
    mdf = pd.read_excel("data_files/ModMap.xlsx", sheet_name=mod_group)

    # Get the choice of a mod within the selected group, returned as an int
    mod_list_choice = get_mod(mod_group)
    # Pass that int through to the item list to see which items use this default mod. Returns a list
    item_list = get_sku_from_mod_id(int(mod_list_choice))

    # See how many items are going to be run
    print(len(item_list), "items found")

    # Split the list if the number of items is greater than the number of threads that would be used
    # Should always be true, unless the list has 0 elements. 52 should be the minimum that is greater than 0
    if len(item_list) >= NUM_LISTS:
        item_list = split_list(item_list)

    # Print how many lists the items were broken down into, which will also be the number of threads running
    print(len(item_list), "threads created for concurrent processing\n")

    # Get user input to continue with patching the items
    input("Press Enter to Continue: ")
    print("\nProcessing data...")

    # Using a for loop to create threads based on the number of lists that we are using
    # For as many threads as we are going to be using...
    for i in range(NUM_LISTS):
        # If 'i' is greater than or equal to zero and less than the length of item_list(number of lists)...
        if 0 <= i < len(item_list):
            # We are going to create a new thread and start it
            thread = threading.Thread(target=thread_function, args=(est, item_list[i],))
            thread.start()
            # Sleep for 1 second so not all threads start at once
            time.sleep(1)


# Call the execution of the main function
if __name__ == "__main__":
    main()
