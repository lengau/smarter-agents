#!/usr/bin/env python3
"""
Unit tests for audit_diff.py
"""

import re
import unittest

from audit_diff import audit_diff


class TestAuditDiff(unittest.TestCase):
    def test_clean_diff_passes(self):
        sample_diff = """diff --git a/src/calculator.py b/src/calculator.py
index e69de29..4b825dc 100644
--- a/src/calculator.py
+++ b/src/calculator.py
@@ -0,0 +1,3 @@
+def add(a: int, b: int) -> int:
+    \"\"\"Add two numbers.\"\"\"
+    return a + b
"""
        numstat = {"src/calculator.py": (3, 0)}
        res = audit_diff(sample_diff, numstat)
        self.assertTrue(res["summary"]["passed"])
        self.assertEqual(len(res["errors"]), 0)
        self.assertEqual(len(res["warnings"]), 0)

    def test_detects_stray_debug_print(self):
        sample_diff = """diff --git a/src/calculator.py b/src/calculator.py
index e69de29..4b825dc 100644
--- a/src/calculator.py
+++ b/src/calculator.py
@@ -0,0 +1,3 @@
+def add(a: int, b: int) -> int:
+    print(f"DEBUG: a={a}, b={b}")
+    return a + b
"""
        numstat = {"src/calculator.py": (3, 0)}
        res = audit_diff(sample_diff, numstat)
        self.assertFalse(res["summary"]["passed"])
        self.assertEqual(len(res["errors"]), 1)
        self.assertEqual(res["errors"][0]["type"], "DEBUG_STATEMENT")

    def test_detects_js_console_log(self):
        sample_diff = """diff --git a/src/index.ts b/src/index.ts
index e69de29..4b825dc 100644
--- a/src/index.ts
+++ b/src/index.ts
@@ -0,0 +1,4 @@
+export function calculate(val: number) {
+  console.log("val is", val);
+  return val * 2;
+}
"""
        numstat = {"src/index.ts": (4, 0)}
        res = audit_diff(sample_diff, numstat)
        self.assertFalse(res["summary"]["passed"])
        self.assertEqual(res["errors"][0]["type"], "DEBUG_STATEMENT")

    def test_detects_sensitive_files(self):
        sample_diff = """diff --git a/.env.production b/.env.production
new file mode 100644
index 0000000..4b825dc
--- /dev/null
+++ b/.env.production
@@ -0,0 +1 @@
+API_SECRET=supersecret123
"""
        numstat = {".env.production": (1, 0)}
        res = audit_diff(sample_diff, numstat)
        self.assertFalse(res["summary"]["passed"])
        self.assertEqual(res["errors"][0]["type"], "SENSITIVE_FILE")

    def test_detects_docstring_deletion_warning(self):
        sample_diff = """diff --git a/src/service.py b/src/service.py
index e69de29..4b825dc 100644
--- a/src/service.py
+++ b/src/service.py
@@ -1,8 +1,2 @@
-'''
-Detailed docstring explaining why this service exists.
-It coordinates multiple microservices and handles retries.
-'''
 def handle_request():
-    # Important comment about handling edge cases
-    # Another note
     return True
"""
        numstat = {"src/service.py": (1, 6)}
        res = audit_diff(sample_diff, numstat)
        self.assertTrue(
            res["summary"]["passed"]
        )  # Docstring deletions are warnings by default
        self.assertEqual(len(res["warnings"]), 1)
        self.assertEqual(res["warnings"][0]["type"], "DOCSTRING_DELETION")

    def test_out_of_scope_warning(self):
        sample_diff = """diff --git a/config/database.yml b/config/database.yml
index e69de29..4b825dc 100644
--- a/config/database.yml
+++ b/config/database.yml
@@ -1,1 +1,1 @@
-host: localhost
+host: remote.db
"""
        numstat = {"config/database.yml": (1, 1)}
        allowed = [re.compile(r"^src/")]
        res = audit_diff(sample_diff, numstat, allowed_patterns=allowed)
        self.assertEqual(len(res["warnings"]), 1)
        self.assertEqual(res["warnings"][0]["type"], "OUT_OF_SCOPE")

    def test_excessive_churn_warning(self):
        sample_diff = """diff --git a/src/huge_file.py b/src/huge_file.py
index e69de29..4b825dc 100644
--- a/src/huge_file.py
+++ b/src/huge_file.py
@@ -1 +1 @@
+pass
"""
        numstat = {"src/huge_file.py": (300, 250)}
        res = audit_diff(sample_diff, numstat, max_churn_lines=500)
        self.assertEqual(len(res["warnings"]), 1)
        self.assertEqual(res["warnings"][0]["type"], "EXCESSIVE_CHURN")


if __name__ == "__main__":
    unittest.main()
