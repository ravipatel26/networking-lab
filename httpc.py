import request_methods
import printing_utils
import argparse
import sys


def validate_keyval_syntax(param, fh):
    if param.count(':') == 1:
        key = param.rpartition(':')[0]
        val = param.rpartition(':')[2]

        # clean key and val of whitespace, newlines, tabs.
        key = key.replace('\n', '')
        key = key.replace('\t', '')
        key = key.replace('~', '')
        key = ' '.join(key.split())
        val = val.replace('\n', '')
        val = val.replace('\t', '')
        val = val.replace('~', '')
        val = ' '.join(val.split())

        if key != "" and val != "":
            return str(key + ":" + val)
        else:
            print ("Error, blanks before/after \':\'. "
                   "in this param: \'" + key + ":" + val + "\', Omitting param.", file=fh)
            return ""
    else:
        print("Error, format is (key:value )+, missing \':\', Omitting param.", file=fh)
        return ""


def main():

    # check if help command
    if len(sys.argv) > 1 and sys.argv[1].lower() == "help":
        if len(sys.argv) > 2:
            if sys.argv[2].lower() == "get":
                print (printing_utils.print_help_get())
            elif sys.argv[2].lower() == "post":
                print (printing_utils.print_help_post())
        else:
            print (printing_utils.print_help())
    else:
        # httpc will be used normally
        # httpc (get|post|help (get|post)) [-v] (-h "k:v")* [-d inline-data] [-f file] URL
        parser = argparse.ArgumentParser()
        parser = argparse.ArgumentParser(conflict_handler='resolve')
        parser.add_argument("method", help="specify method (GET/POST)")
        parser.add_argument("-v", help="Verbose?", action='store_true')
        parser.add_argument("-h", metavar="\"k:v\"", nargs='+', dest="custom_headers", help="Add header parameter?")
        parser.add_argument("-d", metavar="inline-data", nargs='+', dest="inline_data", help="Add inline text?")
        parser.add_argument('-f', metavar="infile", dest="infile", help="Add body from file?",
                            type=argparse.FileType('r'))
        parser.add_argument('-o', metavar="outfile", dest="outfile", help="Output to a file?",
                            type=argparse.FileType('w'))
        '''parser.add_argument('-f', metavar="file", dest="file", help="Add body from file?", nargs='?',
                            type=argparse.FileType('r'), default=sys.stdin)'''
        parser.add_argument("URL", help="must input URL")
        args = parser.parse_args()

        # check if output file specified
        if args.outfile is not None:
            print ("Output will now be redirected to specified outfile...")
            fh = args.outfile
        else:
            fh = sys.stdout

        first = True
        headers = ""

        # validate custom header syntax if there were any specified (--h)
        if args.custom_headers is not None:
            print ("Processing Custom Headers (-h)...", file=fh)
            for cust_header in args.custom_headers:
                if first:
                    first = False
                    headers += validate_keyval_syntax(cust_header, fh)
                else:
                    headers += "~" + validate_keyval_syntax(cust_header, fh)

        if args.method.lower() == "get":

            # if method is get, ensure that nothing was specified for the -d or -f args
            if args.inline_data is not None or args.infile is not None:
                print ("inline-data or external file data should not be used with \'GET\'", file=fh)
            else:
                request_methods.get(args.URL, args.v, headers, fh)

        elif args.method.lower() == "post":
            key_val = ""

            # if method is post, ensure get or post specified but not both.
            if args.inline_data is not None and args.infile is None:
                # if attributes set, validate them and insert into dict collection
                print ("Processing Inline Data (-d)...", file=fh)
                for dat in args.inline_data:
                    if first:
                        first = False
                        key_val += validate_keyval_syntax(dat, fh)
                    else:
                        key_val += "~" + validate_keyval_syntax(dat, fh)

                print ("keyval: " + key_val, fh)
                request_methods.post(args.URL, args.v, headers, key_val, fh)

            elif args.infile is not None and args.inline_data is None:
                print ("Processing File (-f)...", file=fh)
                for line in args.infile.readlines():
                    print ("This is a line: " + line, file=fh)
                    if first:
                        first = False
                        key_val += validate_keyval_syntax(line, fh)
                    else:
                        key_val += "~" + validate_keyval_syntax(line, fh)

                print ("keyval: " + key_val, fh)
                request_methods.post(args.URL, args.v, headers, key_val, fh)

            else:
                print ("Error, \'POST\' must specify -d or -f, but not both.", file=fh)
        else:
            print ("Error, method must be either \'GET\' or \'POST\'.", file=fh)

        fh.close()


if __name__ == "__main__":
    main()
