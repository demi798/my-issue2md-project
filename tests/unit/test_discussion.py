"""Discussion 模型的单元测试"""

import pytest
from datetime import datetime
from issue2md.models.discussion import DiscussionData
from issue2md.models.resource import ResourceRef, ResourceType


class TestDiscussionData:
    """测试 DiscussionData dataclass"""

    def setup_method(self):
        """测试前的设置"""
        self.ref = ResourceRef("vercel", "next.js", ResourceType.DISCUSSION, 100)
        self.created_at = datetime(2026, 1, 1, 12, 0, 0)
        self.updated_at = datetime(2026, 1, 2, 12, 0, 0)

    def test_basic_creation(self):
        """测试基本字段必填"""
        discussion = DiscussionData(
            ref=self.ref,
            title="How to use Next.js?",
            author="john",
            body="I have a question about Next.js...",
            created_at=self.created_at,
            updated_at=self.updated_at,
            category="help wanted",
        )
        assert discussion.ref == self.ref
        assert discussion.title == "How to use Next.js?"
        assert discussion.author == "john"
        assert discussion.body == "I have a question about Next.js..."
        assert discussion.created_at == self.created_at
        assert discussion.updated_at == self.updated_at
        assert discussion.category == "help wanted"
        assert discussion.labels == []
        assert discussion.comments == []
        assert discussion.answer_chosen is False

    def test_with_labels(self):
        """测试包含标签"""
        from issue2md.models.issue import Label
        label = Label("help", "008672")
        discussion = DiscussionData(
            ref=self.ref,
            title="How to use Next.js?",
            author="john",
            body="I have a question about Next.js...",
            created_at=self.created_at,
            updated_at=self.updated_at,
            category="help wanted",
            labels=[label],
        )
        assert discussion.labels == [label]
        assert discussion.labels[0].name == "help"

    def test_with_comments(self):
        """测试包含评论"""
        from issue2md.models.issue import Comment
        comment = Comment("jane", "You can use the API routes!", self.created_at)
        discussion = DiscussionData(
            ref=self.ref,
            title="How to use Next.js?",
            author="john",
            body="I have a question about Next.js...",
            created_at=self.created_at,
            updated_at=self.updated_at,
            category="help wanted",
            comments=[comment],
        )
        assert discussion.comments == [comment]
        assert discussion.comments[0].author == "jane"

    def test_answer_chosen_true(self):
        """测试 answer_chosen 为 True"""
        discussion = DiscussionData(
            ref=self.ref,
            title="How to use Next.js?",
            author="john",
            body="I have a question about Next.js...",
            created_at=self.created_at,
            updated_at=self.updated_at,
            category="help wanted",
            answer_chosen=True,
        )
        assert discussion.answer_chosen is True

    def test_comments_count_property(self):
        """测试 comments_count 属性"""
        from issue2md.models.issue import Comment
        comment1 = Comment("user1", "Comment 1", self.created_at)
        comment2 = Comment("user2", "Comment 2", self.created_at)
        discussion = DiscussionData(
            ref=self.ref,
            title="How to use Next.js?",
            author="john",
            body="I have a question about Next.js...",
            created_at=self.created_at,
            updated_at=self.updated_at,
            category="help wanted",
            comments=[comment1, comment2],
        )
        assert discussion.comments_count == 2

    def test_type_property(self):
        """测试 type 属性返回 discussion"""
        discussion = DiscussionData(
            ref=self.ref,
            title="How to use Next.js?",
            author="john",
            body="I have a question about Next.js...",
            created_at=self.created_at,
            updated_at=self.updated_at,
            category="help wanted",
        )
        assert discussion.type == "discussion"

    def test_frozen(self):
        """测试不可变性"""
        discussion = DiscussionData(
            ref=self.ref,
            title="How to use Next.js?",
            author="john",
            body="I have a question about Next.js...",
            created_at=self.created_at,
            updated_at=self.updated_at,
            category="help wanted",
        )
        with pytest.raises(AttributeError):
            discussion.title = "New Title"