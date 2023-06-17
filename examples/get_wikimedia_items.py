import json
from bs4 import BeautifulSoup
import requests

'''
Archivo para obtener listas de items a través de la API de Fandom (Wikimedia)
y guardarlo en un documento JSON para su posterior uso (un poco más eficiente) en el bot.
Consiste en obtener una lista de items de una categoría de la wiki a través de la API y luego
scrapear cada página de item para obtener información adicional (como la imagen y el género).
'''

WIKI_PAGE = "example.fandom.com" # constant value for the wiki page to scrape
CATEGORY = "Characters" # constant value for the category to scrape

def _get_character_list():
    # Set up Fandom API endpoint and parameters
    api_url = f"https://{WIKI_PAGE}/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": f"Category:{CATEGORY}",
        "cmlimit": "max",
        "cmtype": "page"
    }

    character_list = []
    continue_token = None
    while True:
        # Add continue token to params if it exists
        if continue_token:
            params['cmcontinue'] = continue_token

        # Send API request and parse response
        response = requests.get(api_url, params=params)
        data = response.json()
        pages = data['query']['categorymembers']

        # Scrape thumbnail images and gender from each character page
        for page in pages:
            name: str = page['title']

            # Skip subcategories and templates
            if name.startswith("Category") or name.startswith("Template") or name.startswith("List of") or name.startswith("Interview") or name.startswith("User"):
                continue

            page_url = f"https://{WIKI_PAGE}/wiki/{name.replace(' ', '_')}"
            page_content = requests.get(page_url).content
            soup = BeautifulSoup(page_content, 'html.parser')
            image = soup.find('div', attrs={'data-source': 'image'})
            gender = soup.find('div', attrs={'data-source': 'gender'})
            
            if gender is not None:
                gender_value = gender.find('div', class_='pi-data-value pi-font').text.strip()
                
                # Normalize gender values
                if (gender_value not in ('Male', 'Female')):
                    male_pronouns = ['he', 'him', 'his', 'male', 'boy', 'man']
                    for pronoun in male_pronouns:
                        if pronoun in gender_value.lower():
                            gender_value = "Male"
                            break
                    else:
                        female_pronouns = ['she', 'her', 'female', 'girl', 'woman']
                        for pronoun in female_pronouns:
                            if pronoun in gender_value.lower():
                                gender_value = "Female"
                                break
                        else:
                            gender_value = "Unknown"
            else:
                gender_value = "Unknown"

            # Add character to list
            if image is not None:
                image_url = image.find('img')['src']
                character_list.append(
                    {'name': name,
                     'image': image_url,
                     'gender': gender_value
                     })
                print(f"Added {name} to list")

        # Check if there are more results to get
        if 'continue' in data:
            continue_token = data['continue']['cmcontinue']
        else:
            break

    return character_list

# Get list of all characters
json_str = json.dumps(_get_character_list(), ensure_ascii=False)

# Escribir en un archivo
with open("./characterlist.json", "w", encoding="utf-8") as file:
    # Write some text to the file
    file.write(json_str)
