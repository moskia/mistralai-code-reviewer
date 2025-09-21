import requests

def fetch_repo_contents(api_url, headers):
    all_files = []
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        contents = response.json()
        for item in contents:
            if item["type"] == "file":
                all_files.append({
                    "name": item["name"],
                    "path": item["path"],
                    "download_url": item["download_url"]
                })
            elif item["type"] == "dir":
                dir_files = fetch_repo_contents(item["url"], headers)
                all_files.extend(dir_files)
    else:
        print(f"Failed to fetch {api_url}: {response.status_code}")
    return all_files

def fetch_file_contents(file_urls, headers):
    contents = {}
    for file in file_urls:
        response = requests.get(file["download_url"], headers=headers)
        if response.status_code == 200:
            contents[file["path"]] = response.text
        else:
            contents[file["path"]] = f"Failed to fetch: {response.status_code}"
    return contents
