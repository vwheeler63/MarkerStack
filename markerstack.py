"""
Marker Stack Subsystem
**********************

Documentation Contents:

- Usage
- Marker Stack Object

See README.rst for more details.

Code Contents:

- Private configuration variables
- Events (Package initialization/configuration)
- MarkerStackPushCommand
- MarkerStackPopCommand



Usage
*****

The following applies to every View on every platform:

- F5 (or your custom Key Binding) to PUSH a Marker (cursor- and viewport positions).

- Shift+F5 (or your custom Key Binding) to POP a Marker (and return to cursor- and
  viewport positions).



Design
******


PUSH
====

1.  View Settings object is retrieved.
2.  Marker Stack object is attempted to be retrieved from
    View Settings with key ``_stack_key``.  If it is ``None``,
    an empty list (the stack) is created.
3.  Caret position and Viewport position are captured.
4.  The index of where the new Marker will go is remembered in
    ``marker_idx``.
5.  A new Marker is created and pushed (appended) onto the stack.
6.  The modified stack (list) is saved to the View Settings with
    ``_stack_key``.
7.  An icon for the new Marker is added to the left gutter by:
    - formulating a unique key from the Marker just PUSH-ed
      (``_rgn_key_prefix`` + ``marker_idx``),
    - a new Region is created from the saved Caret position,
    - ``vw.add_regions(new_rgn_key, [rgn], _icon_color, _icon_path, _rflags)``

Originally it was tried to save all the left-gutter icons in a single region list
with a single key, but it turned out that Sublime Text manages these independently
and can and does merge them when they occupy the same location.  This made the
region (icon) list go out of sync with the stack.  So the new method of positively
linking a Marker with a Region icon using a unique key was adopted.

.. code-block:: text

                            View Settings[_stack_key]
    Left Gutter             Marker Stack (list)
    ----------------        ---------------------------
    RgnIcon[rgn_key] <----> rgn_key = Marker[_icon_key]
    RgnIcon[rgn_key] <----> rgn_key = Marker[_icon_key]
    RgnIcon[rgn_key] <----> rgn_key = Marker[_icon_key]

.. note::

    The Marker is a dictionary where its creation is encapsulated in a class.
    This was necessary (instead of a custom object with fields) because Sublime Text
    creates its own "mapping" internally and only copies the items in the passed
    dictionary object.  So if the value object is not a Python dictionary or list
    or other basic Python value, it doesn't know what to do with it and complains
    with an error message:  "TypeError: Value required" and the item is not saved
    in the View Settings.


POP
===

**Important:**  while editing of the Buffer occurs, the region icons represent
"anchors" within the Buffer text, and so they stay current.  On the other hand, the
Markers are stored in the stack with a mere "copy" of the Point values(locations in
text) when the Marker was created.  And so this goes out of date. Because of this,
the point in the Marker is updated before being used from the corresponding region
icon which returns the current point in

1.  View Settings object is retrieved.
2.  Marker Stack object is attempted to be retrieved from View Settings with
    key ``_stack_key``.  If it is ``None``, then the stack is empty and there
    is nothing to do.  If it is not ``None``, then this sequence is continued.
3.  The top Marker is popped off the Marker Stack.
    If stack is now empty, then the key is erased from the View Settings,
    otherwise the remaining stack is saved back to View Settings.
4.  The region (icon) is fetched from the left gutter (contains current
    position where we want to place the caret).  It is retrieved using the
    unique key stored inside the popped Marker object.
5.  That set of 1 region (with that unique key) is removed from the
    View's region dictionary, causing that icon to be removed.
6.  The saved Viewport position is retrieved from the Marker and
    restored in the View.
7.  Move cursor to previously-stored position.  This is done by:
    - All current "Selections" (i.e. carets) are removed from the View, and
    - replaced with one new region created from the retrieved caret Point.



Design Thoughts on Scroll State
*******************************

Restoring "scroll state" along with restoring a previous cursor position is "sort of"
what we want.  However, Sublime Text's "scroll state" is called Viewport Position,
which is not quite what we want.

What we DO want is that when the position of the cursor is saved, it is a certain
percentage of the way down the screen.  And that percentage would need to hold, no
matter if the number of lines of visible text in the window changed before the
positions were "popped".  If the percent is 30% of the way down the screen when
there are 116 lines of visible text, and then the window size gets changed so there
are now only 50 lines of text showing, when the position is popped, the viewport
is scrolled so that the cursor is still 30% of the way down the screen --- if that
is doable....

It is possible Viewport Position would be fine as a start, but there appears to be a
group of View-object position queries with the names "viewport", "window", "layout"
and "text" relating to position and DIP\ [1]_ coordinates may be applicable to this
problem, and they are found right underneath these 2 functions in the
``python38/sublime.py`` file which leads me to believe that they are related.

    viewport_position(self) -> Vector:
        # :returns: The offset of the viewport in layout coordinates.

    set_viewport_position(self, xy: Vector, animate=True):
        # Scrolls the viewport to the given layout position.

As of 29-May-2025, so far, we have been experimenting with just using the above
functions and so far they have been sufficient to the needs of the testers.

.. [1]  DIP stands for "device-independent pixel".  It is a unit of length, typically
        applied to describing a location on a computer monitor, and is defined more
        thoroughly at:  https://en.wikipedia.org/wiki/Device-independent_pixel

        Sublime Text uses a data type called a `DIP`, which is a type definition from
        `sublime_types.py` and is shown below.  Note also that type `Vector`
        is an (X,Y) coordinate pair that uses type `DIP`:

        DIP: TypeAlias = 'float'
        Vector: TypeAlias = 'Tuple[DIP, DIP]'

        The 2 functions named above return, and accept, `Vector` types respectively.



How Marker Stack Saves State Across Sessions:  View Settings
************************************************************

Persistence across sessions is achieved by storing the list of markers (Marker Stack)
with the View settings.  Unfortunately, it doesn't take custom objects (e.g. a list
of MarkerStackMarker objects), but it does take Python objects (e.g. lists,
dictionaries, lists of dictionaries, etc.).

Fortunately and unfortunately, it's not a simple dictionary that retains its state
or *actually* gives a reference to objects inside it.

:Reading:   To get things from it, you have to make a call (get()) and what you get is
            not a reference, but a COPY, so updating it doesn't do anything to the
            actual settings.

:Writing:   To update anything in it, you have to make a call (set()), and what you
            pass to it is COPIED to the internal data.  So you STILL don't have a
            reference to it.

The gutter icons are also set with the sublime.RegionFlags.PERSISTENT flag so that
they too are saved across sessions.  Together, these two lists form a "unit" tied
together in this Marker Stack subsystem.



Marker Stack Object
*******************

The Marker Stack proper is kept in the View settings, but only when needed.  It is
deleted when not needed, so that this Package does not force every View to have one.

Its structure is a list of Marker dictionary objects.  A Marker object has this
structure:

.. code-block:: json

    {
        "id":  icon_key,     // String containing unique key to gutter icon (Region).
                             // That gutter icon also contains the current Point
                             // location within the text that the Marker represents.
        "vp":  (DIP, DIP)    // Sublime Text `Vector` value
                             // used with `viewport_position()` and
                             // `set_viewport_position()`.
    }

"""
import sublime
import sublime_plugin
import os
import functools


