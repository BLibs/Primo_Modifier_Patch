from cli import *
from config import *
import math
import threading
import time
import requests

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


# Getting the ID of the product; needed for locating the mod groups that are attached to the item
def get_product_id(est_choice, sku):
    url = "https://primohoagies.revelup.com/resources/Product/"

    querystring = {"establishment": est_choice, "sku": sku}

    payload = ""
    headers = {
        "User-Agent": "insomnia/2023.5.8",
        "API-AUTHENTICATION": API
    }

    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    response = response.json()
    response = response.get("objects")
    response = response[0]
    response = response.get("id")

    print("*****", response, "*****")
    return response


# Function calls the API endpoint for est data; returns a list of valid choices and prints the menu in the CLI
def get_est_data():
    url = "https://primohoagies.revelup.com/enterprise/Establishment/"

    payload = ""
    headers = {
        "User-Agent": "insomnia/2023.5.8",
        "API-AUTHENTICATION": API
    }

    response = requests.request("GET", url, data=payload, headers=headers)
    response = response.json()

    # Creating a list that can be returned when this function is called
    valid_est_nums = []

    est_data = response.get("objects")
    # For each site in the data...
    for site in est_data:
        # Get and print the name and the id of the establishment
        name = site.get("name")
        site_id = site.get("id")
        print(f"{name} - {site_id}")
        # Append the site_id to the list
        valid_est_nums.append(site_id)

    print("")

    # Return the list; used to make sure that user selection is a valid establishment
    return valid_est_nums


# Get associated mod groups from item
def get_mod_groups(est_choice, product_id):
    url = "https://primohoagies.revelup.com/resources/ProductModifierClass/"

    querystring = {"establishment": est_choice, "limit": "560", "product": product_id}

    payload = ""
    headers = {
        "User-Agent": "insomnia/2023.5.8",
        "API-AUTHENTICATION": API
    }

    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    response = response.json()
    response = response.get("objects")

    return response


# Get the mods that are in the mod group
def get_mods_from_group(uid):
    # Setting a starting value for the total sum of the mods
    sum_total = 0
    # Endpoint that we get the mods from
    url = "https://primohoagies.revelup.com/resources/ProductModifier/"

    querystring = {"limit": "560", "product_modifier_class": uid}

    payload = ""
    headers = {
        "User-Agent": "insomnia/2023.5.8",
        "API-AUTHENTICATION": API
    }

    # Get the response from endpoint, convert to JSON, and get the Objects (mods in the group)
    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    response = response.json()
    mods = response.get("objects")

    # For each item that is attached to the mod group...
    for items in mods:
        # Checking to see if the mod is default in the mod group (does not apply if not default)
        default = items.get("default_modifier")
        # Getting the mod id to display in output with the parent mod uri when patching
        mod_id = items.get('id')
        # URI is linked back to the parent mod that holds the price of the item.
        uri = items.get('modifier')
        # Only if the item is default...
        if default:
            # Print the id of the mod and the URI attached to the parent mod
            print(f"Default mod: {mod_id} {uri}")
            # Get the mods price from the URI
            price = get_mod_price(uri)
            # If there is a price on the mod...
            if price:
                # Sum to total
                sum_total += price
    print(f"total: {sum_total}")

    ''' Once all items are assessed, we can return the sum to the main_patch function for analysis.
        If the sum total is not equal to the free field, it will overwrite the free field variable
        and initiate a patch on the mod group.'''
    return sum_total


# Get Mod Price
def get_mod_price(mod_id):
    url = f"https://primohoagies.revelup.com{mod_id}"

    payload = ""
    headers = {
        "User-Agent": "insomnia/2023.5.8",
        "API-AUTHENTICATION": API
    }

    response = requests.request("GET", url, data=payload, headers=headers)
    response = response.json()
    price = response.get('price')

    # Converting the price of the mod to a float for comparison in main patch function
    print(float(price))
    return price


# Patch a mod class with the new free value
def patch_mods(mod_class, created_by, product, updated_by, item_id, amount_free):
    url = f"https://primohoagies.revelup.com/resources/ProductModifierClass/{item_id}/"

    payload = {
        "modifier_class": mod_class,
        "created_by": created_by,
        "product": product,
        "updated_by": updated_by,
        "amount_free": amount_free
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "insomnia/2023.5.8",
        "API-AUTHENTICATION": API,
        "accept": "application/json"
    }

    response = requests.request("PATCH", url, json=payload, headers=headers)

    print(response)  # 202 would mean the PATCH went through on the group without issue


# Takes the number from the mod in find_mod_number and locates all items tagged to mod in PrimoDB. Returns SKU list
def get_sku_from_mod_id(name):
    items_list = df.loc[df['Mod'].eq(name)]['SKU'].to_list()

    return items_list


# Split the list of returned SKUs to be patched into smaller lists for concurrent processing
def split_list(item_data):
    length = len(item_data)
    length = length / NUM_LISTS
    length = math.ceil(length)
    chunks = [item_data[x:x + length] for x in range(0, len(item_data), length)]

    return chunks


# Main patch function that the items will be run through
def patch_main(est_choice, sku):
    # Getting the product ID (required to pull the mod groups for analysis).
    product_id = get_product_id(est_choice, sku)
    # Get the mod groups that are linked to that product ID on the Management Console
    mod_groups = get_mod_groups(est_choice, product_id)

    # For each mod group attached to the item...
    for group in mod_groups:
        # Checking to see what the free variable is set to (we don't care about ones that don't use this field)
        free = group.get("amount_free")
        # Checking to make sure the group is even active
        active = group.get("active")
        # Running a check to see if the item is active and the free field is active and more than $0.00
        if active and free and free > 0:
            print("___________")
            print(f"Free amount: {free}")
            # All required variables for patching a mod group through API
            product_id = group.get('id')
            mod_class = group.get('modifier_class')
            created = group.get('created_by')
            product = group.get('product')
            updated = group.get('updated_by')
            # Getting the sum of all default mods in the group
            mod_total = get_mods_from_group(product_id)
            # If the mod total is different from free, we are going to patch the mod group
            if mod_total != free:
                print("PATCHING!")
                patch_mods(mod_class, created, product, updated, product_id, mod_total)


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
