# -*- coding: utf-8 -*-
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

from dataclasses import dataclass

import aqt
from anki.lang import _
from aqt import gui_hooks
from aqt.sound import av_player
from aqt.toolbar import BottomBar
from aqt.utils import askUserDialog, openLink, shortcut, tooltip
import datetime


class DrillOverviewBottomBar:
    def __init__(self, overview: Overview):
        self.overview = overview


@dataclass
class DrillOverviewContent:
    """Stores sections of HTML content that the overview will be
    populated with.

    Attributes:
        deck {str} -- Plain text deck name
        shareLink {str} -- HTML of the share link section
        desc {str} -- HTML of the deck description section
        table {str} -- HTML of the deck stats table section
    """

    deck: str
    shareLink: str
    desc: str
    table: str
    tags: str


class DrillOverview:
    "Deck overview."

    def __init__(self, mw: aqt.AnkiQt) -> None:
        self.mw = mw
        self.web = mw.web
        self.bottom = BottomBar(mw, mw.bottomWeb)

    def show(self):
        av_player.stop_and_clear_queue()
        self.web.set_bridge_command(self._linkHandler, self)
        self.mw.setStateShortcuts(self._shortcutKeys())
        self.refresh()

    def refresh(self):
        self.mw.col.reset()
        self._renderPage()
        self._renderBottom()
        self.mw.web.setFocus()
        gui_hooks.overview_did_refresh(self)

    
    # increment to the next tag, or roll back to the beginning
    # then start studying
    # called by user action/link
    def studyNextTag(self):
        tags = self.mw.drill.getTags(self.mw.col)
        currentTag = self.mw.drill.currentTag
        # set a reasonable default: first tag, or ''
        nextTag = ''
        if len(tags) > 0:
            nextTag = tags[0]
        # pick subsequent tag if exists
        tagCount = len(tags)
        for i, tag in enumerate(tags):
            if tag == currentTag and (i + 1) < tagCount:
                nextTag = tags[i+1]
                break
        # start studying
        self.startStudying(nextTag)

    
    # begins study state and move to reviewer
    def startStudying(self, tag):
        self.mw.col.startTimebox()
        self.mw.drill.onStudy(tag)
        self.mw.moveToState("review") 
        if self.mw.state == "overview":
            tooltip(_("No cards are due yet."))




    # Handlers
    ############################################################

    def _linkHandler(self, url):
        if url.startswith("study"):
            tag = url[6:] # returns '' if out of bounds
            self.startStudying(tag)
        elif url == "next":
            self.studyNextTag()
        elif url == "anki":
            print("anki menu")
        elif url == "opts":
            self.mw.onDeckConf()
        elif url == "cram":
            deck = self.mw.col.decks.current()
            self.mw.onCram("'deck:%s'" % deck["name"])
        elif url == "refresh":
            self.mw.col.sched.rebuildDyn()
            self.mw.reset()
        elif url == "empty":
            self.mw.col.sched.emptyDyn(self.mw.col.decks.selected())
            self.mw.reset()
        elif url == "decks":
            self.mw.moveToState("deckBrowser")
        elif url == "review":
            openLink(aqt.appShared + "info/%s?v=%s" % (self.sid, self.sidVer))
        elif url == "studymore":
            self.onStudyMore()
        elif url == "unbury":
            self.onUnbury()
        elif url.lower().startswith("http"):
            openLink(url)
        return False

    def _shortcutKeys(self):
        return [
            ("o", self.mw.onDeckConf),
            ("r", self.onRebuildKey),
            ("e", self.onEmptyKey),
            ("c", self.onCustomStudyKey),
            ("u", self.onUnbury),
            ("n", self.studyNextTag)
        ]

    def _filteredDeck(self):
        return self.mw.col.decks.current()["dyn"]

    def onRebuildKey(self):
        if self._filteredDeck():
            self.mw.col.sched.rebuildDyn()
            self.mw.reset()

    def onEmptyKey(self):
        if self._filteredDeck():
            self.mw.col.sched.emptyDyn(self.mw.col.decks.selected())
            self.mw.reset()

    def onCustomStudyKey(self):
        if not self._filteredDeck():
            self.onStudyMore()

    def onUnbury(self):
        if self.mw.col.schedVer() == 1:
            self.mw.col.sched.unburyCardsForDeck()
            self.mw.reset()
            return

        sibs = self.mw.col.sched.haveBuriedSiblings()
        man = self.mw.col.sched.haveManuallyBuried()

        if sibs and man:
            opts = [
                _("Manually Buried Cards"),
                _("Buried Siblings"),
                _("All Buried Cards"),
                _("Cancel"),
            ]

            diag = askUserDialog(_("What would you like to unbury?"), opts)
            diag.setDefault(0)
            ret = diag.run()
            if ret == opts[0]:
                self.mw.col.sched.unburyCardsForDeck(type="manual")
            elif ret == opts[1]:
                self.mw.col.sched.unburyCardsForDeck(type="siblings")
            elif ret == opts[2]:
                self.mw.col.sched.unburyCardsForDeck(type="all")
        else:
            self.mw.col.sched.unburyCardsForDeck(type="all")

        self.mw.reset()

    # HTML
    ############################################################

    def _renderPage(self):
        but = self.mw.button
        deck = self.mw.col.decks.current()
        self.sid = deck.get("sharedFrom")
        if self.sid:
            self.sidVer = deck.get("ver", None)
            shareLink = '<a class=smallLink href="review">Reviews and Updates</a>'
        else:
            shareLink = ""
        content = DrillOverviewContent(
            deck=deck["name"],
            shareLink=shareLink,
            desc=self._desc(deck),
            table=self._table(),
            tags=self._tags()
        )
        gui_hooks.overview_will_render_content(self, content)
        self.web.stdHtml(
            self._body % content.__dict__,
            css=["overview.css"],
            js=["jquery.js", "overview.js"],
            context=self,
        )


