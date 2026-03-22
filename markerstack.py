"""
MarkerStack Subsystem
*********************

Documentation Contents:

- Usage
- Commands

    - PUSH
    - POP
    - DUMP

- Design

    - Requirements
    - Resources

- Design Flaw with Scroll State
- How MarkerStack Saves State Across Sessions:  View Settings
- MarkerStack Object

See README.rst for more details.

Code Contents:

- Configuration
- Settings Utilities
- Events (Package initialization/configuration)
- Commands and Related Classes

    - MarkerStackPushCommand
    - MarkerStackPopCommand
    - MarkerStackDumpCommand



Usage
*****

The following applies to every View on every platform:

- [F5] (or your Key Binding) to PUSH a Marker (caret- and viewport positions).

- [Shift+F5] (or your Key Binding) to POP a Marker (and return to caret- and
  viewport positions).



Design
******


Requirements
============

1.  It should behave like Multi-Edit Marker Stack, namely that Markers appeared
    in the gutter, pushed onto an internal stack, and then as the Markers were
    popped off the stack, the caret position and scroll state would return to
    where they were when the Marker was pushed, with unlimited stack depth, and
    no action (safe) when attempting to pop from an empty stack.

2.  Its state across all open Views needs to persist across Sublime Text sessions.

3.  When text was inserted and deleted ABOVE a Marker, the Marker needed to
    MOVE WITH the text, i.e. retain the same position in the text, even though
    the text moved.

4.  Views with no MarkerStack information must not be required to store
    anything across Sublime Text sessions.

5.  On the first pushed Marker on a line, the gutter icon should represent a
    SINGLE Marker.

6.  When the last marker on a line has been popped, the gutter icon goes away.

7.  When there are 2 or more Markers on the same line, the gutter icon should
    represent MULTIPLE Markers.

8.  When the number of Markers on the same line changes from 2 to 1 after
    a Marker has been popped, the gutter icon should
    revert to representing a SINGLE Marker again.

9.  Marker Icons should instantly update when settings for icons changes.


Resources
=========

This is unfortunately long, but it is important, because of a large amount
of undocumented (but consistent) behavior on Sublime Text's part.  The below
is the only place this author knows of that documents some of this behavior,
and it is worth preserving.  (Especially the "Limitations" listed below,
some of which had to be discovered empirically by tests.)

- A View's Settings object (a representation of which is returned with
  ``self.view.settings()``) stores its content across sessions.  A whole
  Python object (e.g. a dictionary containing your values) can be stored,
  retrieved and removed from within a TextCommand using a unique key like
  this:

  .. code-block:: py

      settings = self.view.settings()
      settings.set(key, my_obj)        # Store
      my_obj = settings.get(key)       # Retrieve
      settings.erase(key)              # Remove

  and whatever is stored is saved across Sublime Text sessions as long
  as the View remains open.

  It is also important to understand that ``my_obj`` retrieved by
  ``my_obj = settings.get(key)`` above is NOT the same object that was
  submitted, but is only a COPY, and thus modifying it does nothing to the
  actual settings inside the View.  Further, ``settings.set(key, my_obj)``
  ALSO does not store the object submitted, but instead makes a COPY of it
  and stores THAT.  So there is no way to get an actual reference to the
  objects stored inside a View's Settings object --- only copies.

  Limitation:

      Simply storing caret position and viewport position (scroll state)
      would not be adequate because when text is added or deleted above the
      marker, the integer stored and retrieved for caret position would
      become invalid, and there would be no way to understand how to adjust
      it, and it would be horribly complex (impractical) to keep it
      adjusted with every user keystroke.


- A View also is able to store a set of Regions referenced with a unique
  key, stored, retrieved and removed via:

  .. code-block:: py

      View.add_regions(key, [rgn], color, icon_path, flags))  # Store
      rgns = View.get_regions(key)                            # Retrieve
      View.erase_regions(key)                                 # Remove

  respectively.  And with the ``flags`` argument, one can cause:

  - only the icon submitted to be visible (actual Region would be hidden), and
  - it can be made to persist across Sublime Text sessions as long as the
    View remains open.

  These Regions DO move with the text when text is added and deleted above
  them.  When retrieved with the key, the set of Regions ONLY know about
  the set of Regions STORED, i.e. caret positions, and thus are NOT able to
  store anything else, such as viewport position (scroll state).

  Limitation #1:

      Whenever you retrieve a set of Regions, Sublime Text PRE-SORTS them to
      be in top-to-bottom order, even if that is not the order in which
      they were submitted!

      Furthermore, Sublime Text can and does merge the Regions when they
      occupy the same location!

      Because of this limitation, one call to ``View.add_regions()`` can
      only apply to ONE Marker, not more, even though the ``add_regions()``
      function accepts a list with unlimited number of Regions in it.

  Limitation #2:

      This one is really weird.  When a set of Regions (each with its own
      icon) are added to View Regions on the same line, Sublime Text
      displays the icon with the unique key with the lowest value (i.e. min
      ([key_list]) is the icon that will be displayed).

      Thus, if the Regions (with icons) are added in this order:

          icon_key ='_marker_stack_icon_16'
          icon_path='Packages/MarkerStack/marker_multiple.png'
          rgn      =Region(20552, 20552)
          icon_key ='_marker_stack_icon_15'
          icon_path='Packages/MarkerStack/marker_multiple.png'
          rgn      =Region(20551, 20551)
          icon_key ='_marker_stack_icon_14'
          icon_path='Packages/MarkerStack/marker_single.png'
          rgn      =Region(20550, 20550)

      the icon that will be displayed is:  ``marker_single.png``, whereas if they
      are added in this order:

          icon_key ='_marker_stack_icon_14'
          icon_path='Packages/MarkerStack/marker_multiple.png'
          rgn      =Region(21421, 21421)
          icon_key ='_marker_stack_icon_15'
          icon_path='Packages/MarkerStack/marker_multiple.png'
          rgn      =Region(21422, 21422)
          icon_key ='_marker_stack_icon_16'
          icon_path='Packages/MarkerStack/marker_single.png'
                      rgn      =Region(21423, 21423)

      even if the icon assignments are erroneous (i.e. #14 was the FIRST one
      at that line, but is being given icon ``marker_multiple.png``), the
      icon that will be displayed is:  ``marker_multiple.png``.

      Because of this limitation, PUSHING a new marker has to go through extra
      steps that assign 2 Regions (with icons) the wrong icon!  In other words,
      Sublime Text APPEARS to discard any icons on the same line when
      ``key > smallest_key_on_that_line``.  In other words, the ICONS appear
      to be managed separately, NOT actually attached to the Region added.
      So the concept that an icon "belongs with" a Region is NULL AND VOID,
      and this is undocumented behavior.

      The better solution on a PUSH operation is probably to:

      - remove all Regions (which removes whatever icon is in the gutter), then

      - add them back again, only this time using only the icon that should be
        displayed.  Or else including NO icon for all except the last one, which
        at least preserves the concept of "correctness" -- the only gutter icon
        added then "goes with" with the Region that was added.

      CONCLUSION:  gutter icons ARE NOT attached to the Region they are added with!
      They are attached to the LINE!

  Limitation #3:

      Because of the above behavior, (icons are not factually connected to
      Regions being added), POPPING a Region also needs to take extra steps
      to use the above knowledge to revert the gutter icon back to the one
      that represents a SINGLE Marker when the count of Markers on that
      line switches from 2 to 1.


- The two (View Settings and View Regions) cleverly used in combination,
  however, make it work:

      View Regions              View Settings
      -----------------------   ----------------------
      Stores a set of caret     Stores a list (stack)
      positions (Points) by      of custom objects by
      unique keys that move     key ('_marker_stack')
      with the text.

  Thus:

                     View Regions                            MarkerStack (in View Settings)
      ===========================================     =============================================
      Regions                  Point   Key            RegionsKey   Index   Viewport Position
      ----------------------   -----   ----------     ----------   -----   ------------------------
      [{a: 16332, b: 16332}]   16332   _ms_icon_0 <-- _ms_icon_0   0       view.viewport_position()
      [{a:  8710, b:  8710}]    8710   _ms_icon_1 <-- _ms_icon_1   1       view.viewport_position()
      [{a: 32998, b: 32998}]   32998   _ms_icon_2 <-- _ms_icon_2   2       view.viewport_position()
      [{a:   425, b:   425}]     425   _ms_icon_3 <-- _ms_icon_3   3       view.viewport_position()
      [{a:    16, b:    16}]      16   _ms_icon_4 <-- _ms_icon_4   4       view.viewport_position()
                                                      ---------------------------------------------
                                                                            ^
                                                                            |
                                                                        stack top

  Note that the gutter icon is NOT associated with the regions submitted in
  `view.add_regions()`, but rather is associated with the LINE of text in
  the View.  This "odd" behavior makes for a lot of "hoop jumping", but now
  that this is understood (through extensive testing), it can be navigated.

  Icon adjustments are done only when the number of Markers on one line changes

  - from 1 to 2, and
  - from 2 to 1.

  In all other cases, the call to `view.add_regions()` adds the appropriate
  SINGLE icon, or removes the icon displayed when the stack becomes empty.


And this is how MarkerStack:

- tracks a stack of caret locations,
- marks each one with a gutter icon,
- shows gutter icons appropriate to the number of Markers on each line, and
- persists state across sessions.



Commands
********

PUSH
====

Command Palette:  "MarkerStack: Push Marker"
Command        :  marker_stack_push

1.  Retrieve View Settings object.
2.  Attempt to retrieve MarkerStack object from View Settings with key
    ``_stack_key``.  If ``None``, create an empty list (the stack).
3.  Capture caret position and Viewport position.
4.  Remember index of where new Marker will go in ``marker_idx``.
5.  Note current line number and count number of Regions now on this
    same line before the new Marker is added.  This needs to be done
    while `mstack` and the View's Region dictionary are in sync.
6.  Create and push new Marker onto stack.
7.  Save modified stack (list) to View Settings with ``_stack_key``.
8.  Add Region to View's Region dictionary.
9.  If needed, adjust gutter icon displayed.   This needs to be done
    while `mstack` and the View's Region dictionary are in sync.

.. code-block:: text

                            View Settings[_stack_key]
    Left Gutter             MarkerStack (list)
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

Command Palette:  "MarkerStack: Pop Marker"
Command        :  marker_stack_pop

**Important:**  while editing of the Buffer occurs, the Region icons represent
"anchors" within the Buffer text, and so they stay current.  On the other hand, the
Markers are stored in the stack with a mere "copy" of the Point values(locations in
text) when the Marker was created.  And so this goes out of date. Because of this,
the point in the Marker is updated before being used from the corresponding Region
icon which returns the current point in

1.  View Settings object is retrieved.
2.  MarkerStack object is attempted to be retrieved from View Settings with
    key ``_stack_key``.  If it is ``None``, then the stack is empty and there
    is nothing to do.  Otherwise continue.
3.  The top Marker is popped off the Marker Stack.
    If stack is now empty, then the key is erased from the View Settings,
    otherwise the remaining stack is saved back to View Settings.
4.  The Region (icon) is fetched from the left gutter (contains current
    position where we want to place the caret).  It is retrieved using the
    unique key stored inside the popped Marker object.
5.  That set of 1 Region (with that unique key) is removed from the
    View's Region dictionary, causing that icon to be removed.
6.  The saved Viewport position is retrieved from the Marker and
    restored in the View.
7.  Move caret to previously-stored position.  This is done by:
    - All current "Selections" (i.e. carets) are removed from the View, and
    - replaced with one new Region created from the retrieved caret Point.
8.  Finally, take the extra steps necessary to ensure that when the
    count of Markers on that same line of text in the file is
    reduced from 2 to 1, that the icon reverts back to the SINGLE
    Marker icon again.  This isn't necessary if stack is now empty.


DUMP
====

Command Palette:  "MarkerStack: Dump"
Command        :  marker_stack_dump

Print out MarkerStack data for current View to Console.

1.  Retrieve View Settings object.
2.  MarkerStack object is attempted to be retrieved from View Settings with
    key ``_stack_key``.  If it is ``None``, then the stack is empty, print
    "Marker Stack empty.".  Otherwise continue.
    else:
3.  For each Marker in stack:
    - Retrieve its salient points:
      - Index
      - Regions Key
    - Retrieve/compute salient points from associated View Regions list.
      - Cursor Point
      - Line number in text (zero-based)
      - Column number in text (zero-based)
    - Print them in readable table form.



How MarkerStack Saves State Across Sessions:  View Settings
***********************************************************

Persistence across sessions is achieved by:

- storing the list of markers (MarkerStack) with the View settings, and
- marking the Markers (gutter icons saved with View Regions) with the
  sublime.RegionFlags.PERSISTENT flag.

Together, these two lists form a "unit" tied together in this MarkerStack
Package.



MarkerStack Object
******************

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



Design Flaw with Scroll State in Version 1.0
********************************************

Restoring Viewport position along with restoring a previous caret position is "sort of"
what we want.  However, Sublime Text's Viewport position is no longer appropriate if
a large amount of text has been added or deleted above the pushed Marker.  Reason:
it is basically the number of pixels the Viewport has been scrolled down from the top
of the text, and the POPPED caret will have significantly moved in the above case!

What we DO want is that when the position of the caret is saved, it is a certain
percentage of the way down the screen.  And that percentage would need to hold, no
matter if the number of lines of visible text in the window changed before the
positions were "popped".  If the percent is 30% of the way down the screen when
there are 116 lines of visible text, and then the window size gets changed so there
are now only 50 lines of text showing, when the position is popped, the viewport
is scrolled so that the caret is still 30% of the way down the screen --- if that
is doable....

For version 1.0, simply restoring the Viewport Position is fine as a start, but there
appears to be a group of View-object position functions with the names "viewport",
"window", "layout" and "text" relating to position and DIP [1]_ coordinates may be
applicable to this problem, and they are found right underneath these 2 functions in
the ``python38/sublime.py`` file which leads me to believe that they are related.

    viewport_position(self) -> Vector:
        # :returns: The offset of the viewport in layout coordinates.

    set_viewport_position(self, xy: Vector, animate=True):
        # Scrolls the viewport to the given layout position.

As of 29-May-2025, so far, we have been experimenting with just using the above
functions and so far they have been sufficient to the needs of the testers.



Solving this Design Flaw in Version 2.0
***************************************

Indeed, there is a whole View's Viewport API that gives us the power to accomplish
the desired plan above:  to preserve the percentage of the way down the Viewport
for the POPPED caret.  Definitions:

DIP
    TypeAlias = 'float' containing a distance/length measurement.  DIP stands
    for device- or density-independent pixels, a unit of length based on a
    "reference screen" with 160 DIP.  Thus, 1 DIP = 1/160 inch = 0.00625 inch.
    We can think of DIP units as "pixels".

Vector
    TypeAlias = 'Tuple[DIP, DIP]' = (xf, yf)

Point
    TypeAlias = 'int' containing a zero-based character offset within a View's
    Buffer.

Viewport
    The visible area of editable text, between the left and right gutters and
    above any horizontal scrollbar at the bottom of the View.

Layout
    The entire rectangular area of existing text in a View's Buffer, rendered
    in the current font and font size, whether it is visible or not.

    The Layout's dimensions are exactly the DIP width and height of the text
    itself, after being rendered.  These dimensions can be larger or smaller
    than the dimensions of the Viewport.

===========================================================================
Given a Point ``pt``, this is how we compute what percentage of the way down
it is in the Viewport:

Given:  ``pt`` is the caret Point that is being pushed onto the MarkerStack.

>>> _, dip_viewport_is_scrolled_down = view.viewport_position()
>>> dip_viewport_is_scrolled_down
1665.0
>>> _, dip_pt_down_from_layout_top = view.text_to_layout(pt)
>>> dip_pt_down_from_layout_top
1755.0
>>> dip_pt_from_top_of_viewport = dip_pt_down_from_layout_top - dip_viewport_is_scrolled_down
>>> dip_pt_from_top_of_viewport
90.0
>>> _, viewport_height = view.viewport_extent()
>>> viewport_height
1381.0
>>> pct_down_from_viewport_top = dip_pt_from_top_of_viewport / viewport_height
>>> pct_down_from_viewport_top
0.06517
>>> # 6.5% down from the top of the Viewport.
>>> # And so we save `pct_down_from_viewport_top` in the Marker.

===========================================================================
Now given a percent of the way down in the Viewport, this is how we scroll
the Viewport vertically to place the restored caret at that same % of the
way down in the Viewport, given the Viewport's current height.
This is done mostly in reverse of how the percent was computed.

Given:  ``rgn`` is the region retrieved from the View's Region Dictionary
        containing the caret position being POPPED off the MarkerStack.

>>> # Retrieve `pct_down_from_viewport_top` from Marker.
>>> pct_down_from_viewport_top = marker[_pct_fr_top_key]
>>> pct_down_from_viewport_top
0.06517
>>> _, viewport_height = view.viewport_extent()
>>> viewport_height
1381.0
# -------------------------------------------------------------------------
# The Viewport's height can be different from original height, but we use
# original value for illustration.
# -------------------------------------------------------------------------
>>> dip_pt_from_top_of_viewport = viewport_height * pct_down_from_viewport_top
>>> dip_pt_from_top_of_viewport
90.0
>>> pt = rgn.b
>>> pt
# -------------------------------------------------------------------------
# Whatever ``pt`` was---it can be different now if text was added or
# removed above the marker.
# -------------------------------------------------------------------------
>>> _, dip_pt_down_from_layout_top = view.text_to_layout(pt)
>>> dip_pt_down_from_layout_top
1755.0
>>> dip_viewport_is_scrolled_down = dip_pt_down_from_layout_top - dip_pt_from_top_of_viewport
>>> dip_viewport_is_scrolled_down
1665.0
>>> view.set_viewport_position((0.0, dip_viewport_is_scrolled_down), animate=_animate_scroll)
# -------------------------------------------------------------------------
# This scrolls the Viewport to correct position, and relative % position
# within the Viewport is preserved.
# -------------------------------------------------------------------------
"""
import sublime
import sublime_plugin
import os
import functools
from sublime_types import DIP, Vector, Point


