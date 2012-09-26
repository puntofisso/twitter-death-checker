#!/usr/bin/env python
# The MIT License
# 
# Copyright (c) 2012 Giuseppe Sollazzo
# Copyright (c) 2010 Yu-Jie Lin
# Copyright (c) 2007 Leah Culver
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Create a config.py file at current directory with such content
# consumer_key = 'my_key_from_twitter'
# consumer_secret = 'my_secret_from_twitter'


import json
import urllib
import urlparse
import sys
import time, datetime
import oauth2 as oauth

global consumer
global client
global api_calls_counter

def wrong_config():

  global config
  class Config():
    pass
  config = Config()
  config.__dict__['consumer_key'] = raw_input('Consumer key? ')
  config.__dict__['consumer_secret'] = raw_input('Consumer secret? ')
  config.__dict__['max_survival_days'] = raw_input('Max survival days? ')
  config.__dict__['username'] = raw_input('Your username? ')
  config.__dict__['addtolist'] = raw_input('Add dead users to a list? y/n ')
  if config.addtolist == 'y':
    config.__dict__['listname'] = raw_input('Enter the list name ')
  config.__dict__['unfollow_deads'] = raw_input('Would you like to automatically unfollow dead users? y/n ')
  if config.addtolist == 'y':
    config.__dict__['refollow_resurrected'] = raw_input('Would you like to automatically refollow resurrected users? y/n ')

# Load oauth key, token and secret
try:
  import config
except ImportError:
  wrong_config()

if not hasattr(config, 'consumer_key') or not hasattr(config, 'consumer_secret'):
  wrong_config()

request_token_url = 'https://api.twitter.com/oauth/request_token'
access_token_url = 'https://api.twitter.com/oauth/access_token'
authorize_url = 'https://api.twitter.com/oauth/authorize'


def get_access_token(consumer):

  client = oauth.Client(consumer)

  resp, content = client.request(request_token_url, "GET")
  if resp['status'] != '200':
      raise Exception("Invalid response %s." % resp['status'])

  request_token = dict(urlparse.parse_qsl(content))


  print "[ACTION] Go to the following link in your browser:"
  print "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
  print 

  accepted = 'n'
  while accepted.lower() == 'n':
      accepted = raw_input('Have you authorized me? (y/n) ')
  oauth_verifier = raw_input('What is the PIN? ')

  token = oauth.Token(request_token['oauth_token'],
      request_token['oauth_token_secret'])
  token.set_verifier(oauth_verifier)
  client = oauth.Client(consumer, token)

  resp, content = client.request(access_token_url, "POST")
  access_token = dict(urlparse.parse_qsl(content))

  return access_token

def death_check():
    dead_users=[]
    global client
    global api_calls_counter
    # get and parse "following" list
    resp, content = client.request('https://api.twitter.com/1/friends/ids.json?cursor=-1&screen_name='+config.username)
    api_calls_counter = api_calls_counter + 1 # TODO replace with time?

    if api_calls_counter > 300:
        print "[WAIT] Waiting a hour before proceeding...\n"
        time.sleep(4200)
        print "[WAIT] Resuming now\n"
        api_calls_counter = 0


    # some very basic error management
    if resp['status'] not in ['200']:
        print "[ERROR] There was an error!\n"
        print resp
        print "\n"
        return

    ids_json = json.loads(content)
    ids = ids_json['ids']

    # get today's date
    today = time.strptime(time.asctime(time.localtime((time.time()))), '%a %b %d %H:%M:%S %Y')
    today = datetime.datetime.today()


    # cycle over each user
    for user in ids:
        latest_url = "https://api.twitter.com/1/users/show.json?user_id="+str(user)+"&include_entities=true"
        #latest_url = "https://api.twitter.com/1/statuses/user_timeline.json?include_entities=true&include_rts=true&user_id="+str(user)+"&count=1"
        print "[DEBUG] " + latest_url
        latest_resp, latest_cont = client.request(latest_url)
	api_calls_counter = api_calls_counter + 1
        latest_json = json.loads(latest_cont)
        created_at = latest_json['status']['created_at']
        handle = latest_json['screen_name']
        x = datetime.datetime.strptime(created_at,'%a %b %d %H:%M:%S +0000 %Y')
        print "[DEBUG] user: " + str(user) + " handle: @" + str(handle)+ " last tweet: " + str(x)
        survival = ((today-x).days)
        # check survival
        if survival > int(config.max_survival_days):
            dead_users.append(user)
        # as twitter allows only 350 calls per hour, if we do about 300 we stop
        # and wait a hour before proceeding
        if api_calls_counter > 300: # TODO replace with time?
            print "[WAIT] Waiting a hour before proceeding...\n"
            time.sleep(4200) 
            print "[WAIT] Resuming now\n"
            api_calls_counter = 0
    death_action(dead_users)


