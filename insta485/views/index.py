"""
Insta485 index and explore.

URLs include:
"""
import hashlib
import pathlib
import uuid
import arrow
from flask import render_template, url_for, request, \
    redirect, session, abort, send_from_directory
import flask
import insta485


# Helper functions
def encrypt_pass(unencrypted_password, salt):
    """Match password to database password."""
    algorithm = 'sha512'
    password_salted = salt + unencrypted_password
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    return password_db_string


@insta485.app.context_processor
def utility_processor():
    """Jinja needs help."""
    def humanize(timestamp):
        """Make timestamp great again."""
        local = arrow.get(timestamp)
        return local.humanize()

    def has_liked_post(postid):
        """Determine if session user has liked this post."""
        connection = insta485.model.get_db()
        cur = connection.execute(
            "SELECT COUNT(*) "
            "FROM likes "
            "WHERE owner = ? "
            "AND postid = ?", (session['username'], postid)
        )
        return cur.fetchone()["COUNT(*)"]

    def is_following(username):
        """Determine if session user is following this user."""
        connection = insta485.model.get_db()
        cur = connection.execute("SELECT COUNT(*) FROM following "
                                 "WHERE username1 = ? "
                                 "AND username2 = ? ",
                                 (session['username'], username)
                                 )
        return cur.fetchone()["COUNT(*)"]
    return dict(humanize=humanize,
                has_liked_post=has_liked_post,
                is_following=is_following)


@insta485.app.route('/uploads/<path:filename>')
def download_file(filename):
    """URL retrieves file from upload folder."""
    if 'username' not in session:
        abort(403)
    return send_from_directory(insta485.app.config['UPLOAD_FOLDER'],
                               filename, as_attachment=True)


def logname_follows_username(username):
    """Temporary logname function."""
    connection = insta485.model.get_db()
    cur = connection.execute("SELECT COUNT(*) FROM following "
                             "WHERE username1 = ? "
                             "AND username2 = ? ",
                             (session['username'], username)
                             )
    return cur.fetchone()["COUNT(*)"]


def username_exists(username):
    """Check if username exists."""
    connection = insta485.model.get_db()
    # Check if username exists
    cur = connection.execute(
        "SELECT username "
        "FROM users WHERE username == ?", (username,)
    )
    db_username = cur.fetchone()
    if not db_username:
        return False
    return True


def get_post_info(postid):
    """Query database for post info and return context."""
    connection = insta485.model.get_db()
    cur = connection.execute(
        "SELECT posts.owner, posts.postid, posts.created, "
        "COUNT(likes.postid) as likes, "
        "posts.filename as p_file, users.filename as u_file "
        "FROM posts "
        "LEFT JOIN users ON users.username = posts.owner "
        "LEFT JOIN likes ON likes.postid = posts.postid "
        "WHERE posts.postid = ? "
        "GROUP BY posts.postid", (postid,)
    )
    posts = cur.fetchall()
    cur = connection.execute(
        "SELECT owner, text, postid, commentid "
        "FROM comments "
        "ORDER BY commentid "
    )
    comments = cur.fetchall()

    context = {'posts': posts, 'comments': comments,
               'logname': session["username"]}
    return context


def unfollow(to_unfollow):
    """Unfollow username."""
    # import pdb; pdb.set_trace()
    connection = insta485.model.get_db()
    connection.execute("DELETE FROM following "
                       "WHERE username1 = ? "
                       "AND username2 = ? ",
                       (session['username'], to_unfollow)
                       )


def follow(to_follow):
    """Follow username."""
    # import pdb; pdb.set_trace()
    connection = insta485.model.get_db()
    connection.execute("INSERT INTO following (username1, username2) "
                       "VALUES (?,?) ", (session['username'], to_follow)
                       )


