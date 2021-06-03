import React from 'react';
import PropTypes from 'prop-types';

class Likes extends React.Component {
  /* Display number of likes and like/unlike button for one post
   * Reference on forms https://facebook.github.io/react/docs/forms.html
   */

  componentDidMount() {
    // This line automatically assigns this.props.url to the const variable url
    const { url, setLikes } = this.props;

    // Call REST API to get number of likes
    fetch(url, { credentials: 'same-origin' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        const numLikes = data.likes_count;
        const lognameHasLiked = data.logname_likes_this;
        setLikes(numLikes, lognameHasLiked);
      })
      .catch((error) => console.log(error));
  }

  render() {
    // This line automatically assigns this.state.numLikes to the const variable numLikes
    const { numLikes, lognameHasLiked, handleLikes } = this.props;
    const likeText = (lognameHasLiked ? 'unlike' : 'like');
    // Render number of likes
    return (
      <div className="likes">
        <button type="button" className="like-unlike-button" onClick={handleLikes}>
          {likeText}
        </button>

        <p>
          {numLikes}
          {' '}
          like
          {numLikes !== 1 ? 's' : ''}
        </p>
      </div>
    );
  }
}

Likes.propTypes = {
  url: PropTypes.string.isRequired,
  handleLikes: PropTypes.func.isRequired,
  setLikes: PropTypes.func.isRequired,
  lognameHasLiked: PropTypes.oneOfType([PropTypes.bool, PropTypes.number]).isRequired,
  numLikes: PropTypes.number.isRequired,
};

export default Likes;
