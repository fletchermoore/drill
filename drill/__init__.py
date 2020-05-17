# import the main window object (mw) from aqt
from aqt import mw, gui_hooks
# import the "show info" tool from utils.py
from aqt.utils import showInfo
# import all of the Qt GUI library
from aqt.qt import *

# imports added for my own code
import copy
from anki.decks import defaultDynamicDeck
import drill.drilldeckconf as drillDiag


# copy-paste of main.py onCram
def onDrill(self, search=""):
    n = 1
    deck = mw.col.decks.current()
    if not search:
        if not deck["dyn"]:
            search = 'deck:"%s" ' % deck["name"]
    decks = mw.col.decks.allNames()
    while _("Drill %d") % n in decks:
        n += 1
    name = _("Drill %d") % n
    #did = mw.col.decks.newDyn(name)
    did = newDrill(mw.col.decks, name) #replaces above line
    diag = drillDiag.DeckConf(mw, first=True, search=search)
    if not diag.ok:
        # user cancelled first config
        mw.col.decks.rem(did)
        mw.col.decks.select(deck["id"])


# copy-paste DeckManager.newDyn
def newDrill(decks, name: str) -> int:
    "Return a new dynamic deck and set it as the current deck."
    deckDetails = copy.deepcopy(defaultDynamicDeck)
    deckDetails['drill'] = True # adding our own flag so we can do something 
                                # wild during review
    did = decks.id(name, type=deckDetails)
    decks.select(did)
    return did


# copy-paste w/ check for drill flag
def patchedOnDeckConf(self, deck=None):
    if not deck:
        deck = self.col.decks.current()
    if deck["dyn"]:
        if not deck.get("drill", False):
            import aqt.dyndeckconf
            aqt.dyndeckconf.DeckConf(self, deck=deck)
        else:
            drillDiag.DeckConf(self, deck=deck)
    else:
        import aqt.deckconf

        aqt.deckconf.DeckConf(self, deck)


# prior to moving to reviewer, if we are studying a drill deck, switch to my custom reviewer
# otherwise, switch back to default
def onStateWillChange(state, oldState):
    deck = mw.col.decks.current()
    if not deck.get("drill", False):
        mw.reviewer = mw.normalReviewer
        mw.overview = mw.normalOverview
    else:
        mw.reviewer = mw.drillReviewer  
        mw.overview = mw.drillOverview 


# Monkey Patching
from aqt.main import AnkiQt
#AnkiQt._overviewState = patchedOverviewState # ensure switch to custom drill overview on state change
AnkiQt.onDeckConf = patchedOnDeckConf # ensure open drill option page
#AnkiQt._reviewState = patchedReviewState # swaps reviewers


# create a new menu item
action = QAction("Drill", mw)
action.triggered.connect(onDrill)
# and add it to the tools menu
mw.form.menuTools.addAction(action)


# plugin __init__.py code executes right after mw.setupUI(), so we can just add our Reviewer here
# on state changes we are going to swap the reviewer and overview
from drill.drillreviewer import DrillReviewer
mw.drillReviewer = DrillReviewer(mw)
mw.normalReviewer = mw.reviewer # create a second link to swap them out
# same thing with the Overview page
from drill.drilloverview import DrillOverview
mw.drillOverview = DrillOverview(mw)
mw.normalOverview = mw.overview # create a reference


# our scheduler
from drill.drill import Drill
mw.drill = Drill()

# add hooks
gui_hooks.state_will_change.append(onStateWillChange)
gui_hooks.state_did_reset.append(mw.drill.onGuiReset)
