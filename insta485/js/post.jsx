import React from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';
import Likes from './likes';
import Comments from './comments';

class Post extends React.Component {
  constructor(props) {
    // Initialize mutable state
    super(props);
    this.state = {
      age: '',
      imgUrl: '',
      owner: '',
      ownerImgUrl: '',
      ownerShowUrl: '',
      postShowUrl: '',
      numLikes: 0,
      lognameHasLiked: 0,
      comments: [],
      text: '',
    };
    this.setLikes = this.setLikes.bind(this);
    this.handleLike = this.handleLike.bind(this);
    this.handleDoubleLike = this.handleDoubleLike.bind(this);

    this.setComments = this.setComments.bind(this);

    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleChange = this.handleChange.bind(this);
  }

  componentDidMount() {
    const { url } = this.props;
    fetch(url, { credentials: 'same-origin' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        this.setState({
          age: data.age,
          imgUrl: data.img_url,
          owner: data.owner,
          ownerImgUrl: data.owner_img_url,
          ownerShowUrl: data.owner_show_url,
          postShowUrl: data.post_show_url,
        });
      })
      .catch((error) => console.log(error));
  }

  setLikes(numLikes, lognameHasLiked) {
    this.setState({
      numLikes,
      lognameHasLiked,
    });
  }

  setComments(comments) {
    this.setState({
      comments,
    });
  }

  handleDoubleLike() {
    const { url } = this.props;
    const likesUrl = `${url}likes/`;
    const { lognameHasLiked } = this.state;
    let { numLikes } = this.state;
    if (!lognameHasLiked) {
      numLikes += 1;
    }
    if (!lognameHasLiked) {
      fetch(likesUrl, { method: 'POST', credentials: 'same-origin' });
      this.setState({
        lognameHasLiked: !lognameHasLiked,
        numLikes,
      });
    }
  }

  handleLike() {
    const { url } = this.props;
    const likesUrl = `${url}likes/`;
    const { lognameHasLiked, numLikes } = this.state;
    if (lognameHasLiked) {
      fetch(likesUrl, { method: 'DELETE', credentials: 'same-origin' });
      this.setState({
        lognameHasLiked: !lognameHasLiked,
        numLikes: numLikes - 1,
      });
    } else {
      fetch(likesUrl, { method: 'POST', credentials: 'same-origin' });
      this.setState({
        lognameHasLiked: !lognameHasLiked,
        numLikes: numLikes + 1,
      });
    }
  }

  handleChange(event) {
    this.setState({
      text: event.target.value,
    });
  }

  handleSubmit(event) {
    const { url } = this.props;
    const commentsUrl = `${url}comments/`;
    const { text } = this.state;
    const { comments } = this.state;
    // Call REST API to post comment
    // body: JSON.stringify({ title: 'React POST Request Example' })
    fetch(commentsUrl, {
      credentials: 'same-origin',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        this.setState({
          comments: comments.concat(data),
          text: '',
        });
      })
      .catch((error) => console.log(error));
    event.preventDefault();
  }

  render() {
    const {
      age,
      imgUrl,
      owner,
      ownerImgUrl,
      ownerShowUrl,
      postShowUrl,
      numLikes,
      lognameHasLiked,
      comments,
      text,
    } = this.state;
    const humanAge = moment({ age }).fromNow();
    const { url } = this.props;
    const avatarStyle = {
      width: '50px',
      height: '50px'
    };
    // Render comments
    return (
      
      <div className="posts">
        <div className = "postHead">
          <a href={ownerShowUrl}>
            <img src={ownerImgUrl} alt="awdeorio avi" style={avatarStyle}/>
            {' '}
            {owner}
          </a>
          <a href={postShowUrl}>
            {' '}
            {humanAge}
            {' '}
          </a>
        </div>
        <button type="button" onDoubleClick={this.handleDoubleLike}>
          <img src={imgUrl} alt="user post" />
        </button>
        <div className="likes">
          <Likes
            url={`${url}likes/`}
            numLikes={numLikes}
            lognameHasLiked={lognameHasLiked}
            handleLikes={this.handleLike}
            setLikes={this.setLikes}
          />
        </div>
        <div className="comments">
          <Comments
            url={`${url}comments/`}
            handleChange={this.handleChange}
            handleSubmit={this.handleSubmit}
            setComments={this.setComments}
            comments={comments}
            text={text}
          />
        </div>
      </div>
    );
  }
}

Post.propTypes = {
  url: PropTypes.string.isRequired,
};

export default Post;
