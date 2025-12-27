********************************
Sublime Text MarkerStack Package
********************************

Push a "marker" (position in text) onto a "Marker Stack" (with one keystroke) with the
ability to come back to that point later by popping it off the Marker Stack (with
another keystroke).  A symbol appears in the left gutter showing what line it is on.
The marker moves with the text when text is inserted or deleted before it.  Stack size
is virtually unlimited; saves state between sessions.


Introduction
************

MarkerStack gives you the ability to save "where you are" with one keystroke to go
somewhere else in the document temporarily, and then with another keystroke, come
back to where you were again, without having to think about (or remember) what it was
you were doing before, or where it was, when you broke away to do something else.
A"marker" appears in the left gutter to show the position you saved, which is removed
again once that position is removed from the stack.  There is no practical limit as
to how deeply nested your "tasks" get.

Each View has its own Marker Stack, as it applies to a "stack-like task" within only
that one document.  This is by design.

The Marker Stack is "remembered" until the document is closed, including across
Sublime Text sessions.

For additional details, see module header comment in ``markerstack.py``.

Why MarkerStack is Better than Bookmarks for Interruptions
==========================================================

Using Sublime Text Bookmarks is a handy way to navigate repeatedly to different
places in a file you are working on, but it leaves a gap of functionality that
writers, editors and coders sometimes need.  To illustrate, let's say you are typing
in one paragraph (or block of code) and your train of thought (or a phone call) makes
you realize that there is something else in the file that needs to be updated, and
you want to do that quickly before you forget, and then come back to continue what you
were doing before.  You can sort of "manage" that with Bookmarks, but Bookmarks were
not designed to handle that scenario efficiently.  MarkerStack is.


Getting Started
***************

MarkerStack was originally intended to be pre-mapped to a pair of keystrokes

- [F5] and
- [Shift+F5]

but because the good instructions for publishing a Sublime Text Package strongly
advise against any pre-defined key mappings, MarkerStack comes with a
``Default.sublime-keymap`` with a default key mapping that is commented out.  To use
MarkerStack via the keyboard, you'll need to map a pair of keys to its PUSH and POP
Commands.

The easiest way to set your key bindings is through the menu:

    Preferences > Package Settings > Marker Stack > Key Bindings

You can copy/paste the commented out default key mappings into your
``User/Default.sublime-keymap``:

.. code-block:: json

    [
        // --------------------------------------------------------------------
        // Marker Stack Key Mapping
        // --------------------------------------------------------------------
        {
          "keys": ["f5"],
          "command": "marker_stack_push",
        },
        {
          "keys": ["shift+f5"],
          "command": "marker_stack_pop"
        },
    ]


Or if you wanted to map them to [F4] and [Shift+F4] respectively, you could do
something like this instead:

.. code-block:: json

    [
        // --------------------------------------------------------------------
        // Marker Stack Key Mapping -- Swap F4 and F5.
        // --------------------------------------------------------------------
        // First, move `next_result` and `prev_result` to [F5].
        { "keys": ["f5"], "command": "next_result" },
        { "keys": ["shift+f5"], "command": "prev_result" },
        {
          "keys": ["f4"],
          "command": "marker_stack_push",
        },
        {
          "keys": ["shift+f4"],
          "command": "marker_stack_pop"
        },
    ]

Of course, you can also select your own key bindings based on what feels most natural
to you.


Usage
*****

The following applies to every View on every platform:

- [PUSH Key Binding] to PUSH a Marker (cursor and viewport positions).

- [POP Key Binding] to POP a Marker (return to previous cursor and viewport positions).


Menu Items
**********

The following menu items are installed with MarkerStack:

Preferences > Package Settings > Marker Stack >

- README:        opens this file
- Settings:      opens a split-view of MarkerStack settings
- Key Bindings:  opens a split-view MarkerStack key bindings


Commands
********

- MarkerStack: Push Marker    Push current caret + viewport position onto stack
- MarkerStack: Pop Marker     Pop caret + viewport position off stack
- MarkerStack: Open Readme    Open README
- MarkerStack: Settings       Split-view of MarkerStack settings
- MarkerStack: Key Bindings   Split-view of MarkerStack key bindings


Storage
*******

Each View only stores MarkerStack information until the stack becomes empty, and then
that storage is removed again.  In other words, Views with no PUSHED cursor
(caret) positions are not burdened with any kind of storage, including across Sublime
Text sessions.


MarkerStack Gutter Symbol
*************************

The ``marker_gutter_icon.png`` symbol was chosen over a "bookmark" symbol so as to be
explicitly clear in the gutter that the saved position IS NOT a bookmark, which has
different (persistent) behavior.  This symbol is intentionally suggestive of a stack,
and different from any other symbols that appear in the editing area's left gutter.