# Index route and misc
@insta485.app.route('/', methods=['POST', 'GET'])
def show_index():
    """Display / route."""
    if 'username' not in session:
        return redirect(url_for("login"))
    if request.method == 'GET':
        # Connect to database
        connection = insta485.model.get_db()

        # Query database
        cur = connection.execute(
            "SELECT posts.owner, posts.postid, posts.created, "
            "COUNT(likes.postid) as likes, "
            "posts.filename as p_file, users.filename as u_file "
            "FROM posts "
            "LEFT JOIN users ON users.username = posts.owner "
            "LEFT JOIN likes ON likes.postid = posts.postid "
            "WHERE users.username IN "
            "(SELECT following.username2 FROM following "
            "WHERE following.username1 == ? "
            "UNION SELECT users.username FROM users "
            "WHERE users.username = ?) "
            "GROUP BY posts.postid", (session['username'], session['username'])
        )
        posts = cur.fetchall()

        cur = connection.execute(
            "SELECT owner, text, postid, commentid "
            "FROM comments "
            "ORDER BY commentid "
        )
        comments = cur.fetchall()
        # Add database info to context
        context = {'posts': posts, 'comments': comments,
                   'logname': session['username']}
        return flask.render_template("index.html", **context)
    if 'username' in session:
        if 'comment' in request.form:
            comment = request.form['text']
            postid = request.form['postid']
            # Connect to database
            connection = insta485.model.get_db()
            # Query database
            cur = connection.execute(
                "INSERT INTO comments (owner, postid, text) "
                "VALUES (?, ?, ?)", (session['username'], postid, comment)
            )
        if 'like' in request.form:
            postid = request.form['postid']
            # Connect to database
            connection = insta485.model.get_db()
            # Query database
            cur = connection.execute(
                "INSERT INTO likes (owner, postid) "
                "VALUES (?, ?)", (session['username'], postid)
            )
        if 'unlike' in request.form:
            postid = request.form['postid']
            # Connect to database
            connection = insta485.model.get_db()
            # Query database
            cur = connection.execute(
                "DELETE FROM likes "
                "WHERE owner = ? "
                "AND postid = ? ", (session['username'], postid)
            )
        return redirect(url_for("show_index"))
    return None


@insta485.app.route('/explore/', methods=['GET', 'POST'])
def explore():
    """Route for explore page."""
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'follow' in request.form:
            to_follow_user = request.form['username']
            follow(to_follow_user)

    # Connect to database
    connection = insta485.model.get_db()
    # Query database
    cur = connection.execute(
        "SELECT username, filename "
        "FROM users "
        "WHERE username NOT IN "
        "(SELECT following.username2 FROM following "
        "WHERE following.username1 == ? "
        "UNION SELECT users.username FROM users "
        "WHERE users.username = ?) ",
        (session['username'], session['username'])
    )
    users = cur.fetchall()
    context = {'users': users, 'logname': session['username']}
    return render_template('explore.html', **context)


@insta485.app.route('/p/<int:postid>/', methods=['POST', 'GET'])
def post(postid):
    """Display /p/<postid>/ route."""
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Request for deleting post
        if 'delete' in request.form:
            # Query database for post owner
            connection = insta485.model.get_db()
            cur = connection.execute(
                "SELECT owner, filename "
                "FROM posts "
                "WHERE postid = ?", (postid,)
            )
            posts = cur.fetchone()
            # Delete from da filesystem
            img_path = insta485.app.config['UPLOAD_FOLDER'] / posts['filename']
            img_path.unlink()
            # Delete da post
            if posts['owner'] == session['username']:
                connection.execute(
                    "DELETE FROM posts "
                    "WHERE postid = ?", (postid,)
                )
            else:
                abort(403)
            return redirect(url_for('user_page', username=posts['owner']))

        # Post request for deleting comment
        if 'uncomment' in request.form:
            # Query database for comment owner
            connection = insta485.model.get_db()
            cur = connection.execute(
                "SELECT owner "
                "FROM comments "
                "WHERE commentid = ?", (request.form['commentid'],)
            )
            comment = cur.fetchone()
            if comment['owner'] == session['username']:
                connection.execute(
                    "DELETE FROM comments "
                    "WHERE commentid = ?", (request.form['commentid'],)
                )
            context = get_post_info(postid)

        # Post request for adding comment
        if 'comment' in request.form:
            comment = request.form['text']
            postid = request.form['postid']
            # Connect to database
            connection = insta485.model.get_db()
            # Query database
            cur = connection.execute(
                "INSERT INTO comments (owner, postid, text) "
                "VALUES (?, ?, ?)", (session['username'], postid, comment)
            )
            context = get_post_info(postid)

        # Post request for liking post
        if 'like' in request.form:
            # Connect to database
            connection = insta485.model.get_db()
            # Query database
            cur = connection.execute(
                "INSERT INTO likes (owner, postid) "
                "VALUES (?, ?)", (session['username'], postid)
            )
            context = get_post_info(postid)

        # Post request for liking post
        if 'unlike' in request.form:
            # Connect to database
            connection = insta485.model.get_db()
            # Query database
            cur = connection.execute(
                "DELETE FROM likes "
                "WHERE owner = ? "
                "AND postid = ? ", (session['username'], postid)
            )
            context = get_post_info(postid)
        return flask.render_template('post.html', **context)

    context = get_post_info(postid)
    return flask.render_template("post.html", **context)


