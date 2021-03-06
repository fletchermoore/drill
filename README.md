# Drill
Anki 2.1 Addon to make doing traditional flashcards or grammar drills easier.


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



## ToDo

### Features

- Order tags: last seen or alpha
- Show position within tag while reviewing
- Create own timebox

### Tedious stuff prior to release


- Change drillconf and drillreviewer to inherited classes
- incorporate Undo. this is normally managed by mw def onUndo
- ensure mw._debugCard doesn't do something odd
- Figure out what reviewCleanup does 
- remove label above "Next Card" button
- figure out what a good limit to number of cards allowed for drilling / managing large lists
- remove ordering option from deck conf or code in option
- add decent documentation
- on getCard, do we want to log and startTimer?
- remove "Drill Reviewer" text from above buttons
- remove shortcut that lets user activate Again
- does Bury make sense or should it be removed? remove probably
- figure out what lastCard in reviewer does. it's tracking answered card ids.
- using .current() vs .active() to retrieve deck. risky?
- move table styling to css file?
- make sure styling works with night view
- play nice with localization


## Bugs

- Lost drill meta somehow at least once.