# reference to what is created by default Deck viewer
# <tr class="top-level-drag-row ui-droppable"><td colspan="6">&nbsp;</td></tr>
# <tr class="deck ui-draggable ui-draggable-handle ui-droppable" id="1588104695327">
# <td class="decktd" colspan="5"><span class="collapse"></span><a class="deck " href="#" onclick="return pycmd('open:1588104695327')">Core 10k Sentences</a></td>
# <td align="right"><span class="zero-count">0</span></td>
# <td align="right"><span class="new-count">1000+</span></td>
# <td align="center" class="opts"><a onclick="return pycmd(&quot;opts:1588104695327&quot;);"><img src="/_anki/imgs/gears.svg" class="gears"></a></td>
# </tr>
# <tr class="deck ui-draggable ui-draggable-handle ui-droppable" id="1589635862390">

#         <td class="decktd" colspan="5"><span class="collapse"></span><a class="deck filtered" href="#" onclick="return pycmd('open:1589635862390')">Drill 1 changed</a></td><td align="right"><span class="review-count">230</span></td><td align="right"><span class="zero-count">0</span></td><td align="center" class="opts"><a onclick="return pycmd(&quot;opts:1589635862390&quot;);"><img src="/_anki/imgs/gears.svg" class="gears"></a></td></tr><tr class="deck current ui-draggable ui-draggable-handle ui-droppable" id="1589118906975">

#         <td class="decktd" colspan="5"><span class="collapse"></span><a class="deck " href="#" onclick="return pycmd('open:1589118906975')">Grammar</a></td><td align="right"><span class="zero-count">0</span></td><td align="right"><span class="zero-count">0</span></td><td align="center" class="opts"><a onclick="return pycmd(&quot;opts:1589118906975&quot;);"><img src="/_anki/imgs/gears.svg" class="gears"></a></td></tr><tr class="deck ui-draggable ui-draggable-handle ui-droppable" id="1585075338304">

#         <td class="decktd" colspan="5"><span class="collapse"></span><a class="deck " href="#" onclick="return pycmd('open:1585075338304')">Spanish Essential Top 5000</a></td><td align="right"><span class="review-count">1000+</span></td><td align="right"><span class="new-count">1000+</span></td><td align="center" class="opts"><a onclick="return pycmd(&quot;opts:1585075338304&quot;);"><img src="/_anki/imgs/gears.svg" class="gears"></a></td></tr><tr class="deck ui-draggable ui-draggable-handle ui-droppable" id="1588127450627">

#         <td class="decktd" colspan="5"><span class="collapse"></span><a class="deck " href="#" onclick="return pycmd('open:1588127450627')">Takoboto</a></td><td align="right"><span class="review-count">28</span></td><td align="right"><span class="new-count">17</span></td><td align="center" class="opts"><a onclick="return pycmd(&quot;opts:1588127450627&quot;);"><img src="/_anki/imgs/gears.svg" class="gears"></a></td></tr><tr class="deck ui-draggable ui-draggable-handle ui-droppable" id="1588017320375">

#         <td class="decktd" colspan="5"><span class="collapse"></span><a class="deck " href="#" onclick="return pycmd('open:1588017320375')">日本語　KanjiDamage</a></td><td align="right"><span class="zero-count">0</span></td><td align="right"><span class="zero-count">0</span></td><td align="center" class="opts"><a onclick="return pycmd(&quot;opts:1588017320375&quot;);"><img src="/_anki/imgs/gears.svg" class="gears"></a></td></tr><tr class="deck ui-draggable ui-draggable-handle ui-droppable" id="1588970810769">

