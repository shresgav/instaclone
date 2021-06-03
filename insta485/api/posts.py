"""REST API for post paths."""
from flask import session
import flask
import insta485


@insta485.app.route("/api/v1/p/", methods=["GET"])
def get_posts():
    """Get all posts."""
    if 'username' not in session:
        send_context = {
            "message": "Forbidden",
            "status_code": "403"
        }
        return (flask.jsonify(**send_context)), 403

    # Query for postids and post urls
    connection = insta485.model.get_db()

    cur = connection.execute(
        "SELECT * "
        "FROM posts "
    )
    all_results = cur.fetchall()
    total_posts = len(all_results)

    size = flask.request.args.get("size", default=10, type=int)
    page = flask.request.args.get("page", default=0, type=int)
    if size < 0 or page < 0:
        context = {'message': 'Bad Request', 'status_code': 400}
        return flask.jsonify(**context)

    if len(all_results) > size:
        total_pages = ceil(total_posts / size) - 1
    else:
        total_pages = 0

    cur = connection.execute(
        "SELECT posts.postid, '/api/v1/p/' || postid || '/' as url "
        "FROM posts "
        "LEFT JOIN users ON users.username = posts.owner "
        "WHERE users.username IN "
        "(SELECT following.username2 FROM following "
        "WHERE following.username1 == ? "
        "UNION SELECT users.username FROM users "
        "WHERE users.username = ?) AND postid <= ? - ? * ? "
        "ORDER BY postid DESC LIMIT ?",
        (session['username'], session['username'],
         total_posts, page, size, size)
    )
    result = cur.fetchall()

    context = {'url': flask.request.path}

    if total_pages == 0 or page + 1 > total_pages:
        context['next'] = ''
    else:
        context['next'] = '/api/v1/p/?size='\
                        + str(size) + '&page=' + str(page + 1)

    if page > total_pages:
        context['results'] = []
    else:
        context['results'] = result

    return flask.jsonify(**context)


@insta485.app.route('/api/v1/p/<int:postid_url_slug>/', methods=["GET"])
def get_post(postid_url_slug):
    """Get post at postid_url_slug."""
    # Error check
    if 'username' not in session:
        error_context = {
            "message": "Forbidden",
            "status_code": "403"
        }
        return (flask.jsonify(**error_context)), 403
    # End error check

    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT posts.owner as owner, posts.created as age, "
        "posts.filename as img_url, users.filename as owner_img_url "
        "FROM posts "
        "LEFT JOIN users ON users.username = posts.owner "
        "LEFT JOIN likes ON likes.postid = posts.postid "
        "WHERE posts.postid = ? "
        "GROUP BY posts.postid", (postid_url_slug,)
    )
    post_info = cur.fetchone()
    # Error check
    if post_info is None:
        check_error_context = {
            "message": "Not Found",
            "status_code": "404"
        }
        return (flask.jsonify(**check_error_context)), 404
    # End error check

    img_url = '/uploads/' + post_info['img_url']
    owner_img_url = '/uploads/' + post_info['owner_img_url']
    owner_show_url = '/u/' + post_info['owner'] + '/'
    post_show_url = '/p/' + str(postid_url_slug) + '/'
    context = {
        'age': post_info['age'],
        'img_url': img_url,
        'owner': post_info['owner'],
        'owner_img_url': owner_img_url,
        'owner_show_url': owner_show_url,
        'post_show_url': post_show_url,
        'url': flask.request.path
    }
    return flask.jsonify(**context)


def ceil(num):
    """Return ceiling of num."""
    integer = int(num)
    if integer == num:
        return integer
    return integer + 1