# =========================================================================
# Configuration
# =========================================================================


# General
_pkg_name       = 'MarkerStack'
_debugging      = 0          # Integer:  Levels:  0, 1, 2, 3...

# Regions (Gutter Icons)
_rgn_key_prefix = '_marker_stack_icon_'
_rflags         = (
                        sublime.RegionFlags.PERSISTENT  # Save across sessions
                      | sublime.RegionFlags.HIDDEN      # Don't show selection, just the icon.
                  )
_icons_changed  = False

# Marker
_stack_key      = '_marker_stack'
_icon_key       = 'id'
_pct_fr_top_key = 'pct'

# Track on-settings-changed listener.
_settings_chgd_listener_id = '_ms_settings_changed_tag'

# Package Settings
_pkg_settings_file = 'MarkerStack.sublime-settings'

# User Configurable
_icon_path      = 'Packages/MarkerStack/marker_single.png'
_icon_mult_path = 'Packages/MarkerStack/marker_multiple.png'
_icon_color     = 'region.purplish'
_animate_scroll = False


# =========================================================================
# Settings Utilities
# =========================================================================


def ms_setting(key):
    """
    Get a MarkerStack setting from a cached settings object.
    This function expects the following objects to already exist:

    - ``ms_setting.obj``      a ``sublime.Settings`` object (looks like a dictionary)
    - ``ms_setting.default``  a dictionary object with named default values

    :param key:  name of setting whose value will be returned
    """
    assert ms_setting.default is not None, '`ms_setting.default` must exist before calling `ms_setting()`.'
    assert ms_setting.obj is not None, '`ms_setting.obj` must exist before calling `ms_setting()`.'
    default = ms_setting.default.get(key, None)
    return ms_setting.obj.get(key, default)


