# drill
Anki 2.1 Addon to make doing traditional flashcards or grammar drills easier.

Very early code and not functional yet.


TODO:
- incorporate Undo. this is normally managed by mw def onUndo
- ensure mw._debugCard doesn't do something odd
- Figure out what reviewCleanup does 
- stop monkey patching reviewState change and use existing hook
- remove label above "Next Card" button
- cycle
- figure out what a good limit to number of cards allowed for drilling / managing large lists
- remove ordering option from deck conf or code in option
- add decent documentation
- on getCard, do we want to log and startTimer?
- remove "Drill Reviewer" text from above buttons
- remove shortcut that lets user activate Again
- does Bury make sense or should it be removed? remove probably
- figure out what lastCard in reviewer does. it's tracking answered card ids.


BUGS:
- fin