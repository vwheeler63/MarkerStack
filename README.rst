***********
MarkerStack
***********

MarkerStack is a package for Sublime Text that enables you to efficiently manage
temporary moves away from your current editing position in Sublime Text 3 and
onward by:

- pushing a "Marker" (position in text) onto a "Marker Stack", with

- the ability to come back to that point later by popping it off the Marker Stack.

When a Marker is pushed, a symbol appears in the left gutter showing what line it is
on.  The gutter icon changes to a "multiple Marker" icon when there is more than one
Marker on the same line.  The marker moves with the text when text is inserted or
deleted before it.  MarkerStack state is "remembered" until the View is closed,
or until all Markers are popped off the stack, whichever comes first.


The Problem MarkerStack Handles
===============================

There are many kinds of editing interruptions that happen regularly for most people
using a text editor.  Examples:

- go elsewhere in a file to copy a line of text (e.g. source code) onto the
  clipboard, so that it can be pasted where you are editing;
- handle something elsewhere in the file before you forget it;
- you get interrupted and need to move your cursor away from where you are
  editing in order to handle the need brought by the interruption.

With MarkerStack, you can PUSH your cursor (caret) position in a Sublime Text View
with one keystroke, go do something elsewhere in the same file, and then POP your
cursor position with another keystroke, to instantly be back where you left off,
without having to remember where it is.

Marker Stack data is saved across Sublime Text sessions, for those occasions when
handling an interruption might span across Sublime Text sessions.

It is designed for efficiently managing temporary moves away from your current
editing position in the text.

For additional details, see the module header comment in ``markerstack.py``.


Why MarkerStack is Better than Bookmarks for Interruptions
==========================================================

Using Sublime Text Bookmarks is a handy way to navigate repeatedly to different
places in a file you are working on, but it leaves a gap of functionality that
writers, editors and coders sometimes need for *temporary* moves away from the
part of the file being viewed or edited.

Using MarkerStack is significantly more efficient than setting a Bookmark for
interruptions such as the above, and doesn't leave you with the task of

- cleaning up unused bookmarks, or
- remembering where you were previously in the file.

To illustrate, let's say you are typing in one paragraph (or block of code) and your
train of thought (or a phone call) makes you realize that there is something else in
the file that needs to be updated, and you want to do that quickly before you forget,
and then come back to continue what you were doing before.  You can sort of "manage"
that with Bookmarks, but Bookmarks were not designed to handle that scenario
efficiently.  MarkerStack is.


Getting Started
***************

MarkerStack was originally intended to be pre-mapped to a pair of keystrokes

- [F5] and
- [Shift+F5]

but because the good instructions for publishing a Sublime Text Package strongly
advise against any pre-defined key mappings, MarkerStack comes with a
``Default.sublime-keymap`` with a default key mapping that is commented out.  To use
MarkerStack via the keyboard (easier than using it through the Command Palette),
you'll need to map a pair of keys to its PUSH and POP Commands.

The easiest way to set your key bindings is through the menu:

    Preferences > Package Settings > MarkerStack > Key Bindings

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

Of course, you can select your own key bindings based on what feels most natural to you.


Usage
*****

The following applies to every View on every platform:

- [PUSH Key Binding] to PUSH a Marker (cursor and viewport positions).

- [POP Key Binding] to POP a Marker (return to previous cursor and viewport positions).


Menu Items
**********

The following menu items are installed with MarkerStack:

Preferences > Package Settings > MarkerStack >

- README:        opens this file
- Settings:      opens a split-view of MarkerStack settings
- Key Bindings:  opens a split-view MarkerStack key bindings


Commands
********

+-----------------------------+-------------------------------------------------------------+
| Command                     | Description                                                 |
+=============================+=============================================================+
| MarkerStack: Push Marker    | Push current caret + viewport position onto stack           |
+-----------------------------+-------------------------------------------------------------+
| MarkerStack: Pop Marker     | Pop caret + viewport position off stack                     |
+-----------------------------+-------------------------------------------------------------+
| MarkerStack: Dump           | Dump MarkerStack data for current View, into Console output |
+-----------------------------+-------------------------------------------------------------+
| MarkerStack: Open Readme    | Open README (this file)                                     |
+-----------------------------+-------------------------------------------------------------+
| MarkerStack: Settings       | Split-view of MarkerStack settings                          |
+-----------------------------+-------------------------------------------------------------+
| MarkerStack: Key Bindings   | Split-view of MarkerStack key bindings                      |
+-----------------------------+-------------------------------------------------------------+


Storage
*******

Each View only stores MarkerStack information until the stack becomes empty, and then
that storage is removed again.  In other words, Views with no PUSHed cursor (caret)
positions are not burdened with any kind of storage, including across Sublime Text
sessions.
