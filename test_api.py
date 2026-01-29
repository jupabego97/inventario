import requests

ALEGRA_API_URL = 'https://api.alegra.com/api/v1'
ALEGRA_API_KEY = 'bmFub3Ryb25pY3NhbHNvbmRlbGF0ZWNub2xvZ2lhQGdtYWlsLmNvbTphMmM4OTA3YjE1M2VmYTc0ODE5ZA=='

# Probar consultar un item (ID 10 como ejemplo)
url = f'{ALEGRA_API_URL}/items/10'
headers = {
    'accept': 'application/json',
    'authorization': f'Basic {ALEGRA_API_KEY}'
}
response = requests.get(url, headers=headers, timeout=30)
print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print(f"Item ID: {data.get('id')}")
    print(f"Nombre: {data.get('name')}")
    inv = data.get('inventory', {})
    print(f"Cantidad disponible: {inv.get('availableQuantity')}")
    print(f"Costo unitario: {inv.get('unitCost')}")
    price_list = data.get('price', [])
    if price_list:
        print(f"Precio: {price_list[0].get('price')}")
else:
    print(f'Error: {response.text}')
