import requests

class NetworkClient:
    def __init__(self):
        self.url = None

    def fetch_json(self, host, file_name):
        self.url = f"http://{host}/player_tracking_shared_files/{file_name}.json"
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # Raise an error for bad responses
            return response.json()  # Return the JSON data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None


if __name__ == "__main__":
    client = NetworkClient()
    print(client.fetch_json("10.0.0.49", "current_team"))