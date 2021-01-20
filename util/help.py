#!/usr/bin/env python

def show_help():
    return """Hi!  I repost **Voice of Light** posts to specified channels and optionally mention specified roles

To set a channel for a Youtube or Twitch creator:

`;giggle set <creator> <channel> role=<role>`

role is optional.  If the role name contains spaces, it must be enclodesd in double quotes

For example:

`role="Some role name with spaces"`

To unset a channel for a creator

`;giggle unset <creator>`

To see a list of current settings:

`;giggle list`"""
