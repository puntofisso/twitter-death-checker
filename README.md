twitter-death-checker
=====================

Automatically put people who don't tweet in a list (and unfollow); signal people from that list who resume tweeting (or
refollow)

The script is intended to be run server side, but here is shown as a command line script. 

Note:
- it counts 300 API calls, after which it goes to sleep for a hour (not particularly smart, just a silly workaround to Twitter API limits)
- you need to provide OAUTH key and secret
- authentication happens through a URL displayed on the command line (Twitter will return a PIN number you need to enter the first time you run the script)
- settings are stored in a config.py file, created on your first execution of the script.
- ideally, run the script within a python 2.6 virtualenv
- it requires json, urllib, urlparse, sys, time, datetime, oauth2

Any question, puntofisso_AT_gmail_DOT_com