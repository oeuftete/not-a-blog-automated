import datetime
import os.path
import pickle

import click
from googleapiclient.discovery import build
from googleapiclient.http import HttpError as GoogleApiHttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pytz


class GoogleApi():

    SCOPES = [
        'https://www.googleapis.com/auth/blogger',
        'https://www.googleapis.com/auth/drive',
    ]

    def __init__(self):
        creds = None

        # TODO: Let the pickled token location be configurable.
        #
        # The file token.pickle stores the user's access and refresh tokens,
        # and is created automatically when the authorization flow completes
        # for the first time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                #  TODO: The json credentials should be configurable.
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.path.join(os.path.expanduser('~'),
                                 '.gdrive-credentials-notablog.json'),
                    self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.creds = creds

    @property
    def drive_service(self):
        return build('drive', 'v3', credentials=self.creds)

    @property
    def blogger_service(self):
        return build('blogger', 'v3', credentials=self.creds)

    def get_file_id_by_name(self, name):
        """Return the id of an untrashed file with the given name."""
        r = self.drive_service.files().list(
            pageSize=1,
            q=f"name='{name}' and trashed=false",
            fields="nextPageToken, files(id, name)").execute().get(
                'files', [None])
        if r:
            return r[0].get('id')


def tomorrow():
    """Return tomorrow as a datetime date."""
    return datetime.date.today() + datetime.timedelta(days=1)


#  TODO: Some of these methods should be in their own class or maybe our
#  GoogleApi class since they start by instantiating the API.
def create_daily_post(date, blog_id, sheet_id):
    """Create the daily blog post if necessary."""

    api = GoogleApi()
    #  Does the post exist?  Look for it.

    #  TODO: DRY
    target_post_name = date.strftime('%A, %m/%-d/%y')
    thirty_days_ago = (datetime.datetime.now(datetime.timezone.utc) -
                       datetime.timedelta(days=30)).isoformat()

    post_hits = api.blogger_service.posts().list(
        blogId=blog_id,
        status=['draft', 'live', 'scheduled'],
        startDate=thirty_days_ago).execute()
    if list(
            filter(lambda p: p.get('title') == target_post_name,
                   post_hits.get('items', {}))):
        click.echo(f'  Post already exists for [{target_post_name}]')
        click.echo('  You may need to schedule it manually.')
        return

    #  Post didn't exist, let's make it.
    anchor_url = ('https://docs.google.com/spreadsheets/d/'
                  f'{sheet_id}/edit?usp=sharing')

    embed_url = ('https://docs.google.com/spreadsheets/d/'
                 f'{sheet_id}/preview?usp=sharing')

    content = f'''
<a href="{anchor_url}">Add your times here</a>.
<br />
<iframe src="{embed_url}"></iframe>
'''

    post = api.blogger_service.posts().insert(blogId=blog_id,
                                              body={
                                                  'content': content,
                                                  'labels':
                                                  [date.strftime('%A')],
                                                  'title': target_post_name,
                                              },
                                              isDraft=True).execute()

    post_id = post.get('id')
    if not post_id:
        raise click.ClickException(
            '  No post id: something went wrong with draft creation')

    click.echo(f'  Draft post created: [{post_id}]')

    #  Publish at 7pm Eastern the day before.  This is a bit earlier than Dan's
    #  posts, and earlier than many puzzles are available, but useful for ones
    #  that do come in earlier, like Fireball at times, maybe others.
    publish_date = pytz.timezone('US/Eastern').localize(
        datetime.datetime.combine(date - datetime.timedelta(days=1),
                                  datetime.time(19, 0, 0, 0)))

    api.blogger_service.posts().publish(
        blogId=blog_id, postId=post_id,
        publishDate=publish_date.isoformat()).execute()
    click.echo('  Post scheduled.')


def create_daily_sheet(date):
    """Create (if necessary) the specified daily spreadsheet."""
    api = GoogleApi()

    target_file_name = date.strftime('%A, %m/%-d/%y')
    target_id = api.get_file_id_by_name(target_file_name)

    if target_id:
        click.echo(f'  File already exists: [{target_id}]')
        return target_id

    #  Get the template file for the day of the week.  File must be
    #  named as exactly "{day of week} template" in the Drive account.
    dow = date.strftime('%A')
    template_name = f'{dow} template'

    template_id = api.get_file_id_by_name(template_name)
    if not template_id:
        raise click.ClickException(
            f'No template file found for [{template_name}]!')

    click.echo(f'  Template ID: [{template_id}]')

    new_file_request_body = {
        'name': date.strftime('%A, %m/%-d/%y'),
        'parents': [api.get_file_id_by_name('daily')]
    }
    new_id = api.drive_service.files().copy(
        fileId=template_id, body=new_file_request_body).execute().get('id')
    click.echo(f'  New file created: [{new_id}]')
    return new_id


def set_anyone_writer_permissions(file_id):
    """Set global write permission for a file by id."""
    api = GoogleApi()

    #  The new file needs to be writable by all.  That's the point.  This call
    #  still works, and does not add a duplicate permission, if the permission
    #  already exists.
    api.drive_service.permissions().create(fileId=file_id,
                                           body={
                                               'role': 'writer',
                                               'type': 'anyone'
                                           }).execute()
    click.echo('  New file permissions set.')


def publish_file(file_id):
    """Publish a file by id to allow embedding."""

    # HT: https://stackoverflow.com/a/38617031/7674
    api = GoogleApi()
    api.drive_service.revisions().update(fileId=file_id,
                                         revisionId='1',
                                         body={
                                             'published': True,
                                             'publishAuto': True
                                         }).execute()
    click.echo('  File published for web embedding.')


def get_blog_id_by_url(url):
    api = GoogleApi()
    try:
        blog_id = api.blogger_service.blogs().getByUrl(
            url=url).execute().get('id')
        click.echo(f'  Found blog id: [{blog_id}]')
        return blog_id
    except GoogleApiHttpError:
        raise click.ClickException(
            f'  Blog not found in this account: [{url}]')


#  MAIN
@click.command()
@click.option('--date',
              default=tomorrow(),
              help='Date to generate as YYYYMMDD')
@click.option('--blog-url',
              default='https://danstilldoesnnotblog.blogspot.com/',
              help='The Blogger blog to post to')
def main(date, blog_url):
    """
    Generate the daily blog entry for a given day.
    """
    click.echo('Beginning blog entry generation...')

    if isinstance(date, str):
        try:
            date = datetime.date(int(date[:4]), int(date[4:6]), int(date[6:]))
        except ValueError:
            raise click.ClickException(
                f'Given date [{date}] was probably invalid')

    click.echo('  Date: {}'.format(date.strftime('%Y%m%d')))

    drive_file_id = create_daily_sheet(date)
    set_anyone_writer_permissions(drive_file_id)
    publish_file(drive_file_id)

    blog_id = get_blog_id_by_url(blog_url)
    create_daily_post(date, blog_id, drive_file_id)


if __name__ == '__main__':
    main()
