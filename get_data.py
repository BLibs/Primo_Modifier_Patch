import requests
from config import API


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