# =========================================================================
# Configuration Values
# =========================================================================

# General
_pkg_name       = 'MarkerStack'
_animate_scroll = False


# Regions (Gutter Icons)
_rgn_key_prefix = '_marker_stack_icon_'
_icon_path      = 'Packages/MarkerStack/marker_gutter_icon.png'
_icon_color     = 'region.purplish'
_rflags         = (
                        sublime.RegionFlags.PERSISTENT  # Save across sessions
                      | sublime.RegionFlags.HIDDEN      # Don't show selection, just the icon.
                  )

# Marker
_stack_key      = '_marker_stack'
_vp_pos_key     = 'vp'
_icon_key       = 'id'
_debugging      = 0          # Levels: 0, 1, 2, 3...


# =========================================================================
# Events
# =========================================================================


def ms_setting(key):
    """
    Get a MarkerStack setting from a cached settings object.
    """
    default = ms_setting.default.get(key, None)
    return ms_setting.obj.get(key, default)


def init():
    """
    Initialize plugin.
    """
    global _pkg_name
    global _icon_path
    global _icon_color

    # Set up default and overridable Package settings.
    # `ms_setting()` cannot be called until this is done.
    ms_setting.obj = sublime.load_settings("MarkerStack.sublime-settings")

    ms_setting.default = {
        "ms_icon_path": _icon_path,
        "ms_icon_color": _icon_color,
        "ms_animate_scrolling": False,
    }

    # Now we can fetch user-configurable values.
    _icon_path = ms_setting('ms_icon_path')
    _icon_color = ms_setting('ms_icon_color')
    _animate_scroll = ms_setting('ms_animate_scrolling')

    if _debugging:
        print(f'{_pkg_name} loaded.')
        print(f'  Configured _icon_path      = [{_icon_path}]')
        print(f'  Configured _icon_color     = [{_icon_color}]')
        print(f'  Configured _animate_scroll = [{_animate_scroll}]')


