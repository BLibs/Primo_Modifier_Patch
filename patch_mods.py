import requests
from config import API
from get_data import get_product_id, get_mod_groups, get_mods_from_group


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
