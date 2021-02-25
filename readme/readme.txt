Plugin for CudaText.
Snippets engine, which is described in CudaText wiki:
https://wiki.freepascal.org/CudaText_plugins#Snippets

Now plugin also supports snippets from VS Code.
It gives the command to install snippets from VS Code repositories.
This big rework was done by @OlehL.
This includes support of TextMate snippet macros:

- TM_SELECTED_TEXT
- TM_CURRENT_LINE
- TM_CURRENT_WORD
- TM_LINE_INDEX
- TM_LINE_NUMBER
- TM_FILEPATH
- TM_DIRECTORY
- TM_FILENAME
- TM_FILENAME_BASE
- CLIPBOARD
- WORKSPACE_NAME
- CURRENT_YEAR
- CURRENT_YEAR_SHORT
- CURRENT_MONTH
- CURRENT_MONTH_NAME
- CURRENT_MONTH_NAME_SHORT
- CURRENT_DATE
- CURRENT_DAY_NAME
- CURRENT_DAY_NAME_SHORT
- CURRENT_HOUR
- CURRENT_MINUTE
- CURRENT_SECOND
- CURRENT_SECONDS_UNIX
- BLOCK_COMMENT_START
- BLOCK_COMMENT_END
- LINE_COMMENT

Authors:
  Alexey Torgashin (CudaText)
  Oleh Lutsak, https://github.com/OlehL
  Shovel (CudaText forum user), https://github.com/halfbrained
License: MIT
