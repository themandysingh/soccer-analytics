from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as Soup
from player import Player
from event import Match_Event

class Match_Center_Scraping:
    STATS_BUTTON_CSS = '#mainContent > div > section > div.centralContent > div > div.wrapper.col-12 > div > div > ul > li:nth-child(3)'
    STATS_BUTTON_CONFIRMATION = '#mainContent > div > section > div.centralContent > div > div.mcTabs > section.mcMainTab.head-to-head.active > div.mcTabs > div.mcStatsTab.statsSection.season-so-far.wrapper.col-12.active > table > tbody > tr:nth-child(11)'
    LINEUPS_BUTTON_CSS = '#mainContent > div > section > div.centralContent > div.mcTabsContainer > div.wrapper.col-12 > div > div > ul > li.matchCentreSquadLabelContainer'
    LINEUPS_BUTTON_CONFIRMATION = '#mainContent > div > section > div.centralContent > div.mcTabsContainer > div.mcTabs > section.squads.mcMainTab.active > div > div > div.teamList.mcLineUpContainter.homeLineup.active > div > div > ul:nth-child(2) > li > a > div.info > span.nationality > span.playerCountry'

    def __init__(self, MATCH_URL):
        # Team Names
        self.home_team_name = None
        self.away_team_name = None

        # Match Info
        self.date = None
        self.referee = None
        self.attendance = None
        self.stadium = None
        self.score = None
        
        # Team Lineups
        self.home_captain = None
        self.away_captain = None
        self.home_starting_eleven = None
        self.away_starting_eleven = None
        self.home_subs = None
        self.away_subs = None

        self.match_url = MATCH_URL
        self.driver = webdriver.Chrome('/Users/mandy/soccer-analytics/scraping/chromedriver')
        self.driver.implicitly_wait(30)
        self.driver.get(self.match_url)
        self.stats_page_soup = self.get_stats_soup()
        self.lineups_page_soup = self.get_lineups_soup()
        self.driver.quit()

    def get_stats_soup(self):
        stats_button = self.driver.find_element_by_css_selector(self.STATS_BUTTON_CSS)
        stats_button.click()
        try:
            WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, self.STATS_BUTTON_CONFIRMATION)
            ))
        finally:
            return Soup(self.driver.page_source, "html.parser")

    def get_lineups_soup (self):
        lineups_button = self.driver.find_element_by_css_selector(self.LINEUPS_BUTTON_CSS)
        lineups_button.click()
        try:
            WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, self.LINEUPS_BUTTON_CONFIRMATION)
            ))
        finally:
            return Soup(self.driver.page_source, "html.parser")

    def get_match_events(self):
        events = self.lineups_page_soup.find('div', {'class':'timeLineEventsContainer'})
        home_events_soup = events.findAll('div', {'class': 'home'})
        away_events_soup = events.findAll('div', {'class': 'away'})
        home_events = self.extract_event_info(home_events_soup)
        away_events = self.extract_event_info(away_events_soup)
        return home_events, away_events
    
    def extract_event_info(self, events_soup_list):
        events = [None] * len(events_soup_list)
        event_count = 0
        for event_soup in events_soup_list:
            event = Match_Event()
            event.name = event_soup.span.text
            event.time = event_soup.find('time').text[:-1]
            events[event_count] = event
            event_count = event_count + 1
        return events

    def get_lineups(self):
        lineup_containers = self.lineups_page_soup.findAll('div', {'class':'matchLineupTeamContainer'})
        home_team_container = lineup_containers[0]
        away_team_container = lineup_containers[1]
        home_starting_eleven, home_subs = self.extract_players(home_team_container, 'home')
        away_starting_eleven, away_subs = self.extract_players(away_team_container, 'away')
        return [home_starting_eleven, home_subs], [away_starting_eleven, away_subs]

    def extract_players(self, team_container, side):
        team_container_children = team_container.findChildren(recursive=False)
        position = None
        starting_eleven = {}
        substitutes = {}
        for child in team_container_children:
            if child.name == 'h3':
                position = child.text
            else:
                player_lines = child.findAll('li')
                for line in player_lines:
                    player = self.create_player_profile(line, position, side)
                    
                    if position == 'Substitutes':
                        substitutes[player.number] = player
                    else:
                        starting_eleven[player.number] = player

                    
        return starting_eleven, substitutes

    def create_player_profile(self, line, position, side):
        player = Player()
        player_info_divs = line.a.findAll('div')
        player.number = int(player_info_divs[0].text.split(' ')[2])
        player.name = player_info_divs[1].find('span', {'class':'name'}).text.replace(player_info_divs[1].find('span', {'class':'name'}).div.text, '')
        player.nationality = player_info_divs[1].find('span', {'class':'playerCountry'}).text
        player.position = position
        if len(player_info_divs) > 3:
            player.captain = True
            if side == 'home':
                self.home_captain = player
            else:
                self.away_captain = player
        
        if position == 'Substitutes':
            player.position = player_info_divs[1].find('span', {'class':'position'}).text
        
        return player

    def get_teams(self):
        stats_table = self.stats_page_soup.find('tbody', {'class': 'matchCentreStatsContainer'}).parent
        teams = stats_table.thead.findAll("a")
        self.home_team_name = teams[0].text.strip()
        self.away_team_name = teams[1].text.strip()

    def get_team_stats(self):
        stats_table = self.stats_page_soup.find('tbody', {'class': 'matchCentreStatsContainer'}).parent
        stats = stats_table.tbody.findAll('tr')
        home_stats = {}
        away_stats = {}
        for stat in stats:
            stat = stat.findAll('p', {})
            home_stats[stat[1].text] = stat[0].text
            away_stats[stat[1].text] = stat[2].text
        return home_stats, away_stats

    def get_match_info(self):
        infoBar = self.stats_page_soup.find('div', {'class': 'matchInfo'})
        self.date = infoBar.find('div', {'class':'matchDate'}).text
        self.referee = infoBar.find('div', {'class':'referee'}).text.strip()
        self.stadium = infoBar.find('div', {'class':'stadium'}).text
        self.attendance = infoBar.find('div', {'class':'attendance'}).text.split(' ')[1]
        self.score = self.stats_page_soup.find('div', {'class': 'score'}).text.split('-')


if __name__ == '__main__':
	match_center = Match_Center_Scraping('https://www.premierleague.com/match/46610')

home_events, away_events = match_center.get_match_events()
for home_event in home_events:
    print(home_event.name, home_event.time)
print()
print('away stuff')
for away_event in away_events:
    print(away_event.name, away_event.time)

