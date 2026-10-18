# Final release staging

The full candidate2 local suite passed10127cases with14artifact skips.
Staging then found captured whitespace in archived records and one redundant
EOF blank line in a regression module. The archive policy preserves those
records unchanged. The EOF-only fix has identical AST and marshaled compiled
code, and all208 focused cases pass. No runtime bytes, assertions, timing bounds,
case counts or skips changed. The original full gate stays bound to its
original source hash; final committed source requires its own hosted CI.

The final875-input hash map records the single formatting delta. The evidence
policy lives in docs/evidence/.gitattributes and leaves source/test whitespace
checks active. Original archived files match their previous hashes.