def plugin_loaded():
    init()


# =========================================================================
# Commands and Related Classes
# =========================================================================


class MarkerStackMarker(dict):
    """ -------------------------------------------------------------------
    Interestingly, the reason this class inherits from ``dict`` is because
    when we attempt to save a regular Python object (with fields) into the
    View settings, even when it is a value inside a dictionary, ST
    complains with the error "TypeError: Value required".  But it does
    take a dictionary as a value inside another dictionary, and it also
    takes as a value, a list of dictionaries.

    So the purpose of this class is simply to encapsulate the proper
    formatting of this type of dictionary object so that its code
    does not need to live in multiple places.

    :param vp:        Vector object returned from View.viewport_position()
    :param icon_key:  Unique key for icon.  Normally it is
                      f'{_rgn_key_prefix}{marker_idx}', thus looking
                      like this:  '_marker_stack_icon_N' where 'N' is
                      the marker's index.
    ------------------------------------------------------------------- """
    def __init__(self, vp: (float, float), icon_key: str):
        global _vp_pos_key
        global _icon_key
        self[_vp_pos_key] = vp
        self[_icon_key]   = icon_key

    def __repr__(self):
        return f'Marker[{self[_vp_pos_key]}, {self[_icon_key]}]'


class MarkerStackPushCommand(sublime_plugin.TextCommand):
    def run(self, edit, testing=False):
        """
        A Marker PUSH is legal regardless of whether any text is selected.  The
        position of the caret (i.e. region.b) is used to get the Point to be saved.
        The current viewport position is saved with it.  Because the Point saved can
        move around as further editing occurs, it is saved ONLY with the Marker ICON
        in the left gutter, and not saved elsewhere since the value would not be
        valid after an unknown amount of editing on the document, whereas the gutter
        ICON moves with the edited text, and so retains a current value.  The Marker
        in the Marker Stack is connected with that gutter icon by way of a unique key
        with which the icon was stored.

        To preserve the integrity of saving the Marker Stack across sessions, the
        "master copy" of the stack is kept in the View's settings, and not kept
        in this module.  So these 2 things (in Sublime Text's domain) are updated
        each time the Marker Stack changes:

        - View's settings are stored and retrieved with key `_stack_key`.
        """
        global _rgn_key_prefix
        global _icon_path
        global _icon_color
        global _rflags
        global _stack_key
        global _debugging

        # 1.  View Settings object is retrieved.
        vw = self.view
        vw_settings = vw.settings()

        # 2.  Marker Stack object is attempted to be retrieved from
        #     View Settings with key ``_stack_key``.  If it is ``None``,
        #     an empty list (the stack) is created.
        mstack = vw_settings.get(_stack_key)

        if mstack is None:
            mstack = []

        # 3.  Caret position and Viewport position are captured.
        pt = vw.sel()[0].b
        vppos = vw.viewport_position()

        # 4.  The index of where the new Marker will go is remembered in
        #     ``marker_idx``.
        marker_idx = len(mstack)

        # 5.  A new Marker is created and pushed (appended) onto the stack.
        icon_key = f'{_rgn_key_prefix}{marker_idx}'
        marker = MarkerStackMarker(vppos, icon_key)
        mstack.append(marker)

        # 6.  The modified stack (list) is saved to the View Settings with
        #     ``_stack_key``.
        vw_settings.set(_stack_key, mstack)

        # 7.  An icon for the new Marker is added to the left gutter by:
        #     - formulating a unique key from the Marker just PUSH-ed
        #       (``_rgn_key_prefix`` + ``marker_idx``),
        #     - a new Region is created from the saved Caret position,
        #     - ``vw.add_regions(icon_key, [rgn], _icon_color, _icon_path, _rflags)``
        rgn = sublime.Region(pt)
        vw.add_regions(icon_key, [rgn], _icon_color, _icon_path, _rflags)

        if _debugging:
            print(f'Pushed marker: {marker}')
            print(f'Stack        : {mstack}')
            print(f'rgn          : {rgn}')


