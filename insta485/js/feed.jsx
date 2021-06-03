import React from 'react';
import PropTypes from 'prop-types';
import InfiniteScroll from 'react-infinite-scroll-component';
import Post from './post';

class Feed extends React.Component {
  constructor(props) {
    // Initialize mutable state
    super(props);
    this.state = {
      posts: [],
      nextPage: 0,
    };
    this.setPage = this.setPage.bind(this);
  }

  componentDidMount() {
    // This line automatically assigns this.props.url to the const variable url
    const { url } = this.props;
    const { posts } = this.state;

    // Call REST API to get number of likes
    fetch(url, { credentials: 'same-origin' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        if (data.next) {
          this.setState({
            posts: posts.concat(data.results),
            nextPage: data.next,
          });
        } else {
          this.setState({
            posts: posts.concat(data.results),
          });
        }
      })
      .catch((error) => console.log(error));
  }

  // Function for infinite scrolling logic needs some work
  // Url not set properly. We likely need to add a state variable for size
  // Gonna need to figure out how to parse that "next" string from rest api
  setPage() {
    const { nextPage, posts } = this.state;
    if (nextPage) {
      fetch(nextPage, { credentials: 'same-origin' })
        .then((response) => {
          if (!response.ok) throw Error(response.statusText);
          return response.json();
        })
        .then((data) => {
          console.log(data);
          this.setState({
            posts: posts.concat(data.results),
            nextPage: data.next,
          });
        })
        .catch((error) => console.log(error));
    }
  }

  render() {
    const { posts } = this.state;
    return (
      <div className="feed">
        <InfiniteScroll
          dataLength={posts.length}
          next={this.setPage}
          hasMore
        >
          {posts.map((post) => <Post url={post.url} key={post.postid} />)}
        </InfiniteScroll>
      </div>
    );
  }
}

Feed.propTypes = {
  url: PropTypes.string.isRequired,
};

export default Feed;
