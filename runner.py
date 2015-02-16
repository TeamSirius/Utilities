import argparse
import os
from scripts import Locator, analysis, dump, newmapper


def print_options(options):
    message = '{}: {}'
    for indx, item in enumerate(options):
        print (message.format(indx, item))

    print (message.format('q', 'Quit'))

    return raw_input('Your selection: ')


def main(args):
    options = ['Locate last point', 'Analyze DB', 'Dump DB', 'Map New Points']
    while True:
        selection = print_options(options)
        if selection == 'q':
            return
        try:
            selected = int(selection)
        except ValueError:
            selected = -1

        if 0 <= selected < len(options):
            break
        else:
            msg = "{0}That's not an option, Dan. Please try again{0}"
            print(msg.format(os.linesep))

    if selected == 0:
        Locator.Launch_Locator(args.db_password)
    elif selected == 1:
        analysis.Analyse(args.db_password)
    elif selected == 2:
        msg = 'Path to output file (It will be overwritten if it exists): '
        output_file = raw_input(msg)
        dump.dump(args.db_password, output_file)
    elif selected == 3:
        msg = 'Path to image file to work with: '
        input_file = raw_input(msg)
        newmapper.begin_mapping(input_file, False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('db_password', help='The database password')
    args = parser.parse_args()
    main(args)
