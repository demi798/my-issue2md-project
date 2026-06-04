"""支持 ``python -m issue2md`` 形式调用。

等价于在 shell 中执行 ``issue2md ...``。
"""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":
    import sys

    sys.exit(main())