# User routes
@insta485.app.route('/u/<username>/following/', methods=['GET', 'POST'])
def following(username):
    """Display following page."""
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'follow' in request.form:
            to_follow_user = request.form['username']
            follow(to_follow_user)
        elif 'unfollow' in request.form:
            to_unfollow_user = request.form['username']
            unfollow(to_unfollow_user)

    elif request.method == 'GET':
        if not username_exists(username):
            abort(404)

    connection = insta485.model.get_db()
    cur = connection.execute("SELECT following.username2 as username, "
                             "users.filename as user_img_url "
                             "FROM following "
                             "INNER JOIN users ON "
                             "users.username = following.username2 "
                             "WHERE username1 = ? ", (username,)
                             )
    following_data = cur.fetchall()
    context = {'following': following_data, 'logname': session['username'],
               'current_username': username}
    return flask.render_template("following.html", **context)


@insta485.app.route('/u/<username>/followers/', methods=['GET', 'POST'])
def followers(username):
    """Display followers page."""
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'follow' in request.form:
            to_follow_user = request.form['username']
            follow(to_follow_user)
        elif 'unfollow' in request.form:
            to_unfollow_user = request.form['username']
            unfollow(to_unfollow_user)

    elif request.method == 'GET':
        if not username_exists(username):
            abort(404)

    connection = insta485.model.get_db()
    cur = connection.execute("SELECT following.username1 as username, "
                             "users.filename as user_img_url "
                             "FROM following "
                             "INNER JOIN users ON "
                             "users.username = following.username1 "
                             "WHERE username2 = ? ", (username,)
                             )

    followers_data = cur.fetchall()
    context = {'followers': followers_data, 'logname': session['username'],
               'current_username': username}

    return flask.render_template("followers.html", **context)


@insta485.app.route('/u/<username>/', methods=['POST', 'GET'])
def user_page(username):
    """Display /u/<username>/ route."""
    connection = insta485.model.get_db()
    if 'username' not in session:
        return redirect(url_for('login'))
    if not username_exists(username):
        abort(404)
    if request.method == 'POST':
        if 'create_post' in request.form:
            # update DBs and to add new img to web app
            # Unpack flask object
            fileobj = flask.request.files["file"]
            filename = fileobj.filename
            uuid_basename = "{stem}{suffix}".format(
                stem=uuid.uuid4().hex,
                suffix=pathlib.Path(filename).suffix
            )

            # Save to disk
            fileobj.save(insta485.app.config["UPLOAD_FOLDER"] / uuid_basename)
            cur = connection.execute("SELECT postid from posts "
                                     "ORDER BY postid DESC LIMIT 1;")
            try:
                largest_postid = cur.fetchone()['postid']
            except TypeError:
                largest_postid = 0
            new_postid = str(largest_postid + 1)
            connection.execute("INSERT INTO posts (postid, filename, owner) "
                               "VALUES (?, ?, ?) ",
                               (new_postid, uuid_basename, session['username'])
                               )
        elif 'unfollow' in request.form:
            unfollow(request.form['username'])
        elif 'follow' in request.form:
            follow(request.form['username'])

    cur = connection.execute("SELECT COUNT(*) FROM following "
                             "WHERE username1 = ? ", (username,)
                             )
    num_following = cur.fetchone()["COUNT(*)"]
    cur = connection.execute("SELECT COUNT(*) FROM following "
                             "WHERE username2 = ? ", (username,)
                             )
    num_followers = cur.fetchone()["COUNT(*)"]
    log_name_follows_username = logname_follows_username(username)
    cur = connection.execute("SELECT COUNT(*) FROM posts "
                             "WHERE owner = ? ", (username,)
                             )
    total_posts = cur.fetchone()["COUNT(*)"]
    cur = connection.execute("SELECT fullname FROM users "
                             "WHERE username = ?; ", (username,)
                             )
    fullname = cur.fetchone()["fullname"]
    cur = connection.execute("SELECT postid, filename "
                             "FROM posts WHERE owner = ? ", (username,)
                             )
    posts = cur.fetchall()

    context = {'logname': session['username'], 'username': username,
               'following': num_following, 'followers': num_followers,
               'logname_follows_username': log_name_follows_username,
               'total_posts': total_posts, 'fullname': fullname,
               'posts': posts}
    return flask.render_template("user.html", **context)


