import os

password = "admin123"


def calculate_total(price, quantity):
    total = price * quantity
    return total


def get_user_data(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return query


def unused_function():
    x = 10
    y = 20
    return x


print(calculate_total(100, 5))
print(get_user_data("1"))