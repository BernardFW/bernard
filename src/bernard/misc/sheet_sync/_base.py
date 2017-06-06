# coding: utf-8
import httplib2
import os
import ujson
import csv
from tempfile import NamedTemporaryFile
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from bernard.conf import settings


SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
APPLICATION_NAME = 'Bernard Sheet Sync'
DISCOVERY_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'


class SheetDownloader(object):
    """
    Download Google sheets into CSV files.

    Follow the tutorial here:
    https://developers.google.com/sheets/api/quickstart/python

    You must take the JSON credential file's content and put it in the
    settings under GOOGLE_SHEET_SYNC['credentials'].

    In order to make the class usable, you need to call `init()` first, which
    might open your browser and open an OAuth screen.
    """

    def __init__(self, flags):
        self.flags = flags
        self.credentials = None
        self.http = None
        self.service = None

    def init(self):
        """
        Fetch the credentials (and cache them on disk).
        """

        self.credentials = self._get_credentials()
        self.http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build(
            'sheets',
            'v4',
            http=self.http,
            discoveryServiceUrl=DISCOVERY_URL,
        )

    def _get_credentials(self):
        """
        Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """

        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')

        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)

        credential_path = os.path.join(
            credential_dir,
            'bernard.sheets-sync.json',
        )

        store = Storage(credential_path)
        credentials = store.get()

        if not credentials or credentials.invalid:
            with NamedTemporaryFile(suffix='.json') as f:
                data = ujson.dumps(settings.GOOGLE_SHEET_SYNC['credentials'])
                f.write(data.encode('utf-8'))
                f.flush()
                flow = client.flow_from_clientsecrets(f.name, SCOPES)

            flow.user_agent = APPLICATION_NAME
            credentials = tools.run_flow(flow, store, self.flags)
            print('Storing credentials to ' + credential_path)

        return credentials

    def download_sheet(self, file_path, sheet_id, cell_range):
        """
        Download the cell range from the sheet and store it as CSV in the
        `file_path` file.
        """

        result = self.service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=cell_range,
        ).execute()

        values = result.get('values', [])

        with open(file_path, newline='', encoding='utf-8', mode='w') as f:
            writer = csv.writer(f, lineterminator='\n')

            for row in values:
                writer.writerow(row)


def main(flags):
    """
    Download all sheets as configured.
    """

    dl = SheetDownloader(flags)
    dl.init()

    for file_info in settings.GOOGLE_SHEET_SYNC['files']:
        print('Downloading {}'.format(file_info['path']))
        dl.download_sheet(
            file_info['path'],
            file_info['sheet'],
            file_info['range'],
        )
