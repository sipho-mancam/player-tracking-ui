import requests
import time

# Number of requests to make (set to a large number for continuous requests)
num_requests = 10000

# Target URL
url = "http://127.0.0.1:5000/frame"  # Replace with your target endpoint

# Make requests at a rate of 10fps (100ms delay between requests)
for i in range(num_requests):
    try:
        response = requests.get(url)
        print(f"Request {i+1}: {response.status_code} - {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Request {i+1} failed: {e}")
    
    # Wait for 100ms before sending the next request
    time.sleep(0.1)  # 100ms = 0.1 seconds
