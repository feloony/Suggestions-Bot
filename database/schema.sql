CREATE TABLE IF NOT EXISTS votes (
    message_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    vote_type SMALLINT NOT NULL,  -- 1 for upvote, -1 for downvote
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id, user_id)
);
