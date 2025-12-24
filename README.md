# Sublime Text MarkerStack Package

Push a "marker" (position in the text) onto a "Marker Stack" (with a single keystroke)
with the ability to come back to that point later by popping it off the marker stack
(with a single keystroke).  A symbol appears in the left gutter showing what line it
is on.  The marker moves with the text when text is inserted or deleted before it.
Unlimited stack size; saves state between sessions.



## Usage

The following applies to every View on every platform:

- F5 (or your custom Key Binding) to PUSH a Marker (cursor- and viewport positions).

- Shift+F5 (or your custom Key Binding) to POP a Marker (and return to cursor- and
  viewport positions).



## The Problem MarkerStack Solves

Using Sublime Text Bookmarks is a handy way to navigate repeatedly to different
places in a file you are working on, but it leaves a gap of functionality that
writers, editors and coders sometimes need.  To illustrate, let's say you are typing
in one paragraph (or block of code) and your train of thought (or a phone call) makes
you realize that there is something else in the file that needs to be updated, and
you want to go do that quickly before you forget, and then come back to continue what
you were doing before.  You can sort of "manage" that with Bookmarks, but Bookmarks
were not really designed for that:  Bookmarks keep 1 or more places in a file that
are relevant to the task you are doing NOW so you can pop back and forth as needed.
This is common.

Say you have 4 Bookmarks in a document, but NOW realize you need to go edit something
ELSE (different task) and then come back to what you were doing.  Do you clutter up
your 4 Bookmarks by making a 5th, and then go do your edit, and then

- Goto Next Bookmark
- Goto Next Bookmark
- Goto Next Bookmark
- Goto Next Bookmark

until you get back to the place you were before?

Or would you rather simply (in a separate context or namespace), "remember" where
you were in a document, go do your edit, and then come back to where you were in
one keystroke?

And maybe in the middle of THAT edit, you realize something ELSE you need to change
elsewhere in the document, and you want to do THAT before you forget it.

The solution?  MarkerStack.

MarkerStack gives you the ability to save "where you are" to go somewhere else in
the document temporarily and then come back to where you were again.  And there is
no limit as to how deeply nested your "tasks" get.  One keystroke, and you're back
to your previous Marker, without having to think about (or remember) what it was you
were doing when you broke away to do something else.

(The below description uses MarkerStack's default Key Bindings.  You can, of course,
change these to your liking.)

[F5] to push current caret position and viewport position onto a Marker Stack, which
additionally places a MarkerStack icon in one of the gutters on the left.

You can then move your cursor elsewhere and later use [Shift+F5] to to back to the
location and scroll state of an unlimited-size Marker Stack.  Once the Marker
is "popped", the matching icon in the gutter goes away.  Of course, if you
[Shift+F5] when the Marker Stack is empty, nothing happens.

Each View has its own Marker Stack, as it applies to a "stack-like task" within only
that one document.  This is by design.

The Marker Stack is "remembered" until the document is closed, including across
Sublime Text sessions.

For additional details, see module header comment in `markerstack.py`.



## MarkerStack Gutter Symbol

The `marker_gutter_icon.png` symbol was chosen over a "bookmark" symbol so as to be
explicitly clear in the gutter that the saved position IS NOT a bookmark, which has
different (persistent) behavior.  This symbol is intentionally suggestive of a stack,
and different from any other symbols that appear in the editing area's left gutter.
