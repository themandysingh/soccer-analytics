from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup as Soup

MATCH_URL = 'https://www.premierleague.com/match/2'
driver = webdriver.Chrome('/Users/mandy/soccer-analytics/scraping/chromedriver')
driver.implicitly_wait(30)
driver.get(MATCH_URL)

stats_button = driver.find_element_by_css_selector('#mainContent > div > section > div.centralContent > div > div.wrapper.col-12 > div > div > ul > li:nth-child(3)')
stats_button.click()
try:
	WebDriverWait(driver, 10).until()

page_soup = Soup(driver.page_source, "html.parser")
driver.quit()


def get_teams(stats_head):
	teams = stats_head.findAll("a")
	return teams[0].text.strip(), teams[1].text.strip()

def get_team_stats(stats_body):
	stats = stats_body.findAll('tr')
	home_stats = {}
	away_stats = {}
	for stat in stats:
		stat = stat.findAll('p', {})
		home_stats[stat[1].text] = stat[0].text
		away_stats[stat[1].text] = stat[2].text
	return home_stats, away_stats

stats_table = page_soup.find('tbody', {'class': 'matchCentreStatsContainer'}).parent
home_team, away_team = get_teams(stats_table.thead)
home_stats, away_stats = get_team_stats(stats_table.tbody)
print(home_team)
print(home_stats)
print()
print(away_team)
print(away_stats)
