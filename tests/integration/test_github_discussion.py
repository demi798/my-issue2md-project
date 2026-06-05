"""GitHub Discussion 集成测试"""


import pytest
from requests_mock import Mocker as requests_mock

from issue2md.core.github import fetch
from issue2md.errors import GithubAPIError
from issue2md.models.discussion import DiscussionData
from issue2md.models.resource import ResourceRef, ResourceType


def test_fetch_discussion_success(requests_mock: requests_mock):
    """测试获取 Discussion 成功"""
    graphql_response = {
        "data": {
            "repository": {
                "discussion": {
                    "title": "Test Discussion",
                    "body": "This is a test discussion body",
                    "author": {"login": "octocat"},
                    "createdAt": "2023-01-02T03:04:05Z",
                    "updatedAt": "2023-06-01T07:08:09Z",
                    "category": {"name": "General"},
                    "labels": {"nodes": [{"name": "help wanted", "color": "0075ca"}]},
                    "comments": {
                        "nodes": [
                            {
                                "author": {"login": "user1"},
                                "body": "Comment 1",
                                "createdAt": "2023-01-02T04:00:00Z",
                            },
                            {
                                "author": {"login": "user2"},
                                "body": "Comment 2",
                                "createdAt": "2023-01-02T05:00:00Z",
                            },
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                    "answerChosen": False,
                }
            }
        }
    }

    requests_mock.post("https://api.github.com/graphql", json=graphql_response)

    ref = ResourceRef("octocat", "Hello-World", ResourceType.DISCUSSION, 1)
    data = fetch(ref, token=None)

    assert isinstance(data, DiscussionData)
    assert data.title == "Test Discussion"
    assert data.body == "This is a test discussion body"
    assert data.author == "octocat"
    assert data.category == "General"
    assert data.answer_chosen is False
    assert data.comments_count == 2
    assert len(data.labels) == 1
    assert data.labels[0].name == "help wanted"
    assert len(data.comments) == 2
    assert data.comments[0].author == "user1"
    assert data.comments[0].body == "Comment 1"
    assert data.comments[1].author == "user2"
    assert data.comments[1].body == "Comment 2"


def test_fetch_discussion_with_category(requests_mock: requests_mock):
    """测试 Discussion category 字段"""
    graphql_response = {
        "data": {
            "repository": {
                "discussion": {
                    "title": "Feature Request",
                    "body": "I would like to suggest a new feature",
                    "author": {"login": "featureuser"},
                    "createdAt": "2023-01-02T03:04:05Z",
                    "updatedAt": "2023-06-01T07:08:09Z",
                    "category": {"name": "Ideas"},
                    "labels": {"nodes": []},
                    "comments": {
                        "nodes": [],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                    "answerChosen": False,
                }
            }
        }
    }

    requests_mock.post("https://api.github.com/graphql", json=graphql_response)

    ref = ResourceRef("featureuser", "repo", ResourceType.DISCUSSION, 100)
    data = fetch(ref, token=None)

    assert data.category == "Ideas"


def test_fetch_discussion_recursive_paging(requests_mock: requests_mock):
    """测试 Discussion 递归翻页"""
    first_page_response = {
        "data": {
            "repository": {
                "discussion": {
                    "title": "Long Discussion",
                    "body": "A discussion with many comments",
                    "author": {"login": "testuser"},
                    "createdAt": "2023-01-02T03:04:05Z",
                    "updatedAt": "2023-06-01T07:08:09Z",
                    "category": {"name": "Q&A"},
                    "labels": {"nodes": []},
                    "comments": {
                        "nodes": [
                            {
                                "author": {"login": "user1"},
                                "body": "Comment 1",
                                "createdAt": "2023-01-02T04:00:00Z",
                            },
                            {
                                "author": {"login": "user2"},
                                "body": "Comment 2",
                                "createdAt": "2023-01-02T05:00:00Z",
                            },
                        ],
                        "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                    },
                    "answerChosen": False,
                }
            }
        }
    }

    second_page_response = {
        "data": {
            "repository": {
                "discussion": {
                    "title": "Long Discussion",
                    "body": "A discussion with many comments",
                    "author": {"login": "testuser"},
                    "createdAt": "2023-01-02T03:04:05Z",
                    "updatedAt": "2023-06-01T07:08:09Z",
                    "category": {"name": "Q&A"},
                    "labels": {"nodes": []},
                    "comments": {
                        "nodes": [
                            {
                                "author": {"login": "user3"},
                                "body": "Comment 3",
                                "createdAt": "2023-01-02T06:00:00Z",
                            },
                            {
                                "author": {"login": "user4"},
                                "body": "Comment 4",
                                "createdAt": "2023-01-02T07:00:00Z",
                            },
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                    "answerChosen": False,
                }
            }
        }
    }

    requests_mock.post(
        "https://api.github.com/graphql",
        [{"json": first_page_response}, {"json": second_page_response}],
    )

    ref = ResourceRef("testuser", "repo", ResourceType.DISCUSSION, 50)
    data = fetch(ref, token=None)

    assert data.comments_count == 4
    assert len(data.comments) == 4
    assert data.comments[0].author == "user1"
    assert data.comments[1].author == "user2"
    assert data.comments[2].author == "user3"
    assert data.comments[3].author == "user4"


def test_fetch_discussion_not_found(requests_mock: requests_mock):
    """测试 Discussion 不存在时的错误处理"""
    error_response = {
        "data": {"repository": {"discussion": None}},
        "errors": [
            {
                "message": "Could not resolve to a Discussion with the number '999'.",
                "type": "NOT_FOUND",
            }
        ],
    }

    requests_mock.post("https://api.github.com/graphql", json=error_response)

    ref = ResourceRef("nonexistent", "repo", ResourceType.DISCUSSION, 999)

    with pytest.raises(GithubAPIError) as exc_info:
        fetch(ref, token=None)

    assert "not found" in str(exc_info.value).lower() or "enabled" in str(exc_info.value).lower()
