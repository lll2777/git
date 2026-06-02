from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from check_env import parse_env


class EnvParsingTests(unittest.TestCase):
    def test_parse_env_accepts_utf8_bom(self) -> None:
        tmp_root = Path.cwd() / "tmp"
        tmp_root.mkdir(exist_ok=True)
        with TemporaryDirectory(dir=tmp_root) as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("APP_ENV=development\n", encoding="utf-8-sig")

            self.assertEqual(parse_env(env_path)["APP_ENV"], "development")


if __name__ == "__main__":
    unittest.main()