#         <td class="decktd" colspan="5"><span class="collapse"></span><a class="deck " href="#" onclick="return pycmd('open:1588970810769')">日本語だけ</a></td><td align="right"><span class="review-count">1</span></td><td align="right"><span class="zero-count">0</span></td><td align="center" class="opts"><a onclick="return pycmd(&quot;opts:1588970810769&quot;);"><img src="/_anki/imgs/gears.svg" class="gears"></a></td></tr><tr class="top-level-drag-row ui-droppable"><td colspan="6">&nbsp;</td></tr>


    def _tags(self):
        htmlTableHeader = """
<table cellspacing="0" cellpading="3" style="margin-top:20px;margin-bottom:20px">
    <tbody>
        <tr>
            <th align="right"></th>
            <th align="left">Tag</th>
            <th align="center">Last Review</th>
            <th class="count" align="center">Reps<br>Today</th>
            <th class="count" align="center">Reps<br>Total</th>
            <th class="count" align="left"></th>
        </tr>
        """
        tags = self.mw.drill.getTags(self.mw.col)
        htmlRows = ""
        for tag in tags:
            last = self.mw.drill.tagLast(tag) # timestamp of last review
            htmlTag = tag
            indicatorStyle = ""
            indicatorLeft = ""
            indicatorRight = ""
            reps = self.mw.drill.tagReps(tag)
            repsToday = self.mw.drill.tagRepsToday(tag)
            if self.mw.drill.currentTag == tag:
                indicatorStyle = "style=\"background-color:#c9c9c9\""
                indicatorLeft = ">> "
                indicatorRight = " <<"
            htmlRow = """
        <tr %s>
            <td align="right">%s</td>
            <td style="padding-right:20px" class="decktd" align="left"><a class="deck" href=# onclick="return pycmd('study:%s')">%s</a></td>
            <td align="right">%s</td>
            <td align="right">%s</td>
            <td align="right">%s</td>
            <td align="left">%s</td>
        </tr>
            """ % (indicatorStyle, indicatorLeft, tag, htmlTag, last, repsToday, reps, indicatorRight)
            htmlRows += htmlRow
        htmlTableFooter = """
    </tbody>
</table>
        """
        return htmlTableHeader + htmlRows + htmlTableFooter


    def _desc(self, deck):
        if deck["dyn"]:
            desc = _(
                """\
This is a special deck for studying outside of the normal schedule."""
            )
            desc = _("Select a tag to study all cards with that tag in a fixed order. Repeat this exercise as much as desired. Cards will not be scheduled.")
        else:
            desc = deck.get("desc", "")
        if not desc:
            return "<p>"
        if deck["dyn"]:
            dyn = "dyn"
        else:
            dyn = ""
        return '<div class="descfont descmid description %s">%s</div>' % (dyn, desc)

    def _table(self):
        counts = list(self.mw.col.sched.counts())
        finished = not sum(counts)
        if self.mw.col.schedVer() == 1:
            for n in range(len(counts)):
                if counts[n] >= 1000:
                    counts[n] = "1000+"
        but = self.mw.button
        if finished:
            return '<div style="white-space: pre-wrap;">%s</div>' % (
                self.mw.col.sched.finishedMsg()
            )
        else:
            return """
<table width=400 cellpadding=5>
<tr><td align=center>
%s %s</td></tr></table>""" % (
                but("study", _("Study Current"), id="study", extra=" autofocus"),
                but("next", _("Study Next"), key = 'N', id="next"),
            )

    _body = """
<center>
<h3>%(deck)s</h3>
%(shareLink)s
%(desc)s
%(table)s
%(tags)s
</center>
"""

    # Bottom area
    ######################################################################

    def _renderBottom(self):
        links = [
            ["O", "opts", _("Options")],
        ]
        if self.mw.col.decks.current()["dyn"]:
            links.append(["R", "refresh", _("Rebuild")])
            links.append(["E", "empty", _("Empty")])
        else:
            links.append(["C", "studymore", _("Custom Study")])
            # links.append(["F", "cram", _("Filter/Cram")])
        if self.mw.col.sched.haveBuried():
            links.append(["U", "unbury", _("Unbury")])
        buf = ""
        for b in links:
            if b[0]:
                b[0] = _("Shortcut key: %s") % shortcut(b[0])
            buf += """
<button title="%s" onclick='pycmd("%s")'>%s</button>""" % tuple(
                b
            )
        self.bottom.draw(
            buf=buf, link_handler=self._linkHandler, web_context=DrillOverviewBottomBar(self)
        )

    # Studying more
    ######################################################################

    def onStudyMore(self):
        import aqt.customstudy

        aqt.customstudy.CustomStudy(self.mw)