# =========================================================================
# Events
# =========================================================================


def _dump_internal_values(descr: str):
    if descr:
        print(f'Internal values {descr}:')
    else:
        print(f'Internal values:')

    print(f'  _icon_path      = {_icon_path}')
    print(f'  _icon_mult_path = {_icon_mult_path}')
    print(f'  _icon_color     = {_icon_color}')
    print(f'  _animate_scroll = {_animate_scroll}')
    print(f'  _icons_changed  = {_icons_changed}')


def _dump_settings(descr: str):
    if descr:
        print(f'Settings {descr}:')
    else:
        print(f'Settings:')

    print(f'  icon_path         = {ms_setting("icon_path")}')
    print(f'  icon_mult_path    = {ms_setting("icon_mult_path")}')
    print(f'  icon_color        = {ms_setting("icon_color")}')
    print(f'  animate_scrolling = {ms_setting("animate_scrolling")}')


def _establish_default_settings_once():
    ms_setting.default = {
        'icon_path': _icon_path,
        'icon_mult_path': _icon_mult_path,
        'icon_color': _icon_color,
        'animate_scrolling': False,
    }


def _load_and_import_cached_settings():
    global _icon_path
    global _icon_mult_path
    global _icon_color
    global _animate_scroll
    global _icons_changed

    ms_setting.obj = sublime.load_settings(_pkg_settings_file)

    # if _debugging:
    #     when = 'after loading from settings file'
    #     _dump_settings(when)
    #     _dump_internal_values(when)

    # Prepare to detect icon changes.
    prev_icon_path = _icon_path
    prev_icon_mult_path = _icon_mult_path
    prev_icon_color = _icon_color

    # if _debugging:
    #     print(f'{prev_icon_path=}')
    #     print(f'{prev_icon_mult_path=}')
    #     print(f'{prev_icon_color=}')

    # Now we can fetch user-configurable values.
    _icon_path = ms_setting('icon_path')
    _icon_mult_path = ms_setting('icon_mult_path')
    _icon_color = ms_setting('icon_color')
    _animate_scroll = ms_setting('animate_scrolling')

    # Changed?
    if (
               _icon_path      != prev_icon_path
            or _icon_mult_path != prev_icon_mult_path
            or _icon_color     != prev_icon_color
        ):
        _icons_changed = True

    # if _debugging:
    #     when = 'after loading internal values from cached settings'
    #     _dump_settings(when)
    #     _dump_internal_values(when)


