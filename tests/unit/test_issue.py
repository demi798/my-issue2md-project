"""Issue 模型的单元测试"""

import pytest
from datetime import datetime
from issue2md.models.issue import Label, Comment, IssueData
from issue2md.models.resource import ResourceRef, ResourceType


class TestLabel:
    """测试 Label dataclass"""

    def test_basic_creation(self):
        """测试基本字段必填"""
        label = Label("bug", "d73a4a")
        assert label.name == "bug"
        assert label.color == "d73a4a"

    def test_optional_color(self):
        """测试 color 字段可选"""
        label1 = Label("enhancement")
        assert label1.name == "enhancement"
        assert label1.color is None

        label2 = Label("bug", None)
        assert label2.name == "bug"
        assert label2.color is None

    def test_frozen(self):
        """测试不可变性"""
        label = Label("bug", "d73a4a")
        with pytest.raises(AttributeError):
            label.name = "enhancement"


class TestComment:
    """测试 Comment dataclass"""

    def test_basic_creation(self):
        """测试基本字段必填"""
        created_at = datetime(2026, 1, 1, 12, 0, 0)
        comment = Comment("octocat", "Hello world!", created_at)
        assert comment.author == "octocat"
        assert comment.body == "Hello world!"
        assert comment.created_at == created_at

    def test_frozen(self):
        """测试不可变性"""
        created_at = datetime(2026, 1, 1, 12, 0, 0)
        comment = Comment("octocat", "Hello world!", created_at)
        with pytest.raises(AttributeError):
            comment.author = "anotheruser"


class TestIssueData:
    """测试 IssueData dataclass"""

    def setup_method(self):
        """测试前的设置"""
        self.ref = ResourceRef("octocat", "Hello-World", ResourceType.ISSUE, 1)
        self.created_at = datetime(2026, 1, 1, 12, 0, 0)
        self.updated_at = datetime(2026, 1, 2, 12, 0, 0)

    def test_basic_creation(self):
        """测试基本字段必填"""
        issue = IssueData(
            ref=self.ref,
            title="Test Issue",
            state="open",
            author="octocat",
            body="This is a test issue",
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        assert issue.ref == self.ref
        assert issue.title == "Test Issue"
        assert issue.state == "open"
        assert issue.author == "octocat"
        assert issue.body == "This is a test issue"
        assert issue.created_at == self.created_at
        assert issue.updated_at == self.updated_at
        assert issue.labels == []
        assert issue.comments == []
        assert issue.draft is None
        assert issue.merged is None
        assert issue.mergeable is None

    def test_with_labels(self):
        """测试包含标签"""
        label = Label("bug", "d73a4a")
        issue = IssueData(
            ref=self.ref,
            title="Test Issue",
            state="open",
            author="octocat",
            body="This is a test issue",
            created_at=self.created_at,
            updated_at=self.updated_at,
            labels=[label],
        )
        assert issue.labels == [label]
        assert issue.labels[0].name == "bug"

    def test_with_comments(self):
        """测试包含评论"""
        comment = Comment("octocat", "Hello world!", self.created_at)
        issue = IssueData(
            ref=self.ref,
            title="Test Issue",
            state="open",
            author="octocat",
            body="This is a test issue",
            created_at=self.created_at,
            updated_at=self.updated_at,
            comments=[comment],
        )
        assert issue.comments == [comment]
        assert issue.comments[0].author == "octocat"

    def test_pr_fields(self):
        """测试 PR 专用字段"""
        pr_ref = ResourceRef("octocat", "Hello-World", ResourceType.PULL, 1)
        issue = IssueData(
            ref=pr_ref,
            title="Test PR",
            state="merged",
            author="octocat",
            body="This is a test PR",
            created_at=self.created_at,
            updated_at=self.updated_at,
            draft=True,
            merged=True,
            mergeable=True,
        )
        assert issue.draft is True
        assert issue.merged is True
        assert issue.mergeable is True

    def test_comments_count_property(self):
        """测试 comments_count 属性"""
        comment1 = Comment("user1", "Comment 1", self.created_at)
        comment2 = Comment("user2", "Comment 2", self.created_at)
        issue = IssueData(
            ref=self.ref,
            title="Test Issue",
            state="open",
            author="octocat",
            body="This is a test issue",
            created_at=self.created_at,
            updated_at=self.updated_at,
            comments=[comment1, comment2],
        )
        assert issue.comments_count == 2

    def test_type_property_issue(self):
        """测试 type 属性返回 issue"""
        issue = IssueData(
            ref=self.ref,
            title="Test Issue",
            state="open",
            author="octocat",
            body="This is a test issue",
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        assert issue.type == "issue"

    def test_type_property_pull(self):
        """测试 type 属性返回 pull"""
        pr_ref = ResourceRef("octocat", "Hello-World", ResourceType.PULL, 1)
        issue = IssueData(
            ref=pr_ref,
            title="Test PR",
            state="open",
            author="octocat",
            body="This is a test PR",
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        assert issue.type == "pull"

    def test_frozen(self):
        """测试不可变性"""
        issue = IssueData(
            ref=self.ref,
            title="Test Issue",
            state="open",
            author="octocat",
            body="This is a test issue",
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        with pytest.raises(AttributeError):
            issue.title = "New Title"
