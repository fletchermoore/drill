# drill
Anki 2.1 Addon to make doing traditional flashcards or grammar drills easier.

Current state is early, in progress, and not functional.

TODO:
- create a separate review state to review by tag
- incorporate Undo. this is normally managed by mw def onUndo
- ensure mw._debugCard doesn't do something odd
- Figure out what reviewCleanup does and make sure there aren't any conflicts

BUGS:
- Editing a card from drill reviewer will cause state to switch to regular reviewer on close
- no penalty or boosting addon. if drillreviewer is opened before regular reviewer, this addon will error