class RegionInfo:
    def __init__(self, rgns: list, line_no: int):
        """ ---------------------------------------------------------------
        Store data about regions stored with the View, in order to build a
        new set of such regions with new icon settings.

        :param rgns:     Region set retrieved by ``view.get_regions()``
        :param line_no:  View's zero-based line number on which the region set
                           (containing 1 region) was found
        --------------------------------------------------------------- """
        self.rgns = rgns
        self.line_no = line_no

    def __repr__(self):
        return f'RegionInfo[{self.rgns}, {self.line_no}]'


def _replace_all_gutter_icons_for_view(view: sublime.View):
    """
    This routine is called immediately after a settings change that involves
    a change to the appearance of the Marker icons in the left gutter.

    The algorithm used uses 2 dictionaries:

    1.  ``region_data`` containing all pertinent info about the View's
        Marker Regions as we remove them, so they can be put back using
        the new Marker icons settings.  Contents:

        - key = unique key for that region set (though it only has 1 region in it)
        - value = RegionInfo
            - rgns from ``view.get_regions()``
            - zero-based line_no

    2.  ``line_no_data``.  Contents:

        - key = View's line number
        - value count of markers that have that line number

    This makes for a fast way to detect which icons need to get added back in.
    It does not matter what order they are put back in.
    """
    vw_settings = view.settings()
    mstack = vw_settings.get(_stack_key)

    if mstack is not None:
        region_data = {}
        line_no_data = {}

        for marker in mstack:
            icon_key = marker[_icon_key]
            rgns = view.get_regions(icon_key)
            # Certain rare things (e.g. exception in Plugin) can cause these two
            # things (View Settings => stack, and View Regions) to go out of sync.
            # This little precaution prevents an exception when that happens.
            if rgns:
                # Add to `region_data` dictionary.
                rgn = rgns[0]
                line_no = view.rowcol(rgn.b)[0]
                rgn_info = RegionInfo(rgns, line_no)
                region_data[icon_key] = rgn_info

                # Add to, or increase count, in `line_no_data` dictionary.
                if line_no in line_no_data:
                    line_no_data[line_no] += 1
                else:
                    line_no_data[line_no] = 1

                # Remove `rgns` from View
                view.erase_regions(icon_key)

        if _debugging >= 2:
            print(f'Dictionaries built for View [{view.view_id}]:')

            print(f'  region_data:')
            for icon_key in region_data:
                print(f'    key={icon_key:21}  {region_data[icon_key]!r}')

            print(f'  line_no_data:')
            for line_no in line_no_data:
                print(f'    line_no_data={line_no:2}  count={line_no_data[line_no]}')

        # -----------------------------------------------------------------
        # Now we use those 2 dictionaries to put new icons back into the
        # View's Regions dictionary.
        # -----------------------------------------------------------------
        for icon_key in region_data:
            if _debugging >= 2:
                print(f'    Putting back:  key={icon_key:21}  {region_data[icon_key]!r}')
            rgn_info = region_data[icon_key]
            rgns     = rgn_info.rgns
            line_no  = rgn_info.line_no
            count    = line_no_data[line_no]

            # Which icon?
            if count > 1:
                icon_path = _icon_mult_path
            else:
                icon_path = _icon_path

            view.add_regions(icon_key, rgns, _icon_color, icon_path, _rflags)

            if _debugging >= 2:
                print(f'      icon_key ={icon_key!r}')
                print(f'      icon_path={icon_path!r}')
                print(f'      rgn      ={rgns[0]!r}')


