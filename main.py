from lxml import html
import requests

# URL of the GitHub repository contributors page
url = 'https://github.com/gsainfoteam/ziggle-fe/graphs/contributors?from=2023-07-03&to=2024-02-17&type=c'

# Make a GET request to fetch the HTML content
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content
    tree = html.fromstring(response.content)
    
    # Perform the XPath search for the given path
    element = tree.xpath("//*[@id='contributors']/ol/li[2]/span/h3/a[2]")
    
    if element:
        # Assuming you want the text within this element
        print(element[0].text)
    else:
        print("Element not found")
else:
    print(f"Failed to fetch HTML content: {response.status_code}")

# If you need to save the HTML content to a file:
# with open('contributors.html', 'w') as file:
#     file.write(html_content)
