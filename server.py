from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from escpos.printer import File
import json
import os
import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/")
def index():
    return send_from_directory('./', 'koez.html')

# Path to products.json
PRODUCTS_FILE = './products.json'

@app.route("/products", methods=["GET"])
def get_products():
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify({"products": []})

@app.route("/update_pin", methods=["POST"])
def update_pin():
    data = request.json
    item_id = data.get("id")
    pinned = data.get("pinned")
    if not item_id:
        return jsonify({"status": "error", "message": "ID required"})
    
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            content = json.load(f)
        products = content.get("products", [])
        for product in products:
            if product["id"] == item_id:
                product["pinned"] = pinned
                break
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump(content, f, indent=4)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "File not found"})


def print_order(items, customer_name):
    try:
        # Open the printer device as a file
        printer = File("/dev/usb/lp0")
        printer.charcode(code='CP858')  # Set encoding to CP858

        # Print the kitchen order (ID and item)
        printer.set(align="center", font="b")
        printer.image('MF.png')
        printer.text("\n\n")
        IDStr = str(id)
        for item in items:
            if IDStr != "VZ":
                printer.set(align="left", font="a")
                printer.text(f"{item['id']} - {item['name']}\n")
            elif id == "":
                print("test")

        printer.cut(mode='part')

        # Add a line break
        printer.text("\n\n\n")
        
        # Print the customer order (Name, ID, item, price)
        printer.set(align="center", font="b")
        printer.text("********** ")
        timeNow = datetime.datetime.now()
        printer.text(timeNow.strftime("%x %X"))
        printer.text(' **********\n')
        total_price = 0  # Initialize total price
        
        for item in items:
            # Customer order (Name, ID, item, price)
            printer.set(align="left", font="a")
            printer.text(f"{item['customer']} - {item['name']} (ID: {item['id']}) - €: {item['price']}\n")
            total_price += item['price']  # Add the price to the total

        # Print the total price
        printer.text(f"\nTotal Price: €{total_price:.2f}\n")

        # Add cut paper command
        printer.cut(mode='part')
        
        # Close the printer connection
        printer.close()
        return {"status": "success", "message": "Printed successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route("/print", methods=["POST"])
def handle_print():
    # Get the order items and customer name from the request
    order_data = request.json.get("items", [])
    customer_name = request.json.get("customer_name", "")
    
    # Set the combined orders to the current order data (do not accumulate)
    global orders
    orders = order_data
    
    # Get all combined orders
    all_orders = orders
    
    # Call the print function with the entire customer order history
    result = print_order(all_orders, customer_name)
    
    # Return response
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=False)
