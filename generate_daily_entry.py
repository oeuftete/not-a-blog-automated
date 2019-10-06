import datetime
import os.path
import pickle

import click
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.appdata',
    'https://www.googleapis.com/auth/drive.file',
]


class GoogleApi():
    def __init__(self):
        creds = None

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
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.path.join(os.path.expanduser('~'),
                                 '.gdrive-credentials-notablog.json'), SCOPES)
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


def create_daily(date):
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


@click.command()
@click.option('--date',
              default=tomorrow(),
              help='Date to generate as YYYYMMDD')
def main(date):
    """
    Generate the daily blog entry for a given day.
    """
    click.echo('Beginning blog entry generation...')
    click.echo('  Date: {}'.format(date.strftime('%Y%m%d')))

    drive_file_id = create_daily(date)
    set_anyone_writer_permissions(drive_file_id)
    publish_file(drive_file_id)

    #  TODO: Get links for the daily file either way to add to the blog entry.
    #    TODO: anchor link
    #    TODO: embed link

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
    #    TODO: Based on the SO link I found, the regular id should work in the
    #    iframe embedding.  Not sure what the different id is in Dan's posts
    #    yet, or if it matters.


if __name__ == '__main__':
    main()
