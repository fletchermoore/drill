# import the main window object (mw) from aqt
from aqt import mw
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
def patchedOverviewState(self, oldState: str) -> None:
    if not self._selectedDeck():
        return self.moveToState("deckBrowser")
    self.col.reset()
    if self.col.decks.current().get("drill", False):
        if not hasattr(self, "drillOverview"):
            from drill.drilloverview import DrillOverview
            self.drillOverview = DrillOverview(self)
        self.drillOverview.show()
    else:
        self.overview.show()

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

# Monkey Patching
from aqt.main import AnkiQt
AnkiQt._overviewState = patchedOverviewState
AnkiQt.onDeckConf = patchedOnDeckConf

# create a new menu item
action = QAction("Drill", mw)
action.triggered.connect(onDrill)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
