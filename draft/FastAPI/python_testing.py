# "http://127.0.0.1:8000/docs#"
# "http://127.0.0.1:8000/redoc"

import requests

url = "http://127.0.0.1:8000/items"

data = {"text": "Apple"}
response = requests.post(url, json=data)

item_id = 0
response = requests.get(url+f"/{item_id}")
print(response.json())

# import requests

# url = "http://127.0.0.1:8000/items"

# data = {"text": "Apple"}
# response = requests.post(url, json=data)

# print(response.status_code)
# print(response.json())

# print(f"{'-' * 50}")

# data = {"text": "Banana"}
# response = requests.post(url, json=data)

# print(response.status_code)
# print(response.json())

# print(f"{'-' * 50}")

# item_id = 0
# response = requests.get(url+f"/{item_id}")

# print(response.status_code)
# print(response.json())

# print(f"{'-' * 50}")

# response = requests.get(url+f"/{item_id}")

# print(response.status_code)
# print(response.json())
