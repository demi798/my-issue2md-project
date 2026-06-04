"""pytest 配置和共享 fixtures"""

import pytest
from datetime import datetime, timezone

from issue2md.models.resource import ResourceRef, ResourceType
from issue2md.models.issue import IssueData, Label, Comment
from issue2md.models.discussion import DiscussionData


@pytest.fixture
def sample_resource_ref_issue() -> ResourceRef:
    """示例 Issue 资源引用"""
    return ResourceRef(
        owner="octocat",
        repo="Hello-World",
        type=ResourceType.ISSUE,
        number=1,
    )


@pytest.fixture
def sample_resource_ref_pull() -> ResourceRef:
    """示例 PR 资源引用"""
    return ResourceRef(
        owner="octocat",
        repo="Hello-World",
        type=ResourceType.PULL,
        number=42,
    )


@pytest.fixture
def sample_resource_ref_discussion() -> ResourceRef:
    """示例 Discussion 资源引用"""
    return ResourceRef(
        owner="vercel",
        repo="next.js",
        type=ResourceType.DISCUSSION,
        number=100,
    )


@pytest.fixture
def sample_labels() -> list[Label]:
    """示例标签列表"""
    return [
        Label(name="bug", color="d73a4a"),
        Label(name="enhancement", color="a2eeef"),
    ]


@pytest.fixture
def sample_comments() -> list[Comment]:
    """示例评论列表"""
    return [
        Comment(
            author="octocat",
            body="First comment",
            created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        ),
        Comment(
            author="someone",
            body="Second comment",
            created_at=datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]


@pytest.fixture
def sample_issue_data(
    sample_resource_ref_issue: ResourceRef,
    sample_labels: list[Label],
    sample_comments: list[Comment],
) -> IssueData:
    """示例 IssueData"""
    return IssueData(
        ref=sample_resource_ref_issue,
        title="Test Issue",
        state="open",
        author="octocat",
        body="Issue body content",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 6, 1, 7, 8, 9, tzinfo=timezone.utc),
        labels=sample_labels,
        comments=sample_comments,
    )


@pytest.fixture
def sample_pr_data(
    sample_resource_ref_pull: ResourceRef,
    sample_labels: list[Label],
    sample_comments: list[Comment],
) -> IssueData:
    """示例 PR IssueData"""
    return IssueData(
        ref=sample_resource_ref_pull,
        title="Test PR",
        state="merged",
        author="octocat",
        body="PR body content",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 6, 1, 7, 8, 9, tzinfo=timezone.utc),
        labels=sample_labels,
        comments=sample_comments,
        draft=False,
        merged=True,
        mergeable=True,
    )


@pytest.fixture
def sample_discussion_data(
    sample_resource_ref_discussion: ResourceRef,
    sample_labels: list[Label],
    sample_comments: list[Comment],
) -> DiscussionData:
    """示例 DiscussionData"""
    return DiscussionData(
        ref=sample_resource_ref_discussion,
        title="Test Discussion",
        author="octocat",
        body="Discussion body content",
        created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 6, 1, 7, 8, 9, tzinfo=timezone.utc),
        category="Announcements",
        labels=sample_labels,
        comments=sample_comments,
        answer_chosen=True,
    )