# Account routes
@insta485.app.route('/accounts/login/', methods=['POST', 'GET'])
def login():
    """Display /accounts/login/ route."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to database
        connection = insta485.model.get_db()

        # Query database
        cur = connection.execute(
            "SELECT password "
            "FROM users WHERE username == ?", (username,)
        )
        db_password = cur.fetchone()
        if db_password:
            # Encrypt password
            salt = db_password['password'][7:39]
            password_db_string = encrypt_pass(password, salt)
            if db_password['password'] == password_db_string:
                session["username"] = username
                return redirect(url_for('show_index'))
            abort(403)
        abort(403)
        return None
    if 'username' in session:
        return redirect(url_for('show_index'))
    return flask.render_template('login.html')


@insta485.app.route('/accounts/logout/', methods=['POST'])
def logout():
    """Logout user."""
    session.pop('username', None)
    return redirect(url_for("login"))


@insta485.app.route('/accounts/create/', methods=['POST', 'GET'])
def create():
    """Route to create user."""
    if 'username' in session:
        return redirect(url_for("edit"))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['fullname']
        email = request.form['email']
        if not password:
            abort(400)

        # Encrypt password
        salt = uuid.uuid4().hex
        password_db_string = encrypt_pass(password, salt)

        # Unpack flask object
        fileobj = flask.request.files["file"]
        filename = fileobj.filename

        uuid_basename = "{stem}{suffix}".format(
            stem=uuid.uuid4().hex,
            suffix=pathlib.Path(filename).suffix
        )

        # Save to disk
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(path)

        # Connect to database
        connection = insta485.model.get_db()

        # Check if username exists
        cur = connection.execute(
            "SELECT username "
            "FROM users WHERE username == ?", (username,)
        )
        db_username = cur.fetchone()

        if not db_username:
            # Insert user into database
            connection.execute(
                "INSERT INTO users "
                "(username, fullname, email, filename, password) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, fullname, email, uuid_basename, password_db_string)
            )
            session["username"] = username
            return redirect(url_for("show_index"))
        abort(409)
    return flask.render_template('create.html')


@insta485.app.route('/accounts/delete/', methods=['POST', 'GET'])
def delete():
    """Delete user from database."""
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = session["username"]

        connection = insta485.model.get_db()
        # Get filenames to delete from database
        cur = connection.execute(
            "SELECT filename "
            "FROM users WHERE username = ? "
            "UNION SELECT filename "
            "FROM posts "
            "WHERE owner = ?", (session['username'], session['username'])
        )
        f_names = cur.fetchall()
        # Delete files
        for value, key in enumerate(f_names):
            filename = f_names[value]['filename']
            filename = key['filename']
            img_path = insta485.app.config['UPLOAD_FOLDER'] / filename
            img_path.unlink()

        connection.execute(
            "DELETE FROM users "
            "WHERE username=? ", (username,)
        )
        session.pop('username', None)

        return redirect(url_for("create"))
    context = {'logname': session["username"]}
    return flask.render_template('delete.html', **context)


@insta485.app.route('/accounts/edit/', methods=['POST', 'GET'])
def edit():
    """Route to edit user profile."""
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']

        username = session["username"]

        connection = insta485.model.get_db()

        connection.execute(
            "UPDATE users "
            "SET fullname=?, email=? "
            "WHERE username=? ", (fullname, email, username)
        )

        # update with file if one is given, otherwise nothing
        fileobj = flask.request.files["file"]
        if fileobj:
            # Unpack flask object
            filename = fileobj.filename

            uuid_basename = "{stem}{suffix}".format(
                stem=uuid.uuid4().hex,
                suffix=pathlib.Path(filename).suffix
            )

            # Save to disk
            path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
            fileobj.save(path)

            connection.execute(
                "UPDATE users "
                "SET filename=? "
                "WHERE username=? ", (uuid_basename, username)
            )
        else:
            pass

        cur = connection.execute(
            "SELECT users.fullname, users.email "
            "FROM users "
            "WHERE username=? ", (session["username"],)
        )
        context = cur.fetchone()
        context['logname'] = session["username"]
        return flask.render_template('edit.html', **context)

    connection = insta485.model.get_db()

    cur = connection.execute(
        "SELECT users.fullname, users.email "
        "FROM users "
        "WHERE username=? ", (session["username"],)
    )
    context = cur.fetchone()
    context['logname'] = session["username"]
    return flask.render_template('edit.html', **context)


@insta485.app.route('/accounts/password/', methods=['POST', 'GET'])
def account_password():
    """Route to edit password."""
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = session["username"]
        password = request.form['password']
        new_password1 = request.form['new_password1']
        new_password2 = request.form['new_password2']

        # Connect to database
        connection = insta485.model.get_db()

        # Query database
        cur = connection.execute(
            "SELECT password "
            "FROM users WHERE username == ?", (username,)
        )

        db_password = cur.fetchone()
        if db_password:
            # Encrypt password
            salt = db_password['password'][7:39]
            password_db_string = encrypt_pass(password, salt)
            if db_password['password'] == password_db_string:
                if new_password1 == new_password2:
                    # Change password to either (hashed)
                    salt = uuid.uuid4().hex
                    new_password = encrypt_pass(new_password1, salt)

                    connection.execute(
                        "UPDATE users "
                        "SET password=? "
                        "WHERE username=? ", (new_password, username)
                    )
                    # redirect to accounts/edit/
                    # because the change was successful
                    return redirect(url_for("edit"))
                abort(401)
            else:
                abort(403)
        else:
            abort(403)
        return None
    context = {'logname': session["username"]}
    return flask.render_template('password.html', **context)