def _replace_gutter_icons_if_changed():
    global _icons_changed

    if _debugging >= 2:
        print('>> In _replace_gutter_icons_if_changed()...')

    if _icons_changed:
        # Do this only once per icon-settings change.
        _icons_changed = False

        if _debugging:
            print('  Handling changed icon settings...')

        for win in sublime.windows():
            if _debugging >= 2:
                print(f'    Window id: {win.window_id}')
            for view in win.views():
                if _debugging >= 2:
                    print(f'      View id: {view.view_id}')
                # Act only on Views that have MarkerStack info.
                vw_settings = view.settings()
                mstack = vw_settings.get(_stack_key)

                if mstack is not None:
                    if _debugging >= 2:
                        print(f'        View id: {view.view_id} has MarkerStack info.')
                    _replace_all_gutter_icons_for_view(view)
    else:
        if _debugging:
            print('    Icons did not change...')


def _on_pkg_settings_change():
    _load_and_import_cached_settings()
    _replace_gutter_icons_if_changed()


def plugin_loaded():
    """
    Initialize plugin.
    """
    if _debugging:
        print('>> In plugin_loaded()...')
    global _icons_changed

    # Set up default and overridable Package settings.
    # `ms_setting()` cannot be called until this is done.
    _establish_default_settings_once();
    _load_and_import_cached_settings();

    # Don't trigger icon reload here.
    if _debugging:
        print(f'{_icons_changed=} before setting it FALSE.')
    _icons_changed = False

    # Establish event hook for "settings changed" event. This allows the user
    # to change package settings and have them be instantly reflected in the
    # Sublime Text UI.
    ms_setting.obj.add_on_change(_settings_chgd_listener_id, _on_pkg_settings_change)

    if _debugging:
        print(f'{_pkg_name} loaded.')
        print(f'  Configured _icon_path      = [{_icon_path}]')
        print(f'  Configured _icon_mult_path = [{_icon_mult_path}]')
        print(f'  Configured _icon_color     = [{_icon_color}]')
        print(f'  Configured _animate_scroll = [{_animate_scroll}]')