# this function describes what to do with the dead users
def death_action(dead_users):
    users= ','.join(map(str, dead_users)) 
    global api_calls_counter
    if users=="":
        print "[END] No users to be added\n"
        return
    else:
        print "[DEBUG] Going to add users to list...\n"
    if config.addtolist == 'y':
        print "[ADD TO LIST] "+config.listname+": " + str(users) + "\n"
        # POST request to twitter 
        response, content = client.request("https://api.twitter.com/1/lists/members/create_all.json", \
            method="POST", body=urllib.urlencode({'slug': config.listname, 'owner_screen_name': config.username, 'user_id': users}) )
        api_calls_counter = api_calls_counter + 1
        if api_calls_counter > 300: # TODO replace with time?
            print "[WAIT] Waiting a hour before proceeding...\n"
            time.sleep(4200)
            print "[WAIT] Resuming now\n"
            api_calls_counter = 0
    if config.unfollow_deads:
	# POST request to unfollow to twitter 
        for user in dead_users:
            response, content = client.request("http://api.twitter.com/1/friendships/destroy.json", \
                method="POST", body=urllib.urlencode({'user_id': user}) )
            print "[UNFOLLOW] " + str(user)
            api_calls_counter = api_calls_counter + 1
            if api_calls_counter > 300: # TODO replace with time?
                print "[WAIT] Waiting a hour before proceeding...\n"
                time.sleep(4200)
                print "[WAIT] Resuming now\n"
                api_calls_counter = 0
    else:
        print "[NOT UNFOLLOW] " + str(user) 

# this function describes what to do with the resurrected users
def resurrection_check():
    resurrected_users=[]
    global client
    global api_calls_counter
    # get and parse "following" list
    resp, content = client.request('https://api.twitter.com/1/lists/members.json?slug='+config.listname+'&owner_screen_name='+config.username+'&cursor=-1')
    api_calls_counter = api_calls_counter + 1 # TODO replace with time?

    if api_calls_counter > 300: # TODO replace with time?
        print "[WAIT] Waiting a hour before proceeding...\n"
        time.sleep(4200)
        print "[WAIT] Resuming now\n"
        api_calls_counter = 0
  
    # some very basic error management
    if resp['status'] not in ['200']:
        print "[ERROR] There was an error!\n"
        print resp
        print "\n"
        return

    users_json = json.loads(content)
    users = users_json['users']

    

    # get today's date
    today = time.strptime(time.asctime(time.localtime((time.time()))), '%a %b %d %H:%M:%S %Y')
    today = datetime.datetime.today()

 
    # cycle over each user
    for user in users:
        latest_id = user['id']
        latest_name = user['screen_name']
	# TODO it seems that sometimes user comes without "status", this is very weird (and potentially a bug in the API)
        try:
            created_at = user['status']['created_at']
        except:
            print "[DEBUG] we got a user without a status reported: " + user['screen_name']
            continue

        x = datetime.datetime.strptime(created_at,'%a %b %d %H:%M:%S +0000 %Y')
        survival = ((today-x).days)
        print "[DEBUG] user: " + str(latest_id) + " handle: @" + str(latest_name)+ " last tweet: " + str(x) + ", survival = " + str(survival)
        # check survival
        if survival <= int(config.max_survival_days):
            resurrected_users.append(latest_name)

    resurrection_action(resurrected_users)


