3 notable technical elements

1. At the beginning, I struggled with the fact (fact? My own impression?) that with .csv files, it's not as easy to implement an auto-increment feature in the Python as it is with Peewee. However, my .txt files that use simple strings to 'auto-increment' the entries in the .csv files do the trick. 

2. After a while, I arrived at the point at which I had to remove a product after it was sold. This took me a while. A whole weekend in fact. How I solved it? By taking a break from coding, taking a closer look at Pandas and tackling the problem one small step at a time. This is what I ultimately came up with. I definitely didn't think of this in one go, it was a case of stackoverflow + trial and error.

   data = data[data.id != int(id_of_product_to_be_sold)]  

3. Separation of responsibility. When thinking about keeping track of bought products, I decided it was best to use a separate function to add products to inventory.csv. I could have implemented the below piece of code inside the function 'track_bought_products', but the upside of using a separate function is that this will make it easier in the future to als use the application for products to become part of the inventory without being bought. Example: it could be that the supermarket gets a shipment of products from their headquarters, stating that another supermarket is having trouble selling the products at their location. There needs to be a way to add those products to the inventory without calling the function 'track_bought_products'. 

def add_to_inventory(product_name: str, buying_price: float, expiration_date: str):
    with open('inventory.csv', mode='a', newline='') as inventory:
        new_id_for_each_row = open('unique_ids_for_inventory.txt', mode='r').read()
        csv_writer = csv.writer(inventory, delimiter=',', lineterminator='\n') 
        row = [
            new_id_for_each_row, 
            product_name, 
            buying_price, 
            expiration_date
            ] 
        csv_writer.writerow(row)
        open('unique_ids_for_inventory.txt', mode='w').write(str(int(new_id_for_each_row) + 1))      