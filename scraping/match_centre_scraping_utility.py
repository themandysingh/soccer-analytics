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
        self.home_team_formation = None
        self.away_team_formation = None

        # Team Stats
        self.home_stats = None
        self.away_stats = None

        # Match Events
        self.home_events = None
        self.away_event = None


        self.match_url = MATCH_URL
        self.driver = webdriver.Chrome('/Users/mandy/soccer-analytics/scraping/chromedriver')
        self.driver.implicitly_wait(30)
        self.driver.get(self.match_url)
        self.stats_page_soup = self.get_stats_soup()
        self.lineups_page_soup = self.get_lineups_soup()
        self.driver.quit()

        self.get_teams()

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

    # Need to call this function after calling self.get_lineups()
    def get_match_events(self):
        events = self.lineups_page_soup.find('div', {'class':'timeLineEventsContainer'})
        home_events_soup = events.findAll('div', {'class': 'home'})
        away_events_soup = events.findAll('div', {'class': 'away'})
        self.home_events = self.extract_event_info(home_events_soup, self.home_team_name)
        self.away_events = self.extract_event_info(away_events_soup, self.away_team_name)
    
    def extract_event_info(self, events_soup_list, side):
        players = None
        subs = None
        if side == self.home_team_name:
            players = self.home_starting_eleven
            subs = self.home_subs
        else:
            players = self.away_starting_eleven
            subs = self.away_subs
        events = [None] * len(events_soup_list)
        event_count = 0
        for event_soup in events_soup_list:
            event = Match_Event()
            event.team = side
            event.name = event_soup.span.text
            event.time = event_soup.find('time').text[:-1]
            event.score = event_soup.find('div', {'class':'teamScore'}).text.strip().split('\n')[2]
            player_number = int(event_soup.find('div', {'class':'eventPlayerInfo'}).text.strip().split('.')[0])
            if event.name == 'Substitution':
                sub_player_number = int(event_soup.find('div', {'class':'subOn'}).text.strip().split('.')[0])
                event.subOn = subs[sub_player_number]
                players[player_number].subOff = True
                players[player_number].playerSubbedOn = subs[sub_player_number]
                subs[sub_player_number].subOn = True
                subs[sub_player_number].subbedOnFor = players[player_number]
            
            if players[player_number] == None:
                event.player = subs[player_number]
            else:
                event.player = players[player_number]

            self.updatePlayerEvents(event)
            events[event_count] = event
            event_count = event_count + 1
        return events

    def updatePlayerEvents(self, event):
        if event.name == 'Goal':
            event.player.goals += 1
        elif event.name == 'Yellow Card':
            event.player.yc += 1
        elif event.name == 'Red Card':
            event.player.rc += 1

    def get_lineups(self):
        self.get_team_formation()
        lineup_containers = self.lineups_page_soup.findAll('div', {'class':'matchLineupTeamContainer'})
        home_team_container = lineup_containers[0]
        away_team_container = lineup_containers[1]
        home_starting_eleven, home_subs = self.extract_players(home_team_container, self.home_team_name)
        away_starting_eleven, away_subs = self.extract_players(away_team_container, self.away_team_name)
        self.home_starting_eleven = home_starting_eleven
        self.home_subs = home_subs 
        self.away_starting_eleven = away_starting_eleven
        self.away_subs = away_subs

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
                        player.startingEleven = False
                        substitutes[player.number] = player
                    else:
                        starting_eleven[player.number] = player

                    
        return starting_eleven, substitutes

    def create_player_profile(self, line, position, side):
        player = Player()
        player_info_divs = line.a.findAll('div')
        player.number = int(player_info_divs[0].text.split(' ')[2])
        player.name = player_info_divs[1].find('span', {'class':'name'}).text.replace(player_info_divs[1].find('span', {'class':'name'}).div.text, '')
        player.country = player_info_divs[1].find('span', {'class':'playerCountry'}).text
        player.position = position
        player.club = side
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
    
    def get_team_formation(self):
        lineups = self.lineups_page_soup.findAll('strong', {'class' : 'matchTeamFormation'})
        self.home_team_formation = lineups[0].text
        self.away_team_formation = lineups[1].text

    def get_team_stats(self):
        stats_table = self.stats_page_soup.find('tbody', {'class': 'matchCentreStatsContainer'}).parent
        stats = stats_table.tbody.findAll('tr')
        home_stats = {}
        away_stats = {}
        for stat in stats:
            stat = stat.findAll('p', {})
            home_stats[stat[1].text] = stat[0].text
            away_stats[stat[1].text] = stat[2].text
        self.home_stats = home_stats
        self.away_stats = away_stats

    def get_match_info(self):
        infoBar = self.stats_page_soup.find('div', {'class': 'matchInfo'})
        self.date = infoBar.find('div', {'class':'matchDate'}).text
        self.referee = infoBar.find('div', {'class':'referee'}).text.strip()
        self.stadium = infoBar.find('div', {'class':'stadium'}).text
        self.attendance = infoBar.find('div', {'class':'attendance'}).text.split(' ')[1]
        self.score = self.stats_page_soup.find('div', {'class': 'score'}).text.split('-')


if __name__ == '__main__':
	match_center = Match_Center_Scraping('https://www.premierleague.com/match/46610')

# Testing get_match_info()
# match_center.get_match_info()
# print(match_center.date)
# print(match_center.referee)
# print(match_center.stadium)
# print(match_center.attendance)
# print(match_center.score)

# Testing get_team_stats()
# match_center.get_team_stats()
# for stat in match_center.home_stats:
#     print(stat, match_center.home_stats[stat])
# print()
# for stat in match_center.away_stats:
#     print(stat, match_center.away_stats[stat])
# match_center.get_lineups()

# Testing get_teams()
# match_center.get_teams()
# print(match_center.home_team_name, match_center.away_team_name)

# Testing get_lineups()
# match_center.get_lineups()
# match_center.get_match_events()
# print(match_center.home_subs[23].subbedOnFor.name)
match_center.get_lineups()
match_center.get_match_events()
for home_event in match_center.home_events:
    print(home_event.name, home_event.time, home_event.score)
print()
print('away stuff')
for away_event in match_center.away_events:
    print(away_event.name, away_event.time, away_event.score)

print(match_center.home_starting_eleven[10].yc)

