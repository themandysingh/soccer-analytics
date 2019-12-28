from match_centre_scraping_utility import Match_Center_Scraping

BASE_URL = 'https://www.premierleague.com/match/'
match_code = 46609

for i in range(match_code, match_code + 10):
	match_url = BASE_URL + str(i)
	match = Match_Center_Scraping(match_url)
	print(match.get_teams())