# coding: utf-8
import argparse


def make_parser():
    """
    Generate the parser for all sub-commands
    """

    parser = argparse.ArgumentParser(description='BERNARD CLI utility')
    sp = parser.add_subparsers(help='Sub-command')

    parser_run = sp.add_parser('run', help='Run the BERNARD server')
    parser_run.set_defaults(action='run')

    parser_sheet = sp.add_parser('sheet', help='Import files from Google '
                                               'Sheets')
    parser_sheet.set_defaults(action='sheet')
    parser_sheet.add_argument(
        '--auth_host_name',
        default='localhost',
        help='Hostname when running a local web server.'
    )
    parser_sheet.add_argument(
        '--noauth_local_webserver',
        action='store_true',
        default=False,
        help='Do not run a local web server.'
    )
    parser_sheet.add_argument(
        '--auth_host_port',
        default=[8080, 8090],
        type=int,
        nargs='*',
        help='Port web server should listen on.'
    )
    parser_sheet.add_argument(
        '--logging_level',
        default='ERROR',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level of detail.'
    )

    parser_sp = sp.add_parser('start_project', help='Starts a project')
    parser_sp.set_defaults(action='start_project')
    parser_sp.add_argument(
        'project_name',
        help='A snake-case name for your project'
    )
    parser_sp.add_argument(
        'dir',
        help='Directory to store the project'
    )

    return parser


def main():
    """
    Run the appropriate main function according to the output of the parser.
    """

    parser = make_parser()
    args = parser.parse_args()

    if not hasattr(args, 'action'):
        parser.print_help()
        exit(1)

    if args.action == 'sheet':
        from bernard.misc.sheet_sync import main as main_sheet
        main_sheet(args)
    elif args.action == 'run':
        from bernard.cli import main as main_run
        main_run()
    elif args.action == 'start_project':
        from bernard.misc.start_project import main as main_sp
        main_sp(args)
