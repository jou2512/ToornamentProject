import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI

app = FastAPI()


def get_player_data(tournament_id, stage_id):
    base_url = f"https://play.toornament.com/en_GB/tournaments/{tournament_id}/stages/{stage_id}/"
    response = requests.get(base_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        players = []
        pool_links = soup.find_all('a', href=True)
        for link in pool_links:
            if "/groups/" in link['href']:
                pool_url = "https://play.toornament.com" + link['href']
                pool_players = get_players_from_pool(pool_url)
                players.extend(pool_players)
        sorted_players = sort_players(players)
        return sorted_players
    else:
        raise Exception("Fehler beim Abrufen der Daten")


def get_players_from_pool(pool_url):
    response = requests.get(pool_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        pool_title = soup.find(
            'div', class_='weight-1 mobile-size-full tablet-size-full').text.strip()
        player_items = soup.select("div.off.ranking-container")
        pool_players = []
        for item in player_items:
            rank = item.find('div', class_='rank').text
            name = item.find('div', class_='name').text.strip()
            metrics = item.find_all('div', class_='metric')
            played = int(metrics[0].text.strip())
            wins = int(metrics[1].text.strip())
            score_difference = int(metrics[7].text.strip())
            # Calculate the index (wins/played)
            index = wins / played if played > 0 else 0
            pool_players.append({
                'name': name,
                'index': index,
                'played': played,
                'wins': wins,
                'score_difference': score_difference,
                'rank': rank,
                'pool': pool_title
            })
        return pool_players
    else:
        raise Exception("Fehler beim Abrufen der Daten")


def sort_players(players):
    players.sort(key=lambda x: (
        x['index'], x['score_difference']), reverse=True)
    current_rank = 1
    for idx, player in enumerate(players):
        if idx > 0 and player['index'] == players[idx - 1]['index'] and player['score_difference'] == players[idx - 1]['score_difference']:
            player['rank'] = players[idx - 1]['rank']
        else:
            player['rank'] = current_rank
        current_rank += 1
    return players


@app.get("/get_player_data/")
async def get_player_data_endpoint(tournament_id: str, stage_id: str):
    return get_player_data(tournament_id, stage_id)


@app.get("/get_reduced_player_data/")
async def get_reduced_player_data_endpoint(tournament_id: str, stage_id: str):
    player_data = get_player_data(tournament_id, stage_id)
    reduced_data = [{"index": player["index"], "name": player["name"],
                     "rank": player["rank"]} for player in player_data]
    return reduced_data
