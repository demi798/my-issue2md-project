"""Resource 模块的单元测试"""

import pytest

from issue2md.models.resource import ResourceRef, ResourceType


class TestResourceType:
    """测试 ResourceType 枚举"""

    def test_values(self) -> None:
        """测试枚举值正确"""
        assert ResourceType.ISSUE.value == "issues"
        assert ResourceType.PULL.value == "pulls"
        assert ResourceType.DISCUSSION.value == "discussions"

    def test_is_str(self) -> None:
        """测试是字符串类型"""
        assert isinstance(ResourceType.ISSUE, str)
        assert isinstance(ResourceType.PULL, str)
        assert isinstance(ResourceType.DISCUSSION, str)


class TestResourceRef:
    """测试 ResourceRef dataclass"""

    def test_frozen(self) -> None:
        """测试不可变性"""
        ref = ResourceRef("owner", "repo", ResourceType.ISSUE, 123)
        with pytest.raises(AttributeError):
            ref.owner = "newowner"  # type: ignore[misc]

    def test_url_property(self) -> None:
        """测试 url 属性返回正确格式"""
        ref = ResourceRef("octocat", "Hello-World", ResourceType.ISSUE, 1)
        expected = "https://github.com/octocat/Hello-World/issues/1"
        assert ref.url == expected

    def test_url_property_with_slash(self) -> None:
        """测试 url 属性正确包含斜杠"""
        ref = ResourceRef("owner", "repo", ResourceType.PULL, 42)
        expected = "https://github.com/owner/repo/pulls/42"
        assert ref.url == expected

    def test_equality(self) -> None:
        """测试两个相同 ResourceRef 相等"""
        ref1 = ResourceRef("owner", "repo", ResourceType.ISSUE, 123)
        ref2 = ResourceRef("owner", "repo", ResourceType.ISSUE, 123)
        assert ref1 == ref2

    def test_inequality(self) -> None:
        """测试不同 ResourceRef 不等"""
        ref1 = ResourceRef("owner1", "repo1", ResourceType.ISSUE, 123)
        ref2 = ResourceRef("owner2", "repo2", ResourceType.ISSUE, 456)
        assert ref1 != ref2
