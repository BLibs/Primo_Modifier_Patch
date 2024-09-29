# Primo Product Modifier Group Patch

This script gets a user input for which mod they recently updated the price of, uses the attached XLSX files to locate all items that default to this modifier, run those items through a function to get all data for the associated mods, sums the price of the default mods, and patches the associated product modifier group with the updated "free" price.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)

## Introduction

Each item has a unique modifier group attached to it for holding the available modifiers, their price, and which ones are default on the item. The modifier groups leverage a "free" variable, which states that if Example comes with American Cheese ($3.00) and Provolone Cheese ($4.00) by default, there is an applied free modifier value of $7.00 on Example. If the customer chooses to replace American Cheese with Swiss ($5.00), then the difference of $2 should be applied to the price of the item at checkout. The issue here is that the free field is hardcoded, and as the price of modifiers change, the value that is free will no longer line up with the cost of the mods. This required manual patching of each free variable in each modifier group, with an average of 4 modifier groups per item, across 3,854 current items, and a quickly growing number of ~120 establishments. That came out to roughly 1.8 million variables that would need to be patched if the price of all mods changed! 

To combat this problem, the script links the items to their modifiers using the only constant they share across all establishments, their SKU. When the user selects American Cheese now, all items that come with American Cheese by default will be put into a list and patched automatically. The data is pulled across various endpoints, the updated modifier prices are summed and compared to the free variable, and if they do not match anymore, the free field will be overwritten by the sum of the deafult mods and patched accordingly. This script takes what used to be a long tedious process and simplifies it dramatically. 

## Features

- Locates all impacted items when a specific modifier is selected
- Targets a specific establishment
- Automatically patches the items 

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/BLibs/PrimoModifierPatch/.git
    ```
2. Navigate to the project directory:
    ```sh
    cd PrimoModifierPatch
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

Update the `config.py` file in the project directory and define the following API variable:

```python
API = "APIKEY"
```

## Usage 

The script can either be ran directly as a Python file or compiled into an .exe with Pyinstaller
- Run the script to start the automation process:
    ```sh
    python main.py
    ```
- Compile the .exe which can then be ran in any environment.
    ```sh
    pyinstaller --onefile --clean main.py
