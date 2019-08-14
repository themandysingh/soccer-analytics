import bs4
from urllib.request import urlopen as uReq
from bs4 import BeautifulSoup as Soup

MATCH_URL = 'https://www.premierleague.com/match/46609'
uClient = uReq(MATCH_URL)
page_html = uClient.read()
uClient.close()
page_soup = Soup(page_html, "html.parser")


def get_teams(page_soup):
	teams = page_soup.findAll("div", {"class": "mcStatsTab"})[0].findAll("a")
	return teams[0].text.strip(), teams[1].text.strip()


home_team, away_team = get_teams(page_soup)
print(home_team)
print(away_team)