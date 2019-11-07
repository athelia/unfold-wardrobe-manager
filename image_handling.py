"""Functions and global variables related to file (image) handling."""

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return ('.' in filename and 
        filename.rsplit('.',1)[-1].lower() in ALLOWED_EXTENSIONS)
