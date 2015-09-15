from xbmcswift2 import Plugin

import sys
import urllib
import urllib2
import json
import gzip
import StringIO

BASE_API_URL = 'http://api.azubu.tv/public'
BASE_STREAM_URL = 'https://edge.api.brightcove.com/playback/v1/accounts/3361910549001/videos/ref:'


plugin = Plugin()

def GetJSON(url,is_gzip,is_policy):
  request = urllib2.Request(url)
  if is_gzip: request.add_header('Accept-encoding', 'gzip')
  if is_policy: request.add_header('BCOV-Policy', 'BCpkADawqM1A0CwPyYtV8VTU1T_ObgxukCOGnqfrz2ypCNmBTdQ0ZHIRGI_-Snwe5VZ5fz5VGn9DIrKLwNsm-2bylBYbuXdWovgGRExPeytxXQ0NOK1onOiXhjBDBmSlrzSWVUWvYDSjYc1-')
  response = urllib2.urlopen(request)
  if is_gzip:
    buf = StringIO.StringIO(response.read())
    f = gzip.GzipFile(fileobj=buf)
    jsonDict = json.loads(f.read())
  else:
    jsonDict = json.loads(response.read())
  return jsonDict

def GetVideoURL(ref,find):
  videostream = GetJSON(BASE_STREAM_URL+ref,False,True)
  for source in videostream['sources']:
    if source.has_key('src'):
      streaming_src = source['src']
    elif source.has_key('streaming_src'):
      streaming_src = source['streaming_src']
    else:
      streaming_src = ''
    if find in streaming_src:
      return streaming_src
  return ''

def sort_by_viewers(d):
  if 'view_count' in d:
    return d['view_count']


@plugin.route('/')
def index():
  items = [
            {'label': 'Lives', 'path': plugin.url_for('list_lives')},
            {'label': 'Followings', 'path': plugin.url_for('list_followings')},
            {'label': 'Subscriptions', 'path': plugin.url_for('list_subscriptions')}
          ]
  return items

@plugin.route('/list/lives/')
def list_lives():
  items = []
  channels = GetJSON(BASE_API_URL+'/channel/live/list',True,False)
  if channels != []:
    channels = channels['data']
    for channel in sorted(channels, key=sort_by_viewers, reverse=True):
      user = channel['user']['username']
      img = channel['user']['profile']['url_photo_large']
      items.append({'label': user, 'icon': img, 'path': plugin.url_for('list_lives_by_user',user=user)})
  return items

@plugin.route('/list/lives/<user>/')
def list_lives_by_user(user):
  items = []
  videos = GetJSON(BASE_API_URL+'/modules/last-video/'+user+'/info',True,False)
  if videos != []:
    for video in videos:
      videos = videos['data']
      title = videos['title']
      img = videos['thumbnail']
      ref = videos['reference_id']
      videourl = GetVideoURL(ref,'master')
      items.append({'label': title, 'icon': img, 'path': videourl, 'is_playable': True})
  return items

@plugin.route('/list/followings/')
def list_followings():
  items = []
  configuser = plugin.get_setting('azubutv.username',str)
  if configuser == '':
    items.append({'label': 'Username not configured in settings!'})
  else:
    followings = GetJSON(BASE_API_URL+'/modules/user/'+configuser+'/followings/list',True,False)
    if followings != []:
      followings = followings['data']
      for following in sorted(followings, key=sort_by_viewers, reverse=True):
        user = following['user']['username']
        img = following['user']['profile']['url_photo_large']
        items.append({'label': user, 'icon': img, 'path': plugin.url_for('list_videos_by_user',user=user)})
  return items

@plugin.route('/list/subscriptions/')
def list_subscriptions():
  items = []
  configuser = plugin.get_setting('azubutv.username',str)
  if configuser == '':
    items.append({'label': 'Username not configured in settings!'})
  else:
    subscriptions = GetJSON(BASE_API_URL+'/modules/subscriptions/'+configuser,True,False)
    if subscriptions != []:
      subscriptions = subscriptions['data']
      for subscription in sorted(subscriptions, key=sort_by_viewers, reverse=True):
        user = subscription['user']['username']
        img = subscription['user']['profile']['url_photo_large']
        items.append({'label': user, 'icon': img, 'path': plugin.url_for('list_videos_by_user',user=user)})
  return items


@plugin.route('/list/videos/<user>/')
def list_videos_by_user(user):
  items = []
  limit = plugin.get_setting('azubutv.limit',int)
  videos = GetJSON(BASE_API_URL+'/video/list?orderBy={%22video.createdAt%22:%22desc%22}&features={%22lowereq%22:{%22user.username%22:%22'+user.lower()+'%22}}&limit='+str(limit),True,False)
  if videos != []:
    videos = videos['data']
    for video in videos:
      title = video['title']
      img = video['thumbnail']
      ref = video['reference_id']
      videourl = GetVideoURL(ref,'brightcove')
      items.append({'label': title, 'icon': img, 'path': videourl, 'is_playable': True})
  return items
  

if __name__ == '__main__':
    plugin.run()
