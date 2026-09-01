#-*- coding: utf-8 -*-

from update import parser_infinitas
from update import textdistance
from update import log
import iidxrank.models as models

# to make version FORCE
VERSION = -1

# should actually update record if test flag is off.
TEST = 0

# returns 1 if added
# returns 0 if not added(updated)
def update_song_by_object(song, do_add=True):
    
    if (VERSION >= 0):
        song['version'] = VERSION
    
    # if not exists, then add
    # if exists, then check level and title, then update. < 이미 있으면 업뎃 안하도록 해봄
    added = 0
    #print(type(song['title']))
    song_id = textdistance.CreateIntHashFromText(song['title'])
    song_title = song['title']
    version = str(song['version'])
    obj_song = models.Song.objects.filter(songid=song_id, songtype=song['diff']).first()
    if obj_song == None:
        if (do_add):
            if (song['notes'] == None):
                song['notes'] = 0

            if (TEST == 0):
                iidxme_id = 0
                if ('id' in song):
                    iidxme_id = song['id']

                obj_song = models.Song.objects.create(songtitle=song['title'],
                    songtype=song['diff'],
                    songid=song_id,
                    songid_iidxme=iidxme_id,
                    songlevel=song['level'],
                    songnotes=song['notes'],
                    version=song['version'],
                    calclevel_easy=0,
                    calcweight_easy=0,
                    calclevel_normal=0,
                    calcweight_normal=0,
                    calclevel_hd=0,
                    calcweight_hd=0,
                    calclevel_exh=0,
                    calcweight_exh=0)
            print("song %s/%s(%d) added (id %d)" % (song['title'], song['diff'], song['level'], song_id))
            added = 1
    #else:
    #    if (obj_song.songlevel != song['level'] or
    #            obj_song.version != version or
    #            obj_song.songtitle != song_title):
    #        log.Print("song %s(%d)/%s/%s (org: %s/%d/%s) updated" %
    #                (song_title, song['level'], song['diff'], version,
    #                obj_song.songtitle, obj_song.songlevel, obj_song.version))
    #        if (TEST == 0):
    #            obj_song.songlevel = song['level']
    #            obj_song.version = version
    #            obj_song.songtitle = song['title']
    #            obj_song.save()
    return (obj_song, added)

#
# update metadata of new songs from iidx.me
# TODO: we need to separate SPA/SPL, as updating is confusing.
#

#
# update new song from textage.cc
#

#
# update new song from textage.cc for infinitas
#
def update_from_infinitas(ver=-1):
    data = parser_infinitas.parse(ver)
    added_data_cnt = 0
    for song in data:
        obj, is_added = update_song_by_object(song)
        #log.Print(obj)
        #log.Print(song)
        #log.Print(data)
        added_data_cnt += is_added
    log.Print("added %d datas" % added_data_cnt)
