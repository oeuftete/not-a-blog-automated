import datetime

import click


def tomorrow():
    """Return tomorrow as YYYYMMDD."""
    return (datetime.date.today() +
            datetime.timedelta(days=1)).strftime('%Y%m%d')


@click.command()
@click.option('--date',
              default=tomorrow(),
              help='Date to generate as YYYYMMDD')
def main(date):
    """
    Generate the daily blog entry for a given day.
    """
    click.echo('Beginning blog entry generation...')
    click.echo(f'  Date: {date}')

    #  Drive file generation
    #  TODO: Get the template file for the day of the week.
    #  TODO: Template files are by convention or just configurable IDs?
    #  TODO: Copy that to a file named conventionally, e.g. "Monday, 9/30/19"
    #  TODO: The template file may be restricted in permissions, but ensure the
    #  daily file is open.
    #  TODO: Don't create the daily file if it already exists.
    #  TODO: Get a link for the daily file either way to add to the blog entry.

    #  Blog entry generation
    #  TODO: Generate the post if it doesn't exist.
    #  TODO: Post content is "Add your times here." anchor linked to the
    #  spreadsheet for the day.

    #  Extracting from Dan's site:
    #
    #  <a href="https://docs.google.com/spreadsheets/d/{id}/edit?usp=sharing">Add your times here.</a>
    #  <br />
    #  <iframe src="https://docs.google.com/spreadsheets/d/e/{different-id}/pubhtml?gid=0&amp;single=true&amp;widget=true&amp;headers=false"></iframe>
    #
    #  The 'id' is just the 'id' attribute.  How do we get the embed link?


if __name__ == '__main__':
    main()
