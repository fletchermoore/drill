from anki.utils import ids2str, intTime
from typing import List
 

# More or less replaces the functions of the scheduler
class Drill:
    # def __init__(self):
    #     pass
    # #self.col = col

    # Called when studying is initiated from the Overview
    def onStudy(self, col):
        self.col = col # will we need this later?
        print("study begins, let's figure out what cards we got")
        # sort and list cards by tag

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


    # copy-paste from TagManger
    def split(self, tags: str) -> List[str]:
        "Parse a string and return a list of tags."
        return [t for t in tags.replace("\u3000", " ").split(" ") if t]