# This is a _very simple_ example of a web service that recognizes faces in uploaded images.
# Upload an image file and it will check if the image contains a picture of Barack Obama.
# The result is returned as json. For example:
#
# $ curl -F "file=@obama2.jpg" http://127.0.0.1:5001
#
# Returns:
#
# {
#  "face_found_in_image": true,
#  "is_picture_of_obama": true
# }
#
# This example is based on the Flask file upload example: http://flask.pocoo.org/docs/0.12/patterns/fileuploads/

# $ curl curl http://localhost:5001\?url\=https://scontent-lax3-1.cdninstagram.com/t51.2885-15/s320x320/e35/20687008_1639332866078302_2901096829007429632_n.jpg
#
# Returns:
#
# {
#   "count": 1,
#   "faces": [
#     {
#       "bottom": 138,
#       "left": 104,
#       "right": 179,
#       "top": 63
#     }
#   ],
#   "found": true,
#   "image": {
#     "height": 320,
#     "width": 320
#   }
# }

import face_recognition
from PIL import Image;
from flask import Flask, jsonify, make_response, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests;

# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__, static_url_path='')

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=['200 per day'],
    headers_enabled=True
)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def map_face_location(face_location):
    top, right, bottom, left = face_location;
    return {'top': top, 'right': right, 'bottom': bottom, 'left': left};

def detect_faces_in_image(file_stream):
    # Load the uploaded image file
    img = face_recognition.load_image_file(file_stream)
    # Get face encodings for any faces in the uploaded image
    face_locations = face_recognition.face_locations(img)

    pil_im = Image.fromarray(img)
    height, width = pil_im.size

    face_found = len(face_locations)

    if len(face_locations) > 0:
        face_found = True

    face_count = len(face_locations)

    face_locations = list(map(map_face_location, face_locations))

    # Return the result as json
    result = {
        "count": face_count,
        "found": face_found,
        "faces": face_locations,
        "image": { 'height': height, 'width': width }
    }
    return jsonify(result)

@app.route('/', methods=['GET'])
@limiter.exempt
def index():
    return app.send_static_file('index.html')

@app.route('/v1/faces', methods=['GET', 'POST'])
# @limiter.limit('100 per day')
@limiter.exempt
def detect_faces():
    # Check if url in query parameters
    if request.method == 'GET' and 'url' in request.args:
        url = request.args['url']
        response = requests.get(url, stream=True);
        return detect_faces_in_image(response.raw)

    # Check if a valid image file was uploaded
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        print(file)

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # The image file seems valid! Detect faces and return the result.
            return detect_faces_in_image(file)

@app.errorhandler(429)
def rate_limit_handler(e):
    return make_response(
        jsonify(error="ratelimit exceeded %s" % e.description)
        , 429
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
