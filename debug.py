import configparser, json
from bs4 import BeautifulSoup

def parse_page( page ):
    soup = BeautifulSoup(page, 'lxml')  
    stations = soup.find_all('text', class_ = "label")
    states = {}
    for st in stations:
        stat = {
            "name" : "",
            "id" : 0
        }
        id = st.get('data-st-id')
        if id:
            stat["name"] = st.get_text()
            stat["id"] = int(id)
            # states.append(stat)
            states[st.get_text()] = int(id)
            print( stat["name"], stat["id"] )
    with open("metro.json", 'w', encoding='utf-8', newline='') as fp:
        json.dump(states, fp, ensure_ascii=False, indent=4)

def main():
    pass

if __name__ == "__main__":
    main()