def resurrection_action(users):
    global client
    global api_calls_counter
    if config.refollow_resurrected:
        for user in users:
            # refollow
            if user == config.username:
                continue
            resp, content = client.request("http://api.twitter.com/1.1/friendships/create.json", \
                method="POST", body=urllib.urlencode({'screen_name': user}) )
            api_calls_counter = api_calls_counter + 1 # TODO replace with time?

            if api_calls_counter > 300:
                print "[WAIT] Waiting a hour before proceeding...\n"
                time.sleep(4200)
                print "[WAIT] Resuming now\n"
                api_calls_counter = 0


            # some very basic error management
            if resp['status'] not in ['200']:
                print "[ERROR] There was an error!\n"
                print user
                print resp
                print "\n"
                return

            print "[REFOLLOW] " + user
    else:
        print "[DEBUG] You asked not to refollow users. However, here's the list of the resurrected ones: " + str(users)
        print "\n[DEBUG] They will still be removed from the list\n"

    #https://api.twitter.com/1.1/lists/members/destroy_all.json
    # remove from list
    resp, content = client.request("http://api.twitter.com/1.1/friendships/create.json", \
                method="POST", body=urllib.urlencode({'screen_name': user}) )
    userslist= ','.join(map(str, users))
    if userslist=="":
        print "[END] No users to be removed from list\n"
        return
    else:
        print "[DEBUG] Going to remove users to list...\n"
    if config.addtolist == 'y':
        print "[REMOVE FROM LIST] "+config.listname+": " + str(userslist) + "\n"
        # POST request to twitter to remove resurrected users from list
        response, content = client.request("https://api.twitter.com/1.1/lists/members/destroy_all.json", \
            method="POST", body=urllib.urlencode({'slug': config.listname, 'owner_screen_name': config.username, 'screen_name': userslist}) )
        api_calls_counter = api_calls_counter + 1
        if api_calls_counter > 300: # TODO replace with time?
            print "[WAIT] Waiting a hour before proceeding...\n"
            time.sleep(4200)
            print "[WAIT] Resuming now\n"
            api_calls_counter = 0 

def main():
    #https://api.twitter.com/1/lists/statuses.json?slug=the-disappeared&owner_screen_name=puntofisso
    global consumer
    global client
    global api_calls_counter
    
    api_calls_counter = 0

    consumer = oauth.Consumer(config.consumer_key, config.consumer_secret)

    # Check if we have access_token
    if not hasattr(config, 'access_token'):
        config.access_token = get_access_token(consumer)
        f = open('config.py', 'w')
        f.write('consumer_key = %s\n' % repr(config.consumer_key))
        f.write('consumer_secret = %s\n' % repr(config.consumer_secret))
        f.write('access_token = %s\n' % repr(config.access_token))
        f.write('max_survival_days = %s\n' % repr(config.max_survival_days))
        f.write('username = %s\n' % repr(config.username))
        f.write('addtolist = %s\n' % repr(config.addtolist))
        f.write('listname = %s\n' % repr(config.listname))
        f.write('unfollow_deads = %s\n' % repr(config.unfollow_deads))
        f.write('refollow_resurrected = %s\n' % repr(config.refollow_resurrected))
        f.close()
        print '[BOOT] config.py written.\n\n'

    token = oauth.Token(config.access_token['oauth_token'],
      config.access_token['oauth_token_secret'])
    client = oauth.Client(consumer, token)



    #death_check()
    resurrection_check()

if __name__ == '__main__':
  main()
