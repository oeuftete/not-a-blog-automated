# Not a Blog: automated

This project aims to automate the blog posts and spreadsheet generation of Dan
Feyer's crossword speed-solving [Not a Blog][not-a-blog], used by a subset of
speed-solvers and enthusiasts to track their solving times.  Dan recently
announced [he was discontinuing][not-a-blog-the-end] manual generation of the
posts.

## Goals

* Automate the posting of the daily Google Drive spreadsheets, appropriately
  configured by day-of-week.
* Automate the posting of the daily blog entry, with an embedded spreadsheet.
* Automate the above in a way that is easily configurable for arbitrary Google
  accounts.
* Make any sensible improvements to the spreadsheet templates.  This may be
  nothing at all, though default formatting of the cells to be plain text (so
  they are not auto-detected as `hh:mm:ss`) would be nice.

## Configuration

* Generate Google Drive credentials via the [Python
  quickstart][py-gdrive-quickstart].

[not-a-blog]: https://dandoesnotblog.blogspot.com/
[not-a-blog-the-end]: https://dandoesnotblog.blogspot.com/2019/09/friday-92719.html
[py-gdrive-quickstart]: https://developers.google.com/drive/api/v3/quickstart/python
