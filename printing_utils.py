
def print_help():
    return ("   httpc is a curl-like application but supports HTTP protocol only."
            "\n   Usage:"
            "\n       httpc command URL [arguments]"
            "\n   The commands are:"
            "\n       get executes a HTTP GET request and prints the response."
            "\n       post executes a HTTP POST request and prints the response."
            "\n       help prints this screen."
            "\n   Use \"httpc help [command]\" for more information about a command.")


def print_help_get():
    return ("   usage: httpc get URL [-v] [-h key:value]\n"
            "   Get executes a HTTP GET request for a given URL."
            "\n     -v Prints the detail of the response such as protocol, status, and headers."
            "\n     -h key:value Associates headers to HTTP Request with the format \'key:value\'.")


def print_help_post():
    return ("   usage: httpc post [-v] [-h key:value] [-d inline-data] [-f file] URL"
            "\n   Post executes a HTTP POST request for a given URL with inline data or from file."
            "\n      -v Prints the detail of the response such as protocol, status, and headers."
            "\n      -h key:value Associates headers to HTTP Request with the format 'key:value'."
            "\n      -d string Associates an inline data to the body HTTP POST request."
            "\n      -f file Associates the content of a file to the body HTTP POST request."
            "\n   Either [-d] or [-f] can be used but not both.")
