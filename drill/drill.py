from anki.utils import ids2str, intTime
from typing import List
import datetime
 

# More or less replaces the functions of the scheduler
class Drill:
    def __init__(self):
        self.deck = None
        self.col = None  # referencing collection or deck like this is dangerous for us
                         # on sync, and possibly other activities, Anki will discard
                         # the collection and create a new one
                         # in these cases, our reference will become invalid
                         # so this collection reference is set in self.setDeck
                         # which is called every time tags are requested.
                         # hopefully that is sufficient. But this probably isn't
                         # the most appropriate way to deal with this.
        self.currentTag = None
        self.tagMeta = {}
        self.cursor = 0
        self.clearCache()


    def onGuiReset(self):
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
                "cursor": self.cursor,
                "tagMeta": self.tagMeta
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


    
    # lazy loading of the tag dict
    def getTagDict(self):
        if self.tagDict == None:
            self.loadTagDict()
        return self.tagDict


    # DB query to create a tag dict object from the collection
    # queries DB for all cids and tags in the current deck(s?)
    # formats these into a useful dict member
    # return nothing
    def loadTagDict(self):
        lim = 10000 # meh?
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
            keys = list(self.getTagDict().keys())
            if len(keys) > 0:
                self.currentTag = keys[0] 
        cards = self.getTagDict().get(self.currentTag, [])
        if len(cards) <= self.cursor:
            return None
        else:
            card = self.col.getCard(cards[self.cursor])
            self.cursor += 1
            if card:
                card.startTimer() # if we don't call this, we crash. nice.
            return card


    # convenience
    def currentCardCount(self):
        return len(self.getTagDict().get(self.currentTag, []))

    
    #convenience
    def isEnd(self):
        return self.currentCardCount() <= self.cursor


    def tagReps(self, tag):
        meta = self.tagMeta.get(tag, {})
        return meta.get("reps", 0)

    
    def tagRepsToday(self, tag):
        if not self.isToday(self.tagLast(tag)):
            return 0
        else: 
            meta = self.tagMeta.get(tag, {})
            repsToday = meta.get("repsToday", 0)
            return repsToday
    

    def tagLast(self, tag):
        meta = self.tagMeta.get(tag, {})
        return meta.get("last", "")

    
    # convenience
    def currentReps(self):
        return self.tagReps(self.currentTag)

    # convenience
    def currentRepsToday(self):
        return self.tagRepsToday(self.currentTag)


    # safetly set metadata for tags
    def setCurrentMeta(self, key, value):
        meta = self.tagMeta.get(self.currentTag, None)
        if meta == None:
            meta = {
                "reps": 0,
                "repsToday": 0,
                "last": ""
            }
        meta[key] = value
        self.tagMeta[self.currentTag] = meta


    def isToday(self, isotimestamp):
        if isotimestamp == '':
            return True
        last = datetime.datetime.fromisoformat(isotimestamp)
        today = datetime.datetime.now()
        if last.day != today.day or last.month != today.month or last.year != today.year:
            return False
        else:
            return True


    def incrementReps(self):
        reps = self.currentReps()
        reps += 1
        self.setCurrentMeta("reps", reps)
        repsToday = self.currentRepsToday()
        if self.isToday(self.tagLast(self.currentTag)):
            repsToday += 1
        else:
            repsToday = 1
        self.setCurrentMeta("repsToday", repsToday)

    
    def updateLast(self):
        time = datetime.datetime.now().isoformat(sep=' ', timespec="seconds")
        self.setCurrentMeta("last", time)


    # detects if we are at end of cycle
    # records the time and adds to rep count
    def answerCard(self):
        if self.isEnd():
            self.incrementReps() # must be called before update last so the
                                 # old timestamp can be compared to the current
            self.updateLast()
            self.save()


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
    def getTags(self):
        return list(self.getTagDict().keys())


    # called on overview.reset()
    def load(self, col):
        self.col = col
        self.deck = col.decks.current()
        if self.deck.get("drillState", None) != None:
            self.currentTag = self.deck["drillState"].get("currentTag", None)
            self.cursor = self.deck["drillState"].get("cursor", 0)
            self.tagMeta = self.deck["drillState"].get("tagMeta", {})
        else:
            self.currentTag = None
            self.cursor = 0
            self.tagMeta = {}
        self.clearCache()


    # copy-paste from TagManger
    def split(self, tags: str) -> List[str]:
        "Parse a string and return a list of tags."
        return [t for t in tags.replace("\u3000", " ").split(" ") if t]