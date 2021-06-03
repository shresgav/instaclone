"""Get root api using flask."""
import flask
import insta485


@insta485.app.route('/api/v1/', methods=["GET"])
def get_api():
    """Get api root for website."""
    context = {
        "posts": "/api/v1/p/",
        "url": "/api/v1/"
    }
    return flask.jsonify(**context)
