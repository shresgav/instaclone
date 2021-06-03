import React from 'react';
import PropTypes from 'prop-types';

class Comments extends React.Component {
  componentDidMount() {
    // This line automatically assigns this.props.url to the const variable url
    const { url, setComments } = this.props;

    // Call REST API to get number of likes
    fetch(url, { credentials: 'same-origin' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        const { comments } = data;
        setComments(comments);
      })
      .catch((error) => console.log(error));
  }

  render() {
    const {
      comments, handleSubmit, handleChange, text,
    } = this.props;
    // Render comments
    return (
      <div className="comments">
        {comments.map((comment) => (
          <div key={comment.commentid}>
            <a href={comment.owner_show_url}>{comment.owner}</a>
            <p>{comment.text}</p>
          </div>
        ))}
        <div>
          <form className="comment-form" onSubmit={handleSubmit}>
            <input type="text" value={text} onChange={handleChange} />
            <input type="submit" value="comment" />
          </form>
        </div>
      </div>
    );
  }
}

Comments.propTypes = {
  url: PropTypes.string.isRequired,
  setComments: PropTypes.func.isRequired,
  comments: PropTypes.arrayOf(PropTypes.object).isRequired,
  handleSubmit: PropTypes.func.isRequired,
  handleChange: PropTypes.func.isRequired,
  text: PropTypes.string.isRequired,
};

export default Comments;
