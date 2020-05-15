from anki.utils import ids2str, intTime
from typing import List
 

# More or less replaces the functions of the scheduler
class Drill:
    def __init__(self):
        self.deck = None
        self.col = None
        self.currentTag = None
        self.cursor = 0
        self.clearCache()


    # dumps all metadata for deck
    def clearCache(self):
        self.tagDict = None  


    # saves state information to deck JSON
    # currentTag, cursor position
    def save(self):
        if self.deck != None:
            self.deck["drillState"] = {
                "currentTag": self.currentTag,
                "cursor": self.cursor
            }
            self.col.decks.save(self.deck)



    # Called when studying is initiated from the Overview
    # received tag to study
    # sets current tag and cursor to beginning
    # returns nothing
    def onStudy(self, tag):
        if len(tag) > 0:
            self.currentTag = tag
        self.cursor = 0 # start from the beginning
        self.save()


    # DB query to create a tag dict object from the collection
    # queries DB for all cids and tags in the current deck(s?)
    # formats these into a useful dict member
    # return nothing
    def loadTagDict(self, col):
        lim = 2000 # meh?
        dids = ids2str(self.col.decks.active())
#         count = self.col.db.scalar(f"""
# select count() from (select id from cards where
# did in %s limit ?)"""
#             % dids,
#             lim,
#         )
#         print(count)
        # collect all the card ids now
        self.cardIds = self.col.db.list(
            f"""
        select id from cards where did in %s limit ?"""
            % dids,
            lim,
        )
        # collect all tags and card ids
        rows = self.col.db.all(
            f"""
        SELECT c.id, n.tags FROM cards c, notes n WHERE c.nid = n.id AND c.id IN %s LIMIT ?"""
            % ids2str(self.cardIds),
            lim
        )
        self.tagDict = self.groupByTags(rows)


    # returns card or None, called from reviewer.nextCard
    # increments cursor
    def getCard(self):
        # during normal reviewing, col.log(card), bury siblings, and card.startTimer() are called
        # do we want to do these things?
        if self.currentTag == None:
            keys = list(self.tagDict.keys())
            if len(keys) > 0:
                self.currentTag = keys[0] 
        cards = self.tagDict.get(self.currentTag, [])
        if len(cards) <= self.cursor:
            return None
        else:
            card = self.col.getCard(cards[self.cursor])
            self.cursor += 1
            if card:
                card.startTimer() # if we don't call this, we crash. nice.
            return card


    # do nothing for now
    # replaces default in reviewer
    # cursor is updated on getCard and not needed here
    def answerCard(self):
        pass


    # given sql rows containing [tag, cid]
    # return dict with shape { tag: [cids] }
    def groupByTags(self, rows):
        tagDict = {}
        for row in rows:
            tagStr = row[1]
            cid = row[0]
            tags = self.split(tagStr)
            for tag in tags:
                tagDict[tag] = tagDict.get(tag, []) + [cid]
        return tagDict

    
    # called by Overview
    # given collection
    # creates cache of cids and tags in tagDict
    # return list of tags
    def getTags(self, col):
        # will need to clear any cache of tags if set for a different deck
        self.setDeck(col)
        if self.tagDict == None:
            self.loadTagDict(col)
        return list(self.tagDict.keys())


    # if current deck is wrong, reload
    # if deck is unchanged, do nothing
    def setDeck(self, col):
        currentDeck = col.decks.current()
        if self.deck == None or self.deck["id"] != currentDeck["id"]:
            self.col = col
            self.deck = currentDeck
            if currentDeck.get("drillState", None) != None:
                self.currentTag = currentDeck["drillState"].get("currentTag", None)
                self.cursor = currentDeck["drillState"].get("cursor", 0)
            self.clearCache()


    # copy-paste from TagManger
    def split(self, tags: str) -> List[str]:
        "Parse a string and return a list of tags."
        return [t for t in tags.replace("\u3000", " ").split(" ") if t]