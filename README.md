# Drill
Anki 2.1 Addon to make doing traditional flashcards or grammar drills easier.

Work in progress. Major bugs still exist. Not completely functional at the momemnt.


## Basics

This addon adds "Drill" to the Tools menu. This option creates a Filtered deck, very similar to other filtered decks, except cards reviewed with Drill are not scheduled.
Cards are sorted into sets by tags.
From the overview page, you select a tag to study. This launches the reviewer, and you merely go through all the cards with that tag once and
then return to the overview page.
You can then choose another tag, and so on.

You can mostly do this with Filtered decks currently without the addon, but you have to keep updating the filter search criteria and rebuilding
the deck.

## Motivation

Inspired by the method presented to me here (https://www.wasabi-jpn.com/japanese-lessons/japanese-grammar-with-instantaneous-composition-method/), I felt that grammar patterns are best learned
through painful reptitive drilling. 

Anki has an incredible card browser and SRS system, but Anki is not designed for traditional flashcard studying, so it lacks features to make it convenient. My goal is to add them.



## TODO

### Features

- Order tags: last seen or alpha
- Timebox entire study session, even if changing tags
- Show position within tag while reviewing

### Tedious stuff prior to release

- incorporate Undo. this is normally managed by mw def onUndo
- ensure mw._debugCard doesn't do something odd
- Figure out what reviewCleanup does 
- stop monkey patching reviewState change and use existing hook
- remove label above "Next Card" button
- figure out what a good limit to number of cards allowed for drilling / managing large lists
- remove ordering option from deck conf or code in option
- add decent documentation
- on getCard, do we want to log and startTimer?
- remove "Drill Reviewer" text from above buttons
- remove shortcut that lets user activate Again
- does Bury make sense or should it be removed? remove probably
- figure out what lastCard in reviewer does. it's tracking answered card ids.
- ensure behaves properly when tags are added and removed from cards via editor/browser
- using .current() vs .active() to retrieve deck. risky?
- move table styling to css file?
- make sure styling works with night view
- play nice with localization

## Bugs

- On drill overview, when webview refreshes it reverts to normal overview somehow
- empty deck should clear drill cache
- Is possible to not load cards correctly. can trigger with sync
- Rebuilding deck does not actually load cards

