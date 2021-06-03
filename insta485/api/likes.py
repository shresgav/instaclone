"""REST API for likes."""
from flask import request, session
import flask
import insta485


@insta485.app.route('/api/v1/p/<int:postid_url_slug>/likes/',
                    methods=["GET", "POST", "DELETE"])
def get_likes(postid_url_slug):
    """Return likes on postid."""
    # Error checking
    if 'username' not in session:
        context = {
            "message": "Forbidden",
            "status_code": "403"
        }
        return (flask.jsonify(**context)), 403

    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT * "
        "FROM posts "
        "WHERE postid = ? ", (postid_url_slug,)
    )
    error_check = cur.fetchall()
    if not error_check:
        context = {
            "message": "Not Found",
            "status_code": "404"
        }
        return (flask.jsonify(**context)), 404
    # End error check

    # Query database for post info and return context.
    if request.method == 'GET':
        # Find number likes
        connection = insta485.model.get_db()
        cur = connection.execute(
            "SELECT COUNT(likes.postid) as numLikes "
            "FROM likes "
            "WHERE likes.postid = ? "
            "GROUP BY likes.postid", (postid_url_slug,)
        )
        try:
            likes = cur.fetchone()['numLikes']
        except TypeError:
            likes = 0

        # Determine if session user has liked post
        cur = connection.execute(
            "SELECT COUNT(*) "
            "FROM likes "
            "WHERE owner = ? "
            "AND postid = ?", (session['username'], postid_url_slug)
        )
        logname_likes_this = 1 if cur.fetchone()['COUNT(*)'] else 0

    # Query database for post info and return context.
    if request.method == 'GET':
        # Find number likes
        connection = insta485.model.get_db()
        cur = connection.execute(
            "SELECT COUNT(likes.postid) as numLikes "
            "FROM likes "
            "WHERE likes.postid = ? "
            "GROUP BY likes.postid", (postid_url_slug,)
        )
        try:
            likes = cur.fetchone()['numLikes']
        except TypeError:
            likes = 0

        # Determine if session user has liked post
        cur = connection.execute(
            "SELECT COUNT(*) "
            "FROM likes "
            "WHERE owner = ? "
            "AND postid = ?", (session['username'], postid_url_slug)
        )
        logname_likes_this = 1 if cur.fetchone()['COUNT(*)'] else 0

        # Create context object and jsonify
        context = {
            "logname_likes_this": logname_likes_this,
            "likes_count": likes,
            "postid": postid_url_slug,
            "url": flask.request.path,
        }
        return flask.jsonify(**context)
    if flask.request.method == 'DELETE':
        connection = insta485.model.get_db()
        cur = connection.execute(
            "DELETE FROM likes "
            "WHERE postid = ? AND owner = ?",
            (postid_url_slug, session['username'])
        )
        return ('', 204)
    # HANDLING POST REQUEST
    connection = insta485.model.get_db()
    # Determine if session user has liked post
    cur = connection.execute(
        "SELECT COUNT(*) "
        "FROM likes "
        "WHERE owner = ? "
        "AND postid = ?", (session['username'], postid_url_slug)
    )
    logname_likes_this = 1 if cur.fetchone()['COUNT(*)'] else 0
    if not logname_likes_this:
        cur = connection.execute(
            "INSERT INTO likes (owner, postid) "
            "VALUES (?, ?)", (session['username'], postid_url_slug)
        )
        return ('', 201)
    context = {
        'logname': session['username'],
        'message': 'Conflict',
        'postid': postid_url_slug,
        'status_code': 409
    }
    return (flask.jsonify(**context)), 409