class MarkerStackPopCommand(sublime_plugin.TextCommand):
    def run(self, edit, testing=False):
        """
        Pop Marker off stack, restoring that cursor- and viewport positions.
        """
        global _rgn_key_prefix
        global _stack_key
        global _vp_pos_key
        global _icon_key
        global _debugging

        # 1.  View Settings object is retrieved.
        vw = self.view
        vw_settings = vw.settings()

        # 2.  Marker Stack object is attempted to be retrieved from View Settings with
        #     key ``_stack_key``.  If it is ``None``, then the stack is empty and there
        #     is nothing to do.  If it is not ``None``, then this sequence is continued.
        mstack = vw_settings.get(_stack_key)

        if mstack is None:
            if _debugging:
                print("Marker Stack empty.")

            # Erase key from regions if not already done.
            vw.erase_regions(_rgn_key_prefix)
        else:
            # 3.  The top Marker is popped off the Marker Stack.
            #     If stack is now empty, then the key is erased from the View Settings,
            #     otherwise the remaining stack is saved back to View Settings.
            marker = mstack.pop()

            if _debugging:
                print(f'Popped marker: {marker}')

            if len(mstack) == 0:
                vw_settings.erase(_stack_key)
            else:
                vw_settings.set(_stack_key, mstack)

            # 4.  The region (icon) is fetched from the left gutter (contains current
            #     position where we want to place the caret).  It is retrieved using the
            #     unique key stored inside the popped Marker object.
            icon_key = marker[_icon_key]
            rgns = vw.get_regions(icon_key)

            # 5.  That set of 1 region (with that unique key) is removed from the
            #     View's region dictionary, causing that icon to be removed.
            vw.erase_regions(icon_key)

            # 6.  The saved Viewport position is retrieved from the Marker and
            #     restored in the View.
            vppos = marker[_vp_pos_key]
            vw.set_viewport_position(vppos, animate=_animate_scroll)

            # 7.  Move cursor to previously-stored position.  This is done by:
            #     - All current "Selections" (i.e. carets) are removed from the View, and
            #     - replaced with one new region created from the retrieved caret Point.
            # For safety....
            if len(rgns) > 0:
                rgn = rgns[0]
                sel_list = vw.sel()
                sel_list.clear()
                sel_list.add(rgn)

                if _debugging:
                    print(f'Popped region: {rgn}')

