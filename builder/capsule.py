import shutil, os, json
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

TRANSLATIONS = {
    "txt": "<p>%s</p>",
    "pdf": '<embed src="%s" type="application/pdf">',
    "mp3": '<audio controls><source src="%s"></audio>',
    "wav": '<audio controls><source src="%s"></audio>',
    "mp4": '<video controls><source src="%s"></video>',
    "mov": '<video controls><source src="%s"></video>',
    "png": '<img src="%s">',
    "jpg": '<img src="%s">',
    "jpeg": '<img src="%s">',
    "gif": '<img src="%s">',
    "webp": '<img src="%s">',
    "bmp": '<img src="%s">',
    "svg": '<img src="%s">',
    "tiff": '<img src="%s">',
}

def read_file(file):
    try:
        string = ""
        with open(file, "r") as text:
            for line in text:
                string += f"{line}\n"
        
        return string
    except:
        return "No file found."
    
def extract_metadata(file):
    data = {}
    
    try:
        image = Image.open(file)
        exif_data = image._getexif()

        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if type(value) == str:
                    data[tag] = value
    except:
        pass

    return data

def build_website(user, files, messages=None):
    # Establish path to file
    PATH = f"./capsules/{user}/"
    if not os.path.isdir(PATH): os.mkdir(PATH)

    # Copy base file
    shutil.copyfile("base.html", f"{PATH}/index.html")

    # Open new file
    new_file = open(f"{PATH}/index.html", "a")
    if not new_file:
        print("ERROR: FILE NOT FOUND.")
        return

    # Iterate through files
    for index, file in enumerate(files):
        data = extract_metadata(file) # Metadata
        ext = file.split(".")[-1].lower() # File extension

        html = f"<div data-metadata='{json.dumps(data)}'>{(TRANSLATIONS.get(ext, "<p>Unsupported file type.<br>%s</p>") % file)}<p>"
        if index < len(messages) and messages[index] != "":
            html += f"{messages[index]}"
        else:
            html += "&nbsp;" 

        html += "</p></div>"

        # Write to file
        try:
            new_file.write(html)
        except:
            new_file.write("<p>Error writing this HTML</p>")

    new_file.write("</div><script src='capsule.js'></script></body></html>")
    new_file.close()

    # Return path to website
    return PATH




fileList = [
    "images/Screenshot 2025-04-08 123806.png",
    "images/Screenshot 2025-04-08 124841.png",
    "images/Screenshot 2025-04-08 204241.png",
    "images/Screenshot 2025-04-08 204808.png",
    "images/Screenshot 2025-04-08 204959.png",
    "images/Screenshot 2025-04-29 204323.png",
    "images/image0.jpeg",
    "video.mp4",
    "COOP 30 Second Pitch.mov",
    "test.asd"
]



build_website("Xander", fileList, ["yes", "so beautiful", "this is a test for a realllyyyy long message i think users should be able to do this but like this needs to be hella long like reall yufkcing long becaused i have to test this", "", ""])