def plugin_unloaded():
    if hasattr(ms_setting, 'obj'):
        ms_setting.obj.clear_on_change(_settings_chgd_listener_id)

    debugging = ms_setting('pc_debugging')
    if debugging:
        print(f'{_pkg_name}:  Plugin unloaded.')


# =========================================================================
# Commands and Related Classes
# =========================================================================


def _dump_marker_stack_contents(view: sublime.View):
    """
    Display stack contents.
    """
    # 1.  Retrieve View Settings object.
    vw_settings = view.settings()

    # 2.  MarkerStack object is attempted to be retrieved from View Settings with
    #     key ``_stack_key``.  If it is ``None``, then the stack is empty and there
    #     is nothing to do.  If it is not ``None``, then this sequence is continued.
    mstack = vw_settings.get(_stack_key)

    if mstack is None:
        print("Marker Stack empty.")
    else:
        # 3.  For each MarkerStackMarker in stack:
        #     - Retrieve its salient points:
        #       - Index
        #       - Regions Key
        #     - Retrieve/compute salient points from associated View Regions list.
        #       - Cursor Point
        #       - Line number in text (zero-based)
        #       - Column number in text (zero-based)
        #     - Print them in readable table form.
        print('============================================')
        print('Marker Stack Contents:')
        print('============================================')
        print('Idx  Icon Key                Caret  Line:Col')
        print('---  ---------------------  ------  --------')
        #      99.  _marker_stack_icon_99  999999  9999:999
        for i, marker in enumerate(mstack):
            icon_key = marker[_icon_key]
            rgns     = view.get_regions(icon_key)
            # Certain rare things (e.g. exception in Plugin) can cause these two
            # things (View Settings => stack, and View Regions) to go out of sync.
            # This little precaution prevents an exception when that happens.
            if rgns:
                pt       = rgns[0].b
                row, col = view.rowcol(pt)
                row += 1
                col += 1
            else:
                pt       = '?'
                row, col = ('?', '?')
            # Make them 1-based, since line numbers are 1-based.
            print(f'{i:2}.  {icon_key:<21}  {pt:6}  {row:4}:{col}')


def _count_of_regions_on_line(view: sublime.View, mstack: list, target_line_no: int) -> int:
    """
    Count number of Regions (storage of caret location) on line `target_line_no`.
    """
    result = 0

    for marker in mstack:
        icon_key = marker[_icon_key]
        rgns = view.get_regions(icon_key)

        # Certain rare things (e.g. exception in Plugin) can cause these two
        # things (View Settings => mstack, and View Regions) to go out of sync.
        # This little precaution prevents an exception when that happens.
        if rgns:
            rgn = rgns[0]
            line_no = view.rowcol(rgn.b)[0]
            if line_no == target_line_no:
                result += 1

    return result


