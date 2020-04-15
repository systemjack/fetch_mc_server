#!/usr/bin/env python

import os
import sys
import requests
import hashlib

# TODO: proper logging
# TODO: optional release param or latest snapshot
# TODO: optional symlink to update

versions = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest.json").json()

# {u'release': u'1.15.2', u'snapshot': u'20w15a'}
release = versions['latest']['release']
print "fetching current release: {}".format(release)

# {u'url': u'https://launchermeta.mojang.com/v1/packages/86add1e0b35aed5cf7dc0d60c4baadfb0e9e7bc7/1.15.2.json', u'releaseTime': u'2020-01-17T10:03:52+00:00', u'type': u'release', u'id': u'1.15.2', u'time': u'2020-03-18T16:49:45+00:00'}
url = None
for v in versions['versions']:
    if v['id'] == release:
        url = v['url']
        #print v
        break

if not url:
    print "error: not able to find url"
    sys.exit(1)

print "fetching version metadata: {}".format(url)
# curl 'https://launchermeta.mojang.com/v1/packages/86add1e0b35aed5cf7dc0d60c4baadfb0e9e7bc7/1.15.2.json' | python -m json.tool > meta_1.15.2.json
meta = requests.get(url).json()
server = meta['downloads']['server']

# server: {u'url': u'https://launcher.mojang.com/v1/objects/bb2b6b1aefcd70dfd1892149ac3a215f6c636b07/server.jar', u'sha1': u'bb2b6b1aefcd70dfd1892149ac3a215f6c636b07', u'size': 36175593}

dest = "{}_{}".format(release, server['url'].split('/')[-1])
print "downloading to: {}".format(dest)
# TODO: make idempotent so will not re-download same file to work as cron job
# https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
with requests.get(server['url'], stream=True) as r:
    r.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1000000): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                sys.stdout.write(".")
        sys.stdout.write("\n")
        #f.flush()

size = os.path.getsize(dest)
if size != server['size']:
    print "error: file size mismatch (needed: {}, got: {})".format(server['size'], size)
    os.remove(dest)
    sys.exit(1)
else:
    print "info: file size match (needed: {}, got: {})".format(server['size'], size)

# TODO: check sha1, else remove
batch = 65536
sha1 = hashlib.sha1()
with open(dest, 'rb') as f:
    while True:
        data = f.read(batch)
        if not data:
            break
        sha1.update(data)

if sha1.hexdigest() != server['sha1']:
    print "error: sha1 mismatch (needed: {}, got: {})".format(server['sha1'], sha1.hexdigest())
    os.remove(dest)
    sys.exit(1)
else:
    print "info: sha1 match (needed: {}, got: {})".format(server['sha1'], sha1.hexdigest())


# TODO: main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
