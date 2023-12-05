import yaml
import os
import argparse
import datetime

def CreatePage(input, output):
    # Get the episode data
    with open(input, 'r', encoding='utf-8') as file:
        dataDict = yaml.safe_load(file)
        file.close()

    # Select the fields to be written to the FrontMatter section
    episodeDict = {
        'title': dataDict['title'],
        'id': dataDict['id'],
        'publishDate': datetime.datetime.strptime(dataDict['published'], "%Y-%m-%d").date(),
        'excerpt': dataDict['excerpt'],
        'youtubeid': dataDict['youtubeid'],
        'image': dataDict['image'],
        'draft': False,        
    }

    # Write the file
    pagesPath = os.path.join(output, dataDict['filename'] + '.md')
    print('Writing ' + pagesPath)
    with open(pagesPath, 'w', encoding='utf-8') as file:
        file.write('---\n')
        yaml.dump(episodeDict, file)
        file.write('---\n')
        # file.write("{{< show " + dataDict['id'] + " >}}\n")
        file.write(dataDict['shownotes'])
        file.close()

def CreatePages(input, output):
    with os.scandir(input) as episodes:
        for episode in episodes:
            if episode.name.endswith('.yaml') and episode.is_file():
                CreatePage(episode.path, output)

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input')
parser.add_argument('-o', '--output')
args = parser.parse_args()

CreatePages(args.input, args.output)