def _adjust_marker_icon_for_count_on_line(view: sublime.View, mstack: list, target_line_no: int, count: int):
    """
    Remove and replace icon on line `target_line_no` with the icon appropriate
    to ``count`` Markers.  This requires removal of all regions on that line to
    make the original icon go away.  Then they are added back in with the last
    one getting the appropriate icon.

    Use these 2 lists to store the regions and keys while they are being
    removed from the View's Region dictionary:
    `rgns_on_this_line`
    `rgns_on_this_line_keys`
    """
    rgns_on_this_line = []
    rgns_on_this_line_keys = []

    for marker in mstack:
        icon_key = marker[_icon_key]
        rgns = view.get_regions(icon_key)
        # Certain rare things (e.g. exception in Plugin) can cause these two
        # things (View Settings => stack, and View Regions) to go out of sync.
        # This little precaution prevents an exception when that happens.
        if rgns:
            rgn = rgns[0]
            line_no = view.rowcol(rgn.b)[0]
            if line_no == target_line_no:
                # Add key and Region to the 2 lists.
                rgns_on_this_line.append(rgn)
                rgns_on_this_line_keys.append(icon_key)
                # Remove Region temporarily from View's Region dictionary.
                view.erase_regions(icon_key)
                if _debugging:
                    print(f'Temporarily removing (same line)=[{icon_key}]')

    # ---------------------------------------------------------------------
    # Put list of Regions back into View's Regions dictionary.
    # Only the LAST Region will get an icon.  Reason:  after the call
    # to ``add_regions()`` returns, the icon is no longer associated
    # with the Region just added (if it ever was).  Instead it is
    # associated with the LINE OF TEXT in the View.  So this is merely
    # a way of keeping things "neat".
    #
    # The LAST item in both lists now represents the most recent Marker on
    # line ``target_line_no``.  Both lists are guaranteed to have at least
    # 1 element in them.  If they contain more than 1 item, the newest
    # Marker is at the end of the list, and the older Regions + keys are
    # earlier in the list.
    #
    # Example of `rgns_on_this_line` and `rgns_on_this_line_keys`:
    # -----------------------------------------------------------
    # Index   Key
    # 0       _marker_stack_icon_3   <-- oldest Marker
    # 1       _marker_stack_icon_6   <-- old Marker
    # 2       _marker_stack_icon_11  <-- newest Marker
    #
    #     Now add this list (stack) back into the View Regions dictionary,
    #     oldest first.
    # ---------------------------------------------------------------------

    # The ``icon_path`` computed here will be sent with the LAST region
    # passed to ``add_regions()``.  All the rest will have no icon.
    if count > 1:
        icon_path = _icon_mult_path
    else:
        icon_path = _icon_path

    if _debugging:
        print(f'Adding icon [{os.path.basename(icon_path)}] into gutter:')

    while rgns_on_this_line_keys:
        icon_key = rgns_on_this_line_keys.pop()
        rgn      = rgns_on_this_line.pop()

        if len(rgns_on_this_line_keys) == 0:
            view.add_regions(icon_key, [rgn], _icon_color, icon_path, _rflags)
            if _debugging:
                print(f'  icon_key ={icon_key!r}')
                print(f'  icon_path={icon_path!r}')
                print(f'  rgn      ={rgn!r}')
        else:
            view.add_regions(icon_key, [rgn], _icon_color, '', _rflags)
            if _debugging:
                print(f'  icon_key ={icon_key!r}')
                print(f'  icon_path=""')
                print(f'  rgn      ={rgn!r}')


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
    def __init__(self, pct_down_from_viewport_top: float, icon_key: str):
        self[_pct_fr_top_key] = pct_down_from_viewport_top
        self[_icon_key]       = icon_key

    def __repr__(self):
        return f'Marker[{self[_pct_fr_top_key]}, {self[_icon_key]}]'


class MarkerStackPushCommand(sublime_plugin.TextCommand):
    def run(self, edit, testing=False):
        """
        A Marker PUSH is legal regardless of whether any text is selected.  The
        position of the caret (i.e. Region.b) is used to get the Point to be saved.
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
        - Region at caret is added to View Regions dictionary with unique key
          (stored with Marker in stack), and with flags telling it to persist
          across sessions.
        """
        # 1.  Retrieve View Settings object.
        vw = self.view
        vw_settings = vw.settings()

        # 2.  Attempt to retrieve MarkerStack object from View Settings with key
        #     ``_stack_key``.  If ``None``, create an empty list (the stack).
        mstack = vw_settings.get(_stack_key)

        if mstack is None:
            mstack = []

        # 3.  Capture caret position and Viewport position.
        pt = vw.sel()[0].b
        _, dip_vp_is_scrolled_down = vw.viewport_position()

        # 4.  Remember index of where new Marker will go in ``marker_idx``.
        marker_idx = len(mstack)

        # 5.  Note current line number and count number of Regions now on this
        #     same line before the new Marker is added.  This needs to be done
        #     while `mstack` and the View's Region dictionary are in sync.
        curr_line_no = vw.rowcol(pt)[0]
        if _debugging:
            print(f'{curr_line_no=}')
        prev_rgn_count_on_line = _count_of_regions_on_line(vw, mstack, curr_line_no)
        if _debugging:
            print(f'Found {prev_rgn_count_on_line} regions on zero-based line {curr_line_no}.')

        # 5A.  Compute percent down from Viewport top where marker is.
        _, dip_pt_down_from_text_top = vw.text_to_layout(pt)
        dip_pt_from_top_of_vp = dip_pt_down_from_text_top - dip_vp_is_scrolled_down
        _, vp_height = vw.viewport_extent()
        pct_down_from_viewport_top = dip_pt_from_top_of_vp / vp_height

        # 6.  Create and push new Marker onto stack.
        icon_key = f'{_rgn_key_prefix}{marker_idx}'
        marker = MarkerStackMarker(pct_down_from_viewport_top, icon_key)
        mstack.append(marker)

        # 7.  Save modified stack (list) to View Settings with ``_stack_key``.
        vw_settings.set(_stack_key, mstack)
        if _debugging:
            print(f'Pushed marker: {marker!r}')

        # 8.  Add Region to View's Region dictionary.
        rgn = sublime.Region(pt)

        if prev_rgn_count_on_line == 0:
            # First icon.  Passing a real icon here works as expected.
            icon_path = _icon_path
        else:
            # Passing an icon to `add_regions()` after there is already a
            # gutter icon on this line, DOES NOT in fact change the already-
            # existing icon on in the gutter!  That has to be done by
            # special operation later.  So `icon_path` is left empty so it
            # doesn't "seem like" we are causing a new icon to show up.
            icon_path = ''

        vw.add_regions(icon_key, [rgn], _icon_color, icon_path, _rflags)

        # 9.  If needed, adjust gutter icon displayed.   This needs to be done
        #     while `mstack` and the View's Region dictionary are in sync.
        #     This is why this is being done AFTER the call to `add_regions().
        if prev_rgn_count_on_line == 1:
            # Marker count on this line just changed from 1 to 2.  Gutter
            # icon change is needed to show MULTIPLE Marker icon.
            _adjust_marker_icon_for_count_on_line(vw, mstack, curr_line_no, 2)


