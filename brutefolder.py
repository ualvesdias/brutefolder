import threading as th
import queue
import argparse as ap
import sys

import requests as r
from requests.packages.urllib3.exceptions import InsecureRequestWarning
r.packages.urllib3.disable_warnings(InsecureRequestWarning)

def loadList(file):
    try:
        with open(file, 'r+') as wfile:
            listofwords = wfile.readlines()
    except FileNotFoundError as e:
        raise e

    wordqueue = queue.Queue()

    for word in listofwords:
        word = word.strip()
        wordqueue.put(word)
    return wordqueue


def bruter(wordqueue, extentions, url, show, hide):
    while not wordqueue.empty():
        attempt = wordqueue.get()
        attemptlist = []

        if '.' not in attempt:
            attemptlist.append('/%s/' % attempt)
        else:
            attemptlist.append('/%s' % attempt)

        if extentions:
            for ext in extentions:
                attemptlist.append('/%s.%s' % (attempt, ext))

        for item in attemptlist:
            testurl = url+item
            try:
                resp = r.get(testurl, verify=False, allow_redirects=False)
                status = resp.status_code
                print('[*] Trying %s%s' % (testurl,' '*20), end='\r', flush=True)
                if status == 200:
                    print('[+] ====>>>> %d ==> %s' % (status,testurl))
                    if 'Index of /' in resp.text:
                        print('[+] Directory listing is enabled for %s' % testurl)
                elif show and status in show:
                    print('[+] %d ==> %s' % (status,testurl))
                elif hide and status in hide:
                    pass
                elif status in {301, 302, 404}:
                    pass
                else:
                    print('[+] %d ==> %s' % (status,testurl))
            except KeyboardInterrupt:
                print('Task cancelled by the user...')
                exit(0)
            except Exception as e:
                print(e, 'Connection error...'+' '*20, end='\r', flush=True)

        wordqueue.task_done()

if __name__ == '__main__':
    parser = ap.ArgumentParser(description="Website folder/file finder.")
    parser.add_argument('-u', '--url', help='The URL to be brute forced.', required=True)
    parser.add_argument('-w', '--wordlist', help='The file containing the folders/files to test.', required=True)
    parser.add_argument('-t', '--threads', default=1, type=int, help='The number of threads to work with. Default is 1')
    parser.add_argument('-e', '--extensions', default=False, help='List the extentions to be tested, separated by comma.')
    codegroup = parser.add_mutually_exclusive_group()
    codegroup.add_argument('--show', default=False, help='The HTTP codes to be shown, separated by comma.')
    codegroup.add_argument('--hide', default=False, help='The HTTP codes to be excluded, separated by comma.')

    args = parser.parse_args()

    if not args.url.startswith('http'):
        args.url = 'http://'+args.url

    wordqueue = loadList(args.wordlist)
    
    hidecodes = False
    showcodes = False

    try:
        if args.extensions:
            exts = args.extensions.replace(' ','').split(',')
        else:
            exts = False

        if args.show:
            showcodes = set(args.show.replace(' ','').split(','))
        elif args.hide:
            hidecodes = set(args.hide.replace(' ','').split(','))
    except Exception as e:
        raise e

    for _ in range(args.threads):
        th.Thread(target=bruter, args=(wordqueue,exts,args.url, showcodes, hidecodes)).start()
