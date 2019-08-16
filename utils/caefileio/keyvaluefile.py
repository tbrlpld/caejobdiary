"""
Functions for reading of key-value-files (e.g. joblogfiles or job README files)

Joblogfiles (the ones created upon job submission) and job README
files share some similarities. Both files are plain text files where the
information is stored as key-value pairs (of typically one line).

The key and value in these lines are separated by a colon (":").

Both of these filetypes have keys which expand multiple lines, though. These
keys require special handling.

The read functions which are similar between both (joblogfiles and job README)
is stored in this module to make them available to the specialized modules for
each of these filetypes.
"""


# -----------------------------------------------------------------------------
def get_value_string_from_line(line):
    """
    Get value string from colon separated key-value line

    Key and value are expected to be separated by a colon ':'. The key and
    the colon are truncated and the part after the colon, namely the value,
    is returned.

    Leading and trailing whitespaces are stripped from the value

    Parameter
    ---------
    line : str, required
        string to extract the value from

    Returns
    -------
    str
        Value string extracted from the line. Empty string if no value was
        found.
    """

    value_string = ""
    line_split = line.strip().split(":", maxsplit=1)
    if len(line_split) > 1:
        value_string = line_split[1].strip()
    return value_string
