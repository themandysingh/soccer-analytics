class Player:
    def __init__(self, name=None, country=None, club=None, position=None, captain=False, number=None,
    startingEleven=True, goals=0, yc=0, rc=False, subOn=False, subOff=False):
        self.name = name
        self.country = country
        self.club = club
        self.position = position
        self.captain = captain
        self.number = number
        self.startingEleven = startingEleven
        self.goals = goals
        self.yc = yc
        self.rc = rc
        self.subOn = subOn
        self.subOff = subOff
        self.playerSubbedOn = None
        self.subbedOnFor = None
    
    # Created this just to debug
    def __str__(self):
        if self.playerSubbedOn == None or self.subbedOnFor == None:
            return '{} {} {} {} {} {} {} {} {} {} {} {} {} {} '.format(self.name, self.country, self.club, self.position, self.captain, self.number, self. startingEleven, self.goals, self.yc, self.rc, self.subOn, self.subOff, self.playerSubbedOn, self.subbedOnFor)
        else:
            return '{} {} {} {} {} {} {} {} {} {} {} {} {} {} '.format(self.name, self.country, self.club, self.position, self.captain, self.number, self. startingEleven, self.goals, self.yc, self.rc, self.subOn, self.subOff, self.playerSubbedOn.name, self.subbedOnFor.name)