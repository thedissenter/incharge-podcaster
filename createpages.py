import os
import argparse
import datetime
import sys
import json
# import tscribe - No! No! Noooo! Very very sloooow!
import webvttUtils
from transcripttotext import transcriptToText

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def GeneratePage(episodepath, config):
    # Get the episode data
    with open(episodepath, 'r', encoding='utf-8') as file:
        dataDict = json.load(file)
        file.close()

    # Does the page need to be created or updated?
    pagepath = os.path.join(config['page-folder'], dataDict['filename'] + '.md')
    transcriptPath = os.path.join(config['episode-folder'], dataDict['episodeid'], 'transcript.json')
    vttpath = os.path.join(config['vtt-folder'], dataDict['episodeid'] + '.vtt')
    if os.path.exists(pagepath):
        # The page exists. Does it need to be updated?
        pageModified = os.path.getmtime(pagepath)
        # If either the episode data or transcript data has changed?
        dataModified = max(
            os.path.getmtime(transcriptPath) if os.path.exists(transcriptPath) else 0,
            os.path.getmtime(episodepath)
        )
        if dataModified > pageModified:
            writePage = 1   # The episode data has changed, so the page needs to be updated
        else:
            writePage = 0   # The episode data has not changed
    else:
        writePage = -1      # The episode data is new, so the page needs to be created

    if writePage:
        if os.path.exists(transcriptPath):
            print('Writing captions to ' + vttpath)
            # tscribe.write(transcriptPath, format="vtt", save_as=vttpath)
            webvttUtils.writeTranscriptToWebVTT(transcriptPath, 'en', vttpath)
            dataDict["vtt"] = dataDict['episodeid'] + '.vtt'

        if 'published' in dataDict:
            # Convert datetime to date
            # dataDict['publishDate'] = datetime.datetime.strptime(dataDict['published'], "%Y-%m-%d")
            dataDict['publishDate'] = dataDict["published"]
        if "spotifyAudioUrl" in dataDict:
            dataDict["audiourl"] = dataDict["spotifyAudioUrl"]

        print(('Creating' if writePage < 0 else 'Updating') + ' ' + pagepath)
        # Select fields to write to the FrontMatter section, if they exist for this episode
        episodeDict = { key: dataDict[key] for key in ('title', 'episodeid', 'publishDate', 'excerpt', 'youtubeid', 'audiourl', 'image', 'tags', 'itunesEpisodeUrl', 'spotifyEpisodeUrl', 'transcript', 'vtt') if key in dataDict }
        episodeDict['draft'] = False

        with open(pagepath, 'w', encoding='utf-8') as file:
            file.write('---\n')
            json.dump(episodeDict, file, indent='\t')
            file.write('\n---\n')

            # <div> tags require 2 line breaks, otherwise the next line's markup is not processed
            if not os.path.exists(transcriptPath):
                file.write('<div class="timelinks">\n\n')
                file.write(dataDict['shownotes'])
                file.write('</div>\n\n')
            else:
                file.write('<a name="top"></a>[Jump to transcript](#transcript)\n')
                file.write('## Show notes\n')
                file.write('<div class="timelinks">\n\n')
                file.write(dataDict['shownotes'])
                file.write('</div>\n\n')
                file.write('[Back to top](#top)\n')
                file.write('<a name="transcript"></a>\n')
                file.write('## Transcript\n')
                file.write('<div class="timelinks">\n\n')
                if 'transcript-disclaimer' in config:
                    file.write(config['transcript-disclaimer'])
                transcriptToText(transcriptPath, dataDict, config, file)
                file.write('</div>\n\n')
                file.write('[Back to top](#top)\n')

    return writePage

def GeneratePages(config):
    createdCount = 0
    updatedCount = 0

    print(f"Generating pages from {config['episode-folder']} to {config['page-folder']}")
    with os.scandir(config['episode-folder']) as episodes:
        for episode in episodes:
            episodepath = os.path.join(config['episode-folder'], episode.name, 'episode.json')
            # os.episode.name.endswith('.yaml')
            if os.path.exists(episodepath):
                writePage = GeneratePage(episodepath, config)
                if writePage < 0:
                    createdCount += 1
                elif writePage > 0:
                    updatedCount += 1
                # else: Unchanged
            else:
                print(f"WARNING: Missing episode file {episodepath}")
    if createdCount > 0:
        print(str(createdCount) + ' pages created' )
    if updatedCount > 0:
        print(str(updatedCount) + ' pages updated' )
    if createdCount == 0 and updatedCount == 0:
        print('No pages needed to be created or updated' )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--configfile')
    parser.add_argument('-x', '--ignore')
    args = parser.parse_args()

    configpath = args.configfile if args.configfile else 'incharge-podcaster.json'
    with open(configpath, mode='r', encoding='utf-8') as configfile:
        config = json.load(configfile)

    # Assign defaults if no folder settings are provided and convert relative to absolute paths
    config['episode-folder'] = os.path.abspath(
        config['episode-folder'] if 'episode-folder' in config else 'episode'
    )
    if not os.path.exists(config['episode-folder']):
        print(f"The episode folder does not exist: {config['episode-folder']}")
        return

    config['page-folder'] = os.path.abspath(
        config['page-folder'] if 'page-folder' in config else 'page'
    )
    if not os.path.exists(config['page-folder']):
        os.makedirs(config['page-folder'])

    config['vtt-folder'] = os.path.abspath(
        config['vtt-folder'] if 'vtt-folder' in config else 'vtt'
    )
    if not os.path.exists(config['vtt-folder']):
        os.makedirs(config['vtt-folder'])

    GeneratePages(config)

if __name__ == '__main__':
    main()