"""Get comments REST API."""
from flask import request, session
import flask
import insta485


@insta485.app.route('/api/v1/p/<int:postid_url_slug>/comments/',
                    methods=['GET', 'POST'])
def get_comments(postid_url_slug):
    """Get comments for post postid_url_slug."""
    # Error checking
    if 'username' not in session:
        error_check_context = {
            "message": "Forbidden",
            "status_code": "403"
        }
        return (flask.jsonify(**error_check_context)), 403

    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT * "
        "FROM posts "
        "WHERE postid = ? ",
        (postid_url_slug,)
    )
    error_check = cur.fetchall()
    if not error_check:
        error_check_context = {
            "message": "Not Found",
            "status_code": "404"
        }
        return (flask.jsonify(**error_check_context)), 404
    # End error check

    if request.method == 'GET':
        connection = insta485.model.get_db()
        cur = connection.execute(
            "SELECT owner, text, postid, commentid, "
            "'/u/' || owner || '/' as owner_show_url "
            "FROM comments "
            "WHERE postid = ?", (postid_url_slug,)
        )
        comments = cur.fetchall()
        context = {
            'comments': comments,
            'url': flask.request.path
        }
        return flask.jsonify(**context)
    # If post request
    text = request.json['text']
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT MAX(commentid) as id FROM comments"
    )
    new_comment_id = cur.fetchone()['id'] + 1

    context = {
        'commentid': new_comment_id,
        'owner': session['username'],
        'owner_show_url': "/u/" + session['username'] + "/",
        'postid': postid_url_slug,
        'text': text
    }

    connection.execute(
        "INSERT INTO comments (commentid, owner, postid, text) "
        "VALUES (?, ?, ?, ?)",
        (new_comment_id, session['username'], postid_url_slug, text)
    )

    return flask.jsonify(**context), 201
    # request.method == 'POST'
