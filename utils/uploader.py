import requests


def upload_to_temp(file_path):
    url = "https://tmpfiles.org/api/v1/upload"
    with open(file_path, 'rb') as file:
        response = requests.post(url, files={"file": file})
    if response.status_code == 200:
        data = response.json()
        return data.get("data", {}).get("url")
    else:
        print("Failed to upload file:", response.text)
        return None