class MarkerStackPopCommand(sublime_plugin.TextCommand):
    def run(self, edit, testing=False):
        """
        Pop Marker off stack, restoring that caret- and viewport positions.
        """
        # 1.  View Settings object is retrieved.
        vw = self.view
        vw_settings = vw.settings()

        # 2.  MarkerStack object is attempted to be retrieved from View Settings with
        #     key ``_stack_key``.  If it is ``None``, then the stack is empty and there
        #     is nothing to do.  If it is not ``None``, then this sequence is continued.
        mstack = vw_settings.get(_stack_key)

        if mstack is None:
            if _debugging:
                print("Marker Stack empty.")
        else:
            # 3.  The top Marker is popped off the Marker Stack.
            #     If stack is now empty, then the key is erased from the View Settings,
            #     otherwise the remaining stack is saved back to View Settings.
            marker = mstack.pop()

            if _debugging:
                print(f'Popped Marker: {marker}')

            if len(mstack) == 0:
                vw_settings.erase(_stack_key)
            else:
                vw_settings.set(_stack_key, mstack)

            # 4.  The Region (icon) is fetched from the left gutter (contains current
            #     position where we want to place the caret).  It is retrieved using the
            #     unique key stored inside the popped Marker object.
            icon_key = marker[_icon_key]
            rgns = vw.get_regions(icon_key)

            # 5.  That set of 1 Region (with that unique key) is removed from the
            #     View's Region dictionary, causing that icon to be removed.
            vw.erase_regions(icon_key)

            # 6.  Move caret to previously-stored position.  This is done by:
            #     - All current "Selections" (i.e. carets) are removed from the View, and
            #     - replaced with one new Region created from the retrieved caret Point.
            # For safety....
            if rgns:
                rgn = rgns[0]
                sel_list = vw.sel()
                sel_list.clear()
                sel_list.add(rgn)

                # 7.  Scroll Viewport so caret is same percent down from top of
                #     screen as it was when it was pushed.  Note:  viewport's height
                #     might also be different now.  We still use that percent.
                #     This is done mostly in reverse of how the percent was computed.
                #     ('vp' = viewport.)
                pct_down_from_viewport_top = marker[_pct_fr_top_key]
                _, vp_height = vw.viewport_extent()
                dip_pt_from_top_of_vp = vp_height * pct_down_from_viewport_top
                pt = rgn.b
                _, dip_pt_down_from_text_top = vw.text_to_layout(pt)
                dip_vp_is_scrolled_down = dip_pt_down_from_text_top - dip_pt_from_top_of_vp
                vw.set_viewport_position((0.0, dip_vp_is_scrolled_down), animate=_animate_scroll)

                if _debugging:
                    print(f'Popped Region: {rgn}')
                    if len(mstack) == 0:
                        print("Marker Stack now empty.")

                # 8.  Finally, take the extra steps necessary to ensure that when the
                #     count of Markers on that same line of text in the file is
                #     reduced from 2 to 1, that the icon reverts back to the SINGLE
                #     Marker icon again.  This isn't necessary if stack is now empty.
                if mstack:
                    curr_line_no = vw.rowcol(rgn.b)[0]

                    if _count_of_regions_on_line(vw, mstack, curr_line_no) == 1:
                        # Marker count on this line just changed from 1 to 2.  Gutter
                        # icon change is needed to show MULTIPLE Marker icon.
                        _adjust_marker_icon_for_count_on_line(vw, mstack, curr_line_no, 1)


class MarkerStackDumpCommand(sublime_plugin.TextCommand):
    def run(self, edit, testing=False):
        """
        Display stack contents.
        """
        _dump_marker_stack_contents(self.